#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import functools

import chromosome
import best_config
from best_config import Parameter

class Config (best_config.Config):
    """
    Configuration setup of an incremental evolutionary algorithm setup.

    Parameters in the configuration file:

    number_bees:  number of bees in each arena.

    number_generations:  number of generations of the evolutionary algorithm

    number_evaluations_per_episode: maximum number of times a bee group is used to evaluate a chromosome

    evaluation_run_time: duration (in sec) of a single evaluation of a chromosome
    
    spreading_waiting_time: time (in sec) for the bees to spread after vibration

    """

    BEE_WORKDAY_LENGTH = 30 * 60
    """
    Length of bees workday length in seconds.  After this time has elapsed, bees have to go home to rest and get fed.
    """

    def __init__ (self):
        best_config.Config.__init__ (self, [
            Parameter ('number_bees',                    'Number of bees', parse_data = int),
            Parameter ('number_generations',             'Number of generations of the evolutionary algorithm', parse_data = int),
            Parameter ('number_evaluations_per_episode', 'How many evaluations to perform with a set of bees', parse_data = int),
            Parameter ('evaluation_run_time',    'Time in seconds of the total vibration pattern', parse_data = int),
            Parameter ('spreading_waiting_time',  'Time in seconds to spread the bees', parse_data = int),
            Parameter ('population_size', 'Population size of the evolutionary algorithm', parse_data = int),
            Parameter ('number_evaluations_per_chromosome',  'How many evaluations to perform with a chromosome', parse_data = int),
            Parameter (
                'fitness_function',
                '''1 - background bee pixels in active CASU ROI if there is no movement in active CASU ROI
2 - background bee pixels in active CASU ROI if there is no movement in active CASU ROI minus background bee pixels in passive CASU if there is no movement in passive CASU ROI
3 - background bee pixels in active CASU ROI minus background bee pixels in passive CASU
4 - number of frames with no movement in active CASU ROI
5 - number of frames with no movement in active CASU ROI minus number of frames with no movement in passive CASU ROI
Which fitness function to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'stopped_frames'
                        , 'penalize_passive_casu'
                        , 'background_bees_active_minus_passive'
                        , 'frames_with_no_movement_active_casu_roi'
                        , 'frames_with_no_movement_active_passive_casu_rois'
                    ],
                    x)),
            Parameter (
                'arena_type',
                '''1 - stadium arena
2 - circular arena
Which arena to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'StadiumBorderArena' ,
                        'CircularArena'
                    ],
                    x)),
            Parameter ('frame_per_second', 'Frames per second', parse_data = int),
            Parameter (
                'chromosome_type',
                '''1 - single pulse, pause gene
2 - single pulse, frequency gene
3 - single pulse, frequency gene, active part gene, pause gene
Which chromosome type (vibration pattern) to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'SinglePulseGenePause'
                        , 'SinglePulseGeneFrequency'
                        , 'SinglePulseGenesPulse'
                    ],
                    x)),
            Parameter ('pixel_count_previous_frame_threshold', 'Threshold to use when comparing current frame with a previous frame',       path_in_dictionary = ['image_processing'], parse_data = int, default_value = 1000),
            Parameter ('pixel_count_background_threshold',     'Threshold to use when comparing current frame image with background image', path_in_dictionary = ['image_processing'], parse_data = int, default_value = 1000),
            Parameter (
                'same_colour_threshold',                'Threshold to use when computing difference in pixel color',                 path_in_dictionary = ['image_processing'],
                parse_data = functools.partial (best_config.compose, f = functools.partial (best_config.between, min_value = 0, max_value = 0), g = int), default_value = 25),
            Parameter ('interval_current_previous_frame',      'Time distance between compared frames',                                     path_in_dictionary = ['image_processing'], default_value = 1),
            Parameter (
                'sound_hardware',
                '''1 - CASU
2 - speaker
Which sound hardware to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'Zagreb',
                        'Graz'
                    ],
                    x)),
            Parameter ('elitism', 'Use elitism in evolutionary algorithm', parse_data = best_config.str2bool, default_value = False)
            ])
        self.image_width = 600
        self.image_height = 600
        if os.path.isfile ('config'):
            self.load_from_yaml_file ('config')
        else:
            self.ask_user ()
        if self.sound_hardware == 'Graz':
            if self.chromosome_type == "SinglePulseGenePause":
                self.run_vibration_model = chromosome.SinglePulseGenePause.run_vibration_model_v2
            elif self.chromosome_type == "SinglePulseGeneFrequency":
                self.run_vibration_model = chromosome.SinglePulseGeneFrequency.run_vibration_model_v2
            elif self.chromosome_type == "SinglePulseGenesPulse":
                self.run_vibration_model = chromosome.SinglePulseGenesPulse.run_vibration_model_v2
        elif self.sound_hardware == 'Zagreb':
            if self.chromosome_type == "SinglePulseGenePause":
                self.run_vibration_model = chromosome.SinglePulseGenePause.run_vibration_model
            elif self.chromosome_type == "SinglePulseGeneFrequency":
                self.run_vibration_model = chromosome.SinglePulseGeneFrequency.run_vibration_model
            elif self.chromosome_type == "SinglePulseGenesPulse":
                self.run_vibration_model = chromosome.SinglePulseGenesPulse.run_vibration_model

    def status (self):
        """
        Do a diagnosis of this experimental configuration.
        """
        print ("\n\n* ** Configuration Status ** *")
        bwl = self.number_evaluations_per_episode * (self.evaluation_run_time + self.spreading_waiting_time)
        print ("Bees are going to work %d:%d" % (bwl / 60, bwl % 60), end='')
        if bwl > Config.BEE_WORKDAY_LENGTH:
            print (", which is %d%% more than their workday length." % (int ((bwl - Config.BEE_WORKDAY_LENGTH) * 100.0 / Config.BEE_WORKDAY_LENGTH)))
        else:
            print (", which is below their workday length.")
        if self.number_evaluations_per_episode % self.number_evaluations_per_chromosome == 0:
            print ("When a chromosome is being evaluated, no bee change will occur.  Maybe you are assuming that there are changes from one bee set to another.")
        else:
            print ("When a chromosome is being evaluated, bee changes WILL occur.  You are assuming that all bee sets are equal.")
        print ("Configuration setup to use in this experiment:")
        print ("----------------------------------------------------------------")
        print (self, end='')
        print ("----------------------------------------------------------------")
        raw_input ('Press ENTER to continue. ')

if __name__ == '__main__':
    print ("Debugging config.py")
    c = Config ()
    print (c)
