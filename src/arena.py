#!/usr/bin/env python
# -*- coding: utf-8 -*-

import worker
import zmq_sock_utils

import assisipy

import zmq
import yaml
import subprocess
import random
import time
import Image

MAXIMUM_TEMPERATURE_DIFFERENCE = 1

def find_app (app):
    command = "which " + app
    process = subprocess.Popen (command, stdout = subprocess.PIPE, shell = True)
    out, _ = process.communicate ()
    return out [:-1]

CONVERT_BIN_FILENAME = find_app ("convert")
"""
Filename of the convert program.

The convert program is a member of the ImageMagick(1) suite of tools.
It can be used to convert between image formats as well as resize an
image, blur, crop, despeckle, dither, draw on, flip, join, re-sample,
and much more.
"""

COMPARE_BIN_FILENAME = find_app ("compare")

def ask_casu_number (name, worker_settings):
    """
    Ask the user the CASU number of a CASU with the given name relative to the background image.
    Returns a tuple with the casu number and the zmq socket.
    """
    while True:
        try:
            number = int (raw_input ("Number of %s CASU? " % name))
            if number in worker_settings:
                if worker_settings [number].in_use:
                    print ("This CASU is already chosen!")
                else:
                    # FIX this if 
                    worker_settings [number].in_use = True
                    return (number, worker_settings [number].socket, worker_settings [number])
            else:
                print ("There is no worker associated with CASU number %d." % (number))
        except ValueError:
            print ("Invalid number")

class AbstractArena:
    """
    This class represents an abstract arena.  The attributes of this class represent the ZMQ sockets
    where the worker programs are listening for commands.
    """
    def __init__ (self, worker_settings, casu_names, episode_path, img_path, index, config):
        """
        Ask the user the CASUs that are this arena, and the position of the arena in the background image.
        """
        self.workers = [ask_casu_number (name, worker_settings) for name in casu_names]
        self.episode_path = episode_path
        self.img_path = img_path
        self.index = index
        self.same_colour_threshold = '%d%%' % (config.same_colour_threshold)
        self.delta_image = int (config.frame_per_second / config.interval_current_previous_frame)

    def unselect_workers (self):
        """If the user does not like the arena, the workers that have been
        assigned are free to be selected again.
        """
        for ws in self.workers:
            ws [2].in_use = False

    def status (self):
        """
        Return the suitability of this arena to run a vibration pattern.  The CASU temperature must be below a minimum threshold.  The suitability is a function of the CASU ring temperature sensor.
        """
        value = 0
        temps = []
        good = True
        for (_, socket, _) in self.workers:
            temperature = zmq_sock_utils.send_recv (socket, [worker.CASU_STATUS])
            temps.append (temperature)
            if temperature > worker.CASU_TEMPERATURE + 1 or temperature < worker.CASU_TEMPERATURE - 1:
                good = False
            else:
                value += worker.CASU_TEMPERATURE + 1 - temperature
        if good:
            for i1 in xrange (len (self.workers) - 1):
                for i2 in xrange (1, len (self.workers)):
                    if abs (temps [i1] - temps [i2]) > MAXIMUM_TEMPERATURE_DIFFERENCE:
                        good = False
        if not good:
            value = 0
        return (value, temps)
            

    def run_vibration_model (self, config, chromosome):
        """
        Pick a random worker and send the chromosome with the vibration pattern.
        This worker will be the active CASU, while the others are the passive CASU.
        Waits for the response from all workers.  Workers respond when they finish their role.
        """
        #self.selected_worker_index = random.randrange (len (self.workers))
        self.selected_worker_index = 0
        for i in xrange (len (self.workers)):
            (_, socket, _) = self.workers [i]
            if i == self.selected_worker_index:
                zmq_sock_utils.send (socket, [worker.ACTIVE_CASU, chromosome])
            else:
                zmq_sock_utils.send (socket, [worker.PASSIVE_CASU])
        if config.sound_hardware == 'Graz':
            time.sleep (2.0 / config.frame_per_second)
            config.run_vibration_model (chromosome, self.selected_worker_index, config.evaluation_run_time)
        time_start_vibration_pattern = None
        for (number, socket, _) in self.workers:
            answer = zmq_sock_utils.recv (socket)
            if len (answer) == 2:
                time_start_vibration_pattern = answer [1]
            print ("Worker responsible for casu #%d responded with: %s" % (number, str (answer)))
        return time_start_vibration_pattern

    def __compare_image_thomas (self, mask, image1, image2):
        """
        Compare two images using the convert program developed by Thomas Schmickl.  This program computes the pixel count difference between two images in a region of interest.
        """
        command = [
            CONVERT_BIN_FILENAME,
            image1,
            image2,
            '-compose', 'Subtract',
            '-composite',
            '-threshold', '40000',
            mask,
            '-compose', 'ModulusSubtract',
            '-composite',
            '-print', '%[fx:w*h*mean]',
            'null:'
            ]
        #import functools
        #print "Running", functools.reduce (lambda x, y: x + " " + y, command)
        process = subprocess.Popen (command, stdout=subprocess.PIPE)
        out, _ = process.communicate ()
        #print mask, image1, image2, out
        return float (out)
        
    def __compare_image_plsm (self, mask, image1, image2):
        """
        Compare two images using the convert program from the ImageMagick suite.  This program computes the pixel count difference between two images in a region of interest.
        """
        command = [
            CONVERT_BIN_FILENAME,
            '(', mask, image1, '-compose', 'multiply', '-composite', ')',
            '(', mask, image2, '-compose', 'multiply', '-composite', ')',
            '-metric', 'AE', '-fuzz', self.same_colour_threshold, '-compare',
            '-format', '%[distortion]', 'info:'
            ]
        process = subprocess.Popen (command, stdout=subprocess.PIPE)
        out, err = process.communicate ()
        try:
            value = int (out)
        except:
            print ("Result is [" + out + "]")
            raise
        return int (out)
        
    def compare_images (self, ith_image):
        """
        Compare the background image with the ith image from an iteration video.
        """
        result = []
        for index in xrange (len (self.workers)):
            mask = "%sMask-%d.jpg" % (self.img_path, index)
            image1 = self.episode_path + 'Background.jpg'
            image2 = "tmp/iteration-image-%04d.jpg" % (ith_image)
            result.append (self.__compare_image_plsm (mask, image1, image2))
            if ith_image > self.delta_image:
                mask = "%sMask-%d.jpg" % (self.img_path, index)
                image1 = "tmp/iteration-image-%04d.jpg" % ith_image
                image2 = "tmp/iteration-image-%04d.jpg" % (ith_image - self.delta_image)
                result.append (self.__compare_image_plsm (mask, image1, image2))
            else:
                result.append (-1)
        return result
        
    def x__write_properties (self, fp):
        fp.write ("""arena_left : %d
arena_right : %d
arena_top :  %d
arena_bottom : %d
""" % (self.arena_left,
       self.arena_right,
       self.arena_top,
       self.arena_bottom))
        
