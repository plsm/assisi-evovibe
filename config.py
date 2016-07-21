#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import image

from __future__ import print_function

import yaml

class Config:
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
        file_object = open ('config', 'r')
        dictionary = yaml.load (file_object)
        file_object.close ()
        #DEBUG print dictionary
        try:
            self.number_bees                        = dictionary ['number_bees']
            self.number_generations                 = dictionary ['number_generations']
            self.number_evaluations_per_episode     = dictionary ['number_evaluations_per_episode']
            self.evaluation_run_time                = dictionary ['evaluation_run_time']
            self.spreading_waiting_time             = dictionary ['spreading_waiting_time']
            self.population_size                    = dictionary ['population_size']
            self.number_evaluations_per_chromosome  = dictionary ['number_evaluations_per_chromosome']
            self.stopped_threshold                  = dictionary ['stopped_threshold']
            self.aggregation_minDuration_thresh     = dictionary ['aggregation_minDuration_thresh']
            self.fitness_function                   = dictionary ['fitness_function']
            self.arena_type                         = dictionary ['arena_type']
            self.constant_airflow                   = dictionary ['constant_airflow']
            self.frame_per_second                   = dictionary ['frame_per_second']
            self.image_width                        = dictionary ['image']['width']
            self.image_height                       = dictionary ['image']['height']
        except KeyError as e:
            print ("The configuration file does not have parameter '%s'\n" % (str (e)))
            raise
        self.aggregation_threhsoldN = 55 # Threshold for the number of bees aggregated around the vibrating CASU


    def status (self):
        """
        Do a diagnosis of this experimental configuration.
        """
        print ("\n\n\n* ** Configuration Status ** *")
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
        print ("Configuration file read:")
        print ("----------------------------------------------------------------")
        print (self, end='')
        print ("----------------------------------------------------------------")
        raw_input ('Press ENTER to continue')

    def __str__ (self):
        return """number_bees : %d
number_generations: %d
number_evaluations_per_episode: %d
evaluation_run_time: %d
spreading_waiting_time: %d
population_size: %d
number_evaluations_per_chromosome: %d
stopped_threshold : %d
aggregation_minDuration_thresh : %d
fitness_function : %s
constant_airflow : %s
arena_type : %s
frame_per_second : %d
image :
    width : %d
    height : %d
""" % (self.number_bees,
       self.number_generations,
       self.number_evaluations_per_episode,
       self.evaluation_run_time,
       self.spreading_waiting_time,
       self.population_size,
       self.number_evaluations_per_chromosome,
       self.stopped_threshold,
       self.aggregation_minDuration_thresh,
       self.fitness_function,
       str (self.constant_airflow),
       self.arena_type,
       self.frame_per_second,
       self.image_width,
       self.image_height)

if __name__ == '__main__':
    print ("Debugging config.py")
    c = Config ('config')
    print (c)
