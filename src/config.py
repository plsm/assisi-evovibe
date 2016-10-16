#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import functools
import sys

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

    def __init__ (self, filename = 'config'):
        best_config.Config.__init__ (self, [
            Parameter ('number_bees',                    'Number of bees', parse_data = int),
            Parameter ('bee_area_pixels',                'Number of pixels occupied by a bee', parse_data = int, default_value = 850),
            Parameter ('number_generations',             'Number of generations of the evolutionary algorithm', parse_data = int),
            Parameter ('number_evaluations_per_episode', 'How many evaluations to perform with a set of bees', parse_data = int),
            Parameter ('bee_relax_time',                 'How many seconds to wait before testing the first vibration pattern in a set of bees', parse_data = int, default_value = 0),
            Parameter ('evaluation_run_time',    'Time in seconds of the total vibration pattern', parse_data = int, default_value = -1),
            Parameter ('vibration_run_time',    'Time in seconds of the vibration segment'                    , parse_data = int, default_value = -1, path_in_dictionary = ['evaluation']),
            Parameter ('no_stimuli_run_time',  'Time in seconds of the no stimuli segment'                  , parse_data = int, default_value = 0 , path_in_dictionary = ['evaluation']),
            Parameter ('number_repetitions',    'Number of repetitions of vibration plus no stimuli segments', parse_data = int, default_value = 0 , path_in_dictionary = ['evaluation']),
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
6 - number of frames with no movement during vibration segments over number of frames with movement during no stimuli segments in active CASU ROI
Which fitness function to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'stopped_frames'
                        , 'penalize_passive_casu'
                        , 'background_bees_active_minus_passive'
                        , 'frames_with_no_movement_active_casu_roi'
                        , 'frames_with_no_movement_active_passive_casu_rois'
                        , 'ratio_frames_with_no_movement_vibration_over_no_stimuli'
                    ],
                    x)),
            Parameter (
                'arena_type',
                '''1 - stadium arena
2 - circular arena
3 - two rectangular boxes arena
Which arena to use''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'StadiumBorderArena' ,
                        'CircularArena',
                        'TwoBoxesArena'
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
            Parameter (
                'evaluation_values_reduce',
                '''1 - average
2 - average without maximum and minimum
3 - weighted average
Which method to use when computing the chromosome fitness from a set of evaluations''',
                parse_data = lambda x : best_config.list_element (
                    [
                        'average'
                        , 'average_without_best_worst'
                        , 'weighted_average'
                    ],
                    x),
                default_value = 'average'
            ),
            Parameter ('vibration_period',  'vibration period used in chromosome with single gene that represents vibration frequency', path_in_dictionary = ['chromosome', 'single_pulse_gene_frequency'], parse_data = int, default_value = -1),
            Parameter ('image_width',  'Image width in pixels',  parse_data = int, default_value = 600),
            Parameter ('image_height', 'Image height in pixels', parse_data = int, default_value = 600),
            Parameter ('elitism', 'Use elitism in evolutionary algorithm', parse_data = best_config.str2bool, default_value = False)
            ])
        if os.path.isfile (filename):
            self.load_from_yaml_file (filename)
        else:
            self.ask_user ()
        try:
            cm = None
            cm = chromosome.CHROMOSOME_METHODS [self.chromosome_type]
            self.run_vibration_model = cm.run_vibration_model [self.sound_hardware]
        except KeyError as e:
            if cm is None:
                print ('Invalid chromosome type', self.chromosome_type)
            else:
                print ('Invalid sound hardware', self.sound_hardware)
            sys.exit (1)
        if self.vibration_period != -1:
            chromosome.SinglePulseGeneFrequency.VIBRATION_PERIOD = self.vibration_period
        if self.vibration_run_time == -1:
            self.parameters_as_dict ['vibration_run_time'].value = self.evaluation_run_time
            print ('\nUsing deprecated configuration parameter \'evaluation_run_time\' for parameter \'vibration_run_time\'')
            raw_input ('Press ENTER to continue')
        self._evaluation_run_time = self.number_repetitions * (self.vibration_run_time + self.no_stimuli_run_time) + self.vibration_run_time

    def status (self):
        """
        Do a diagnosis of this experimental configuration.
        """
        print ("\n\n* ** Configuration Status ** *")
        bwl = self.number_evaluations_per_episode * (self._evaluation_run_time + self.spreading_waiting_time)
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