class StadiumBorderArena (AbstractArena):
    """
    An arena with two CASUs (top and bottom), stadium shape, and rectangular region of interest.
    """
    def __init__ (self, worker_settings, episode_path, img_path, index, config):
        """
        Ask the user the position of the arena border in the background image.
        """
        AbstractArena.__init__ (self, worker_settings, ["top", "bottom"], episode_path, img_path, index, config)
        ok = False
        while not ok:
            try:
                self.arena_left = int (raw_input ("Leftmost (min) pixel of the arena? "))
                self.arena_right = int (raw_input ("Rightmost (max) pixel of the arena? "))
                if self.arena_left > self.arena_right:
                    print ("Invalid pixel data!")
                    continue
                self.arena_top = int (raw_input ("Topmost (min) pixel of the arena? "))
                self.arena_bottom = int (raw_input ("Bottommost (max) pixel of the arena? "))
                if self.arena_top > self.arena_bottom:
                    print ("Invalid pixel data!")
                    continue
                self.arena_border_coordinate = int (raw_input ("Vertical coordinate of the border? "))
                if not (self.arena_top < self.arena_border_coordinate < self.arena_bottom):
                    print ("Invalid border position!")
                    continue
                ok = True
            except ValueError:
                print ("Not a number!")
                    
    def create_region_of_interests_image (self):
        """
        Process the background image and create an image with region of interest highlighted.
        """
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-crop', str (self.arena_right - self.arena_left) + 'x' + str (self.arena_bottom - self.arena_top) + '+' + str (self.arena_left) + '+' + str (self.arena_top),
            '-fill', 'rgb(255,255,0)',
            '-tint', '100',
            'Measured-Area-tmp-2.jpg'])
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-draw', 'image SrcOver %d,%d %d,%d Measured-Area-tmp-2.jpg' % (self.arena_left, self.arena_top,  self.arena_right - self.arena_left, self.arena_bottom - self.arena_top),
            'Measured-Area-tmp-3.jpg'])
        x0, y0 = self.arena_left,  self.arena_border_coordinate,
        x1, y1 = self.arena_right, self.arena_border_coordinate
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            'Measured-Area-tmp-3.jpg',
            '-fill', 'rgb(0,0,255)',
            '-draw', 'line %d,%d %d,%d' % (x0, y0, x1, y1),
            self.img_path + 'Region-of-Interests.jpg'])
        subprocess.call ([
            'rm',
            'Measured-Area-tmp-2.jpg',
            'Measured-Area-tmp-3.jpg'])

    def create_mask_images_casu_images (self, config):
        """
        Use the background to create the image masks and the casu images that are going to be used by the image processing functions.
        """
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-fill', 'rgb(0,0,0)',
            '-draw', 'rectangle 0,0 %d,%d' % (config.image_width, config.image_height),
            '-fill', 'rgb(255,255,255)',
            '-draw', 'rectangle %d,%d %d,%d' % (self.arena_left, self.arena_top, self.arena_right, self.arena_border_coordinate),
            self.img_path + 'Mask-0.jpg'])
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-fill', 'rgb(0,0,0)',
            '-draw', 'rectangle 0,0 %d,%d' % (config.image_width, config.image_height),
            '-fill', 'rgb(255,255,255)',
            '-draw', 'rectangle %d,%d %d,%d' % (self.arena_left, self.arena_border_coordinate, self.arena_right, self.arena_bottom),
            self.img_path + 'Mask-1.jpg'])
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            self.img_path + 'Mask-0.jpg',
            '-compose', 'multiply',
            '-composite',
            self.img_path + 'Arena-Top-CASU.jpg'])
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            self.img_path + 'Mask-1.jpg',
            '-compose', 'multiply',
            '-composite',
            self.img_path + 'Arena-Bot-CASU.jpg'])

    def image_processing_header (self):
        return ["background_top", "previous_iteration_top", "background_bottom", "previous_iteration_bottom"]

    def write_properties (self):
        """
        Save the arena properties for later reference.
        """
        fp = open (self.img_path + "properties", 'w')
        AbstractArena.x__write_properties (self, fp)
        fp.write ("""arena_border_coordinate: %d
""" % (self.arena_border_coordinate))
        fp.close ()


