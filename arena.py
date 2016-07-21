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

def load_worker_settings ():
    """
    Load the file with the worker setings, namely the CASU they represent and the address where they listen for commands.
    """
    file_object = open ('workers', 'r')
    dictionary = yaml.load (file_object)
    file_object.close ()
    result = []
    number_workers = dictionary ['number_workers']
    for index in xrange (1, number_workers + 1):
        worker_key = 'worker-%03d' % (index)
        casu_number = dictionary [worker_key]['casu_number']
        worker_address = dictionary [worker_key]['address']
        result.append ((casu_number, worker_address))
    print result
    return result

def connect_workers (worker_settings, config):
    """
    Given a list with worker settings, connect to them and return a list with the CASU they represent and the ZMQ socket where they listen for commands.
    """
    result = {}
    context = zmq.Context ()
    for (casu_number, worker_address) in worker_settings:
        print ("Connecting to worker at %s responsible for casu #%d..." % (worker_address, casu_number))
        socket = context.socket (zmq.REQ)
        socket.connect (worker_address)
        result [casu_number] = socket
        print ("Initializing worker responsible for casu #%d..." % (casu_number))
        answer = zmq_sock_utils.send_recv (socket, [worker.INITIALIZE, config.evaluation_run_time, config.spreading_waiting_time, config.frame_per_second])
        print ("Worker responded with: %s" % (str (answer)))
    print result
    return result

def get_zmq (name, worker_zmqs):
    """
    Ask the user the CASU number of a CASU with the given name relative to the background image.
    Returns the zmq socket.
    """
    while True:
        try:
            index = int (raw_input ("Number of %s CASU? " % name))
            if index in worker_zmqs:
                return worker_zmqs [index]
            else:
                print ("There is no worker associated with CASU number %d." % (index))
        except ValueError:
            print ("Invalid number")

