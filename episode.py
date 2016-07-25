#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arena

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

    def __init__ (self, config, worker_zmqs):
        self.config = config
        self.worker_zmqs = worker_zmqs
        self.current_evaluation_in_episode = 0
        self.episode_index = 1

    def initialise (self):
        """
        In the initialisation phase of an episode we:

        * create the background image;

        * ask the user for the characteristics of the arena(s) image and the CASUs;

        * ask the user to put bees in the arena(s);
        """
        self.current_path = "%sepisodes/%03d/" % (self.config.experiment_folder, self.episode_index)
        try:
            os.makedirs (self.current_path)
        except OSError:
            pass
        self.make_background_image ()
        self.ask_arenas ()
        raw_input ('\nPlace %d bees in the arena(s) and press ENTER. ' % self.config.number_bees)

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
                      '! video/x-raw-yuv,width=' + str (self.config.image_width) + ',height=' + str (self.config.image_height) + ',framerate=1/' + str (int (1.0 / self.config.frame_per_second)) + \
                      ' ! jpegenc ! avimux name=mux ! filesink location=' + filename    # with time - everytime generate a new file
        p = subprocess.Popen (bashCommand, shell = True, executable = '/bin/bash') #run the recording stream
        p.wait ()
        bashCommandSplit = "ffmpeg" + \
            " -i " + filename + \
            " -r 0.1" + \
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
        while go:
            img_path = "%sarena-%d/" % (self.current_path, index)
            if self.config.arena_type == 'StadiumBorderArena':
                new_arena = arena.StadiumBorderArena (self.worker_zmqs, self.current_path, img_path, index)
            else:
                print ("Unknown arena type: %s" % (str (self.config.arena_type)))
            self.arenas.append (new_arena)
            os.makedirs (img_path)
            new_arena.create_region_of_interests_image ()
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
        
    def finish (self):
        """
        In the finish phase of an episode we:

        * tell the user to remove the bees from the arena;

        """
        raw_input ("Remove the bees from the arena(s) and press ENTER to continue. ")
