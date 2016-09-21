#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arena
import worker
import zmq_sock_utils

import subprocess
import os
import os.path
import random

class Episode:
    """
    An episode represents a set of evaluations with a set of bees.

    This class is responsible for managing the initialisation and finish phase of episodes.  This class also manages the evaluation counter used in an episode.  The increment of this counter should be done at the beginning of an evaluation phase (see method evaluator.exp_step).

    In the initialisation phase the characteristics of the arena image have to be computed before bees are placed in the arena.  Then we ask the user to place the bees in the arena.  For documentation about the arena images, see module 'image'.

    In the finish phase we ask the user to remove the bees from the arena.

    This class can be used by the incremental evolution or by a parameter sweep.
    """

    def __init__ (self, config, worker_settings, experiment_folder, episode_index = 1):
        self.config = config
        self.worker_settings = worker_settings
        self.experiment_folder = experiment_folder
        self.current_evaluation_in_episode = 0
        self.episode_index = episode_index

    def initialise (self):
        """
        In the initialisation phase of an episode we:

        * create the background image;

        * ask the user for the characteristics of the arena(s) image and the CASUs;

        * ask the user to put bees in the arena(s);
        """
        self.current_path = "%sepisodes/%03d/" % (self.experiment_folder, self.episode_index)
        try:
            os.makedirs (self.current_path)
        except OSError:
            pass
        self.make_background_image ()
        self.ask_arenas ()
        raw_input ('\nPlace %d bees in the arena(s) and press ENTER. ' % self.config.number_bees)

    def ask_user (self, chromosome):
        """
        Ask the user to evaluate the chromosome.  If bees are stopped because they are sleeping, the user may opt to spread them.
        """
        interact = self.current_evaluation_in_episode < self.config.number_evaluations_per_episode
        while interact:
            print "Press ENTER to evaluate chromosome " + str (chromosome)
            print "Enter an integer x to spread bees for x seconds"
            print "Enter 'replace bees' to end the current episode and start a new one with new bees"
            ans = raw_input ("? ")
            try:
                seconds = int (ans)
                print "Spreading bees for %d seconds..." % (seconds)
                #self.episode.spread_bees (seconds)
                for arena in self.arenas:
                    for (_, socket) in arena.workers:
                        zmq_sock_utils.send (socket, [worker.SPREAD_BEES, seconds])
                for arena in self.arenas:
                    for (number, socket) in arena.workers:
                        answer = zmq_sock_utils.recv (socket)
                        print ("Worker responsible for casu #%d responded with: %s" % (number, str (answer)))
            except ValueError:
                if ans == 'replace bees':
                    self.finish ()
                    self.episode_index += 1
                    self.initialise ()
                    self.current_evaluation_in_episode = 0
                    interact = False
                else:
                    interact = ans != ''
                    if interact:
                        print "Invalid option:", ans

    def increment_evaluation_counter (self):
        """
        Increment the evaluation counter.  If we have reached the end of an episode, we finish it and start a new episode.
        """
        if (self.current_evaluation_in_episode == self.config.number_evaluations_per_episode):
            print "\n\n* ** New Episode ** *"
            self.finish ()
            self.episode_index += 1
            self.initialise ()
            self.current_evaluation_in_episode = 1
        else:
            self.current_evaluation_in_episode += 1

    def make_background_image (self):
        """
        Create the background video and image.

        These are used by the bee
        aggregation functions to compute how bees are stopped.  The
        background video and images are created at start of an experiment
        and everytime we change bees.  Whenever we change bees, we may
        disturb the arena.  The bee aggregation is sensitive to changes between the background image and evaluation images.
        """
        print "\n\n* ** Creating background image..."
        filename = self.current_path + 'Background.avi'
        bashCommand = 'gst-launch-0.10 --gst-plugin-path=/usr/local/lib/gstreamer-0.10/ --gst-plugin-load=libgstaravis-0.4.so -v aravissrc num-buffers=1 ' + \
                      '! video/x-raw-yuv,width=' + str (self.config.image_width) + ',height=' + str (self.config.image_height) + ',framerate=1/' + str (int (self.config.frame_per_second)) + '/1' + \
                      ' ! jpegenc ! avimux name=mux ! filesink location=' + filename    # with time - everytime generate a new file
        p = subprocess.Popen (bashCommand, shell = True, executable = '/bin/bash') #run the recording stream
        p.wait ()
        bashCommandSplit = "avconv" + \
            " -i " + filename + \
            " -r 0.1" + \
            " -loglevel error" + \
            " -f image2 " + self.current_path + "Background.jpg" #definition to extract the single image for background from the video
        bashCommandSplit = "ffmpeg" + \
            " -i " + filename + \
            " -r 0.1" + \
            " -loglevel error" + \
            " -f image2 " + self.current_path + "Background.jpg" #definition to extract the single image for background from the video
        p = subprocess.Popen (bashCommandSplit, shell = True, executable = '/bin/bash') #run the script of the extracting
        p.wait ()
        print ("background image is ready")

    def ask_arenas (self):
        """
        Ask the user how many arenas are going to be used and their characteristics.
        """
        p = subprocess.Popen ([
            '/usr/bin/gimp',
            self.current_path + "Background.jpg"])
        go = True
        self.arenas = []
        index = 1
        for ws in self.worker_settings.values ():
            ws.in_use = False
        while go:
            img_path = "%sarena-%d/" % (self.current_path, index)
            os.makedirs (img_path)
            roi_ko = True
            while roi_ko:
                if self.config.arena_type == 'StadiumBorderArena':
                    new_arena = arena.StadiumBorderArena (self.worker_settings, self.current_path, img_path, index, self.config)
                elif self.config.arena_type == 'CircularArena':
                    new_arena = arena.CircularArena (self.worker_settings, self.current_path, img_path, index, self.config)
                else:
                    print ("Unknown arena type: %s" % (str (self.config.arena_type)))
                new_arena.create_region_of_interests_image ()
                command = "display " + img_path + "Region-of-Interests.jpg"
                display_process = subprocess.Popen (command, shell = True)
                roi_ko = raw_input ("Are the region of interests ok? ").upper () [0] == 'N'
                display_process.kill ()
            self.arenas.append (new_arena)
            new_arena.create_mask_images_casu_images (self.config)
            new_arena.write_properties ()
            index += 1
            go = raw_input ('Are there more arena(s) (y/n)? ').upper () [0] == 'Y'
        print ("Close GIMP")
        p.wait ()

    def select_arena (self):
        """
        Check the status of the arenas and select an arena using a roulette wheel approach.
        Returns the selected arena.
        """
        ok = False
        while not ok:
            status = []
            total_sum = 0
            for an_arena in self.arenas:
                (value, temps) = an_arena.status ()
                total_sum += value
                status.append (value)
                print ("Temperature status: %s." % (str (temps)))
            if total_sum == 0:
                print ("All arenas have a temperature above the minimum threshold!")
                raw_input ("Press ENTER to try again. ")
            else:
                ok = True
        x = total_sum * random.random ()
        picked = 0
        print x, "/", total_sum, status
        while x >= status [picked]:
            x -= status [picked]
            picked += 1
        print ("Picked arena #%d." % (picked + 1))
        return self.arenas [picked]
        
    def finish (self, end_evolutionary_algorithm = False):
        """
        In the finish phase of an episode we:

        * tell the user to remove the bees from the arena;

        """
        print ("Remove the bees from the arena(s)!")
        if not end_evolutionary_algorithm:
            print ("Change the wax!")
            print ("Rearrange the arena(s)!")
        raw_input ("When done, press ENTER to continue. ")

if __name__ == '__main__':
    import worker_settings
    lws = worker_settings.load_worker_settings ('workers')
    for ws in lws:
        print ws
    import new_config
    cfg = new_config.Config ()
    dws = dict ([(ws.casu_number, ws) for ws in lws])
    epsd = Episode (cfg, dws, '/tmp/assisi/')
    epsd.initialise ()
    epsd.ask_user (None)
    epsd.increment_evaluation_counter ()
    picked_arena = epsd.select_arena ()