class AbstractArena:
    """
    This class represents an abstract arena.  The attributes of this class represent the ZMQ sockets where the worker programs are listening for commands.
    """
    def __init__ (self, worker_zmqs, casu_names, img_path):
        """
        Ask the user the CASUs that are this arena, and the position of the arena in the background image.
        """
        self.workers = []
        for name in casu_names:
            self.workers.append (get_zmq (name, worker_zmqs))
        ok = False
        while not ok:
            try:
                self.arena_left = int (raw_input ("Leftmost (min) pixel of the arena? "))
                self.arena_right = int (raw_input ("Rightmost (max) pixel of the arena? "))
                self.arena_top = int (raw_input ("Topmost (min) pixel of the arena? "))
                self.arena_bottom = int (raw_input ("Bottommost (max) pixel of the arena? "))
                if self.arena_left > self.arena_right or self.arena_top > self.arena_bottom:
                    print ("Invalid pixel data!")
                else:
                    ok = True
            except ValueError:
                print ("Not a number!")
        self.img_path = img_path

    def status (self):
        """
        Return the suitability of this arena to run a vibration pattern.  The CASU temperature must be below a minimum threshold.  The suitability is a function of the CASU ring temperature sensor.
        """
        value = 0
        temps = []
        good = True
        for socket in self.workers:
            temperature = zmq_sock_utils.send_recv (socket, [worker.CASU_STATUS])
            temps.append (temperature)
            if temperature > worker.CASU_TEMPERATURE + 1 or temperature < worker.CASU_TEMPERATURE - 1:
                good = False
            else:
                value += worker.CASU_TEMPERATURE + 1 - temperature
        if not good:
            value = 0
        return (value, temps)
            

    def run_vibration_pattern (self, config, chromosome):
        """
        Pick a random worker and send the chromosome with the vibration pattern.  This worker will be the active CASU, while the others are the passive CASU.  Sleeps for the duration of the chromosome evaluation.
        """
        self.selected_worker_index = random.randrange (len (self.workers))
        for i in xrange (len (self.workers)):
            socket = self.workers [i]
            if i == self.selected_worker_index:
                zmq_sock_utils.send (socket, [worker.ACTIVE_CASU, chromosome])
            else:
                zmq_sock_utils.send (socket, [worker.PASSIVE_CASU])
        time.sleep (4.0 / config.frame_per_second + config.evaluation_run_time + config.spreading_waiting_time)

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
    def __init__ (self, worker_zmqs, img_path):
        """
        Ask the user the position of the arena border in the background image.
        """
        AbstractArena.__init__ (self, worker_zmqs, ["top", "bottom"], img_path)
        ok = False
        while not ok:
            try:
                self.arena_border_coordinate = int (raw_input ("Vertical coordinate of the border? "))
                if self.arena_top < self.arena_border_coordinate < self.arena_bottom:
                    ok = True
                else:
                    print ("Invalid border position!")
            except ValueError:
                print ("Not a number!")
                    
    def create_region_of_interests_image (self, episode_path):
        """
        Process the background image and create an image with region of interest highlighted.
        """
        run_convert ([
            episode_path + 'Background.jpg',
            '-crop', str (self.arena_right - self.arena_left) + 'x' + str (self.arena_bottom - self.arena_top) + '+' + str (self.arena_left) + '+' + str (self.arena_top),
            '-fill', 'rgb(255,255,0)',
            '-tint', '100',
            'Measured-Area-tmp-2.jpg'])
        run_convert ([
            episode_path + 'Background.jpg',
            '-draw', 'image SrcOver %d,%d %d,%d Measured-Area-tmp-2.jpg' % (self.arena_left, self.arena_top,  self.arena_right - self.arena_left, self.arena_bottom - self.arena_top),
            'Measured-Area-tmp-3.jpg'])
        x0, y0 = self.arena_left,  self.arena_border_coordinate,
        x1, y1 = self.arena_right, self.arena_border_coordinate
        run_convert ([
            'Measured-Area-tmp-3.jpg',
            '-fill', 'rgb(0,0,255)',
            '-draw', 'line %d,%d %d,%d' % (x0, y0, x1, y1),
            self.img_path + 'Region-of-Interests.jpg'])
        subprocess.call ([
            'rm',
            'Measured-Area-tmp-2.jpg',
            'Measured-Area-tmp-3.jpg'])

    def create_mask_images_casu_images (self, config, episode_path):
        """
        Use the background to create the image masks and the casu images that are going to be used by the image processing functions.
        """
        run_convert ([
            episode_path + 'Background.jpg',
            '-fill', 'rgb(0,0,0)',
            '-draw', 'rectangle 0,0 %d,%d' % (config.image_width, config.image_height),
            '-fill', 'rgb(255,255,255)',
            '-draw', 'rectangle %d,%d %d,%d' % (self.arena_left, self.arena_top, self.arena_right, self.arena_border_coordinate),
            self.img_path + 'Mask-0.jpg'])
        run_convert ([
            episode_path + 'Background.jpg',
            '-fill', 'rgb(0,0,0)',
            '-draw', 'rectangle 0,0 %d,%d' % (config.image_width, config.image_height),
            '-fill', 'rgb(255,255,255)',
            '-draw', 'rectangle %d,%d %d,%d' % (self.arena_left, self.arena_border_coordinate, self.arena_right, self.arena_bottom),
            self.img_path + 'Mask-1.jpg'])
        run_convert ([
            episode_path + 'Background.jpg',
            self.img_path + 'Mask-0.jpg',
            '-compose', 'multiply',
            '-composite',
            self.img_path + 'Arena-Top-CASU.jpg'])
        run_convert ([
            episode_path + 'Background.jpg',
            self.img_path + 'Mask-1.jpg',
            '-compose', 'multiply',
            '-composite',
            self.img_path + 'Arena-Bot-CASU.jpg'])

    def write_properties (self):
        """
        Save the arena properties for later reference.
        """
        fp = open (self.img_path + "properties", 'w')
        AbstractArena.x__write_properties (self, fp)
        fp.write ("""arena_border_coordinate: %d
""" % (self.arena_border_coordinate))
        fp.close ()

    def compare_images (i):
        """
        Compare the background image with the ith image from an iteration video.
        """
        return [-1, -1, -1, -1]

def run_convert (args):
    """Run the convert program with the given arguments.

    The convert program is a member of the ImageMagick(1) suite of tools.
    It can be used to convert between image formats as well as resize an
    image, blur, crop, despeckle, dither, draw on, flip, join, re-sample,
    and much more.

    :param list args: a list of the arguments to pass to the convert program.

    """
#    subprocess.check_call (['/usr/local/bin/convert'] + args)
    subprocess.check_call (['/usr/bin/convert'] + args)