class CircularArena (AbstractArena):
    """
    A circular arena with a single casu.  Region of interest is circular
    """
    def __init__ (self, worker_settings, episode_path, img_path, index, config):
        """
        Ask the user the position of the arena, of the casu, and of the region of interest.
        """
        AbstractArena.__init__ (self, worker_settings, ["center"], episode_path, img_path, index, config)
        ok = False
        while not ok:
            try:
                self.arena_center_x = int (raw_input ("Horizontal coordinate of the arena center? "))
                self.arena_center_y = int (raw_input ("Vertical coordinate of the arena center? "))
                self.arena_radius = int (raw_input ("Radius of the arena? "))
                if 0 <= self.arena_center_x - self.arena_radius < self.arena_center_x + self.arena_radius < config.image_width \
                    and 0 <= self.arena_center_y - self.arena_radius < self.arena_center_y + self.arena_radius < config.image_height:
                    ok = True
                else:
                    print ("Invalid arena position!")
            except ValueError:
                print ("Not a number!")

    def create_region_of_interests_image (self):
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-fill', '#FFFF007F',
            '-draw', 'circle %d,%d %d,%d' % (self.arena_center_x, self.arena_center_y, self.arena_center_x, self.arena_center_y + self.arena_radius), 
            self.img_path + 'Region-of-Interests.jpg'])

    def create_mask_images_casu_images (self, config):
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            '-size', '%dx%d' % (config.image_width, config.image_height),
            'xc:black',
            '-fill', '#FFFFFF',
            '-draw', 'circle %d,%d %d,%d' % (self.arena_center_x, self.arena_center_y, self.arena_center_x, self.arena_center_y + self.arena_radius), 
            self.img_path + 'Mask-0.jpg'])
            
    def image_processing_header (self):
        return ["background", "previous_iteration"]

    def write_properties (self):
        """
        Save the arena properties for later reference.
        """
        fp = open (self.img_path + "properties", 'w')
        fp.write ("""arena_center_x : %d
arena_center_y : %d
arena_radius : %d
""" % (self.arena_center_x,
       self.arena_center_y,
       self.arena_radius))
        fp.close ()


class TwoBoxesArena (AbstractArena):
    """
    An arena that contains two rectangular boxes that may not be adjacent.  Each box has a single CASUs.  Regions of interest are the boxes around the CASUs.
    """
    LABELS = ["first", "second"]
    def __init__ (self, worker_settings, episode_path, img_path, index, config):
        """
        Ask the user the position of the arena, of the casu, and of the region of interest.
        """
        AbstractArena.__init__ (self, worker_settings, ["first", "second"], episode_path, img_path, index, config)
        self.roi_top = [-1, -1]
        self.roi_left = [-1, -1]
        self.roi_right = [-1, -1]
        self.roi_bottom = [-1, -1]
        for index in xrange (2):
            ok = False
            while not ok:
                try:
                    self.roi_left [index] = int (raw_input ("Leftmost (min) pixel of the %s box? " % (TwoBoxesArena.LABELS [index])))
                    self.roi_right [index] = int (raw_input ("Rightmost (max) pixel of the %s box? " % (TwoBoxesArena.LABELS [index])))
                    if self.roi_left [index] > self.roi_right [index]:
                        print ("Invalid pixel data!")
                        continue
                    self.roi_top [index] = int (raw_input ("Topmost (min) pixel of the %s box? " % (TwoBoxesArena.LABELS [index])))
                    self.roi_bottom [index] = int (raw_input ("Bottommost (max) pixel of the %s box? " % (TwoBoxesArena.LABELS [index])))
                    if self.roi_top [index] > self.roi_bottom [index]:
                        print ("Invalid pixel data!")
                        continue
                    ok = True
                except ValueError:
                    print ("Not a number!")

    def create_region_of_interests_image (self):
        subprocess.check_call ([
            CONVERT_BIN_FILENAME,
            self.episode_path + 'Background.jpg',
            '-fill', '#FFFF007F',
            '-draw', 'rectangle %d,%d %d,%d' % (self.roi_left [0], self.roi_top [0], self.roi_right [0], self.roi_bottom [0]),
            '-draw', 'rectangle %d,%d %d,%d' % (self.roi_left [1], self.roi_top [1], self.roi_right [1], self.roi_bottom [1]),
            self.img_path + 'Region-of-Interests.jpg'])

    def create_mask_images_casu_images (self, config):
        for index in xrange (2):
            subprocess.check_call ([
                CONVERT_BIN_FILENAME,
                '-size', '%dx%d' % (config.image_width, config.image_height),
                'xc:black',
                '-fill', '#FFFFFF',
                '-draw', 'rectangle %d,%d %d,%d' % (self.roi_left [index], self.roi_top [index], self.roi_right [index], self.roi_bottom [index]),
                self.img_path + 'Mask-%d.jpg' % (index)])

    def image_processing_header (self):
        return ["background_first", "previous_iteration_first", "background_second", "previous_iteration_second"]

    def write_properties (self):
        """
        Save the arena properties for later reference.
        """
        fp = open (self.img_path + "properties", 'w')
        for index, label in zip (xrange (2), TwoBoxesArena.LABELS):
            fp.write ("""roi_left_%s : %d
roi_right_%s : %d
roi_top_%s : %d
roi_bottom_%s : %d
""" % (label, self.roi_left [index],
       label, self.roi_right [index],
       label, self.roi_top [index],
       label, self.roi_bottom [index]))
        fp.close ()


if __name__ == '__main__':
    import worker_settings
    lws = worker_settings.load_worker_settings ('workers')
    for ws in lws:
        print ws
    import config
    cfg = config.Config ()
    dws = dict ([(ws.casu_number, ws) for ws in lws])
    ca = CircularArena (dws, "/tmp/assisi/", "/tmp/assisi/", 1, cfg)
    ca.create_region_of_interests_image ()
    ca.create_mask_images_casu_images (cfg)
    for ws in lws:
        ws.in_use = False
    raw_input ("Check the images and press ENTER")
    sba = StadiumBorderArena (dws, "/tmp/assisi/", "/tmp/assisi/", 1, cfg)
    sba.create_region_of_interests_image ()
    sba.create_mask_images_casu_images (cfg)
    
# devemos ter uma arena onde consideramos uma ROI centrada em torno do CASU como estava na implementação inicial? 
# devemos analisar os videos ovtidos no meu último dia em Graz para determinar a que distância param as abelhas?
# a distância a que param as abelhas deve ser um parâmetro da configuração? Quando estou a perguntar as propriedades das arenas, pergunto também a escala da arena? A escala da imagem é uma constante global, que é perguntada no início da experiência.
# devemos guardar imagens da thermal camera

# devemos fazer experiências com uma arena circular para ver se os CASUs actuais com o método set_vibration_pattern conseguem fazer parar as abelhas
