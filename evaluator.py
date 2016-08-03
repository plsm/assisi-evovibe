#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import subprocess #spawn new processes
import csv
import Image
import assisipy

# Column indexes in file population.csv
POP_GENERATION       = 0
POP_EPISODE          = 1
POP_CHROMOSOME_GENES = 2

# Column indexes in file evaluation.csv
EVA_GENERATION       = 0
EVA_EPISODE          = 1
EVA_ITERATION        = 2
EVA_SELECTED_ARENA   = 3
EVA_ACTIVE_CASU      = 4
EVA_VALUE            = 5
EVA_CHROMOSOME_GENES = 6

class Evaluator:
    """
    Class that implements the evaluator used by the inspyred evolutionary algorithm classes.
    The evaluator computes the fitness value of each chromosome.  Each chromosome represents a vibration model.

    This evaluator is used by inspyred to compute the fitness value of the initial value.
    The evolve method enters a loop whose end condition depends on the terminator used.
    Inside the loop, it selects the next population, evalutes the chromosomes in the population,
    replace chromosomes in the population, archive chromosomes, increment
    the generation number counter, call the observers.

    :param config: A Python object with the following attributes
    """
    def __init__ (self, config, episode, generation_number = 1, continue_values = None):
        self.config = config
        self.episode = episode
        self.generation_number = generation_number
        self.continue_values = continue_values
        # inspyred is moronic because it calls the evaluator to compute the initial fitness,
        # does not increment the generation number, then enters the evolution loop where it
        # first calls the evaluator and then increments the generation number
        self.number_analysed_frames = (int) (self.config.evaluation_run_time * self.config.frame_per_second)

    def population_evaluator (self, population, args = None):
        """
        Evaluate a population.  This is the main method of this class and the one that is used by the evaluator function of the ES class of inspyred package.
        """
        if self.continue_values is None:
            with open (self.config.experiment_folder + "population.csv", 'a') as fp:
                f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
                for chromosome in population:
                    row = [
                        self.generation_number,
                        self.episode.episode_index,
                        ] + chromosome
                    f.writerow (row)
                fp.close ()
            result = [self.chromosome_fitness (chromosome) for chromosome in population]
        else:
            result = [self.chromosome_fitness (chromosome) for chromosome in population]
            self.continue_values = None
        print ("Generation ", self.generation_number, "  Population fitness: " , result)
        self.generation_number += 1
        return result
        
    def chromosome_fitness (self, chromosome):
        """
        Compute the fitness of chromosome.  This is the value that is going to be
        used by the evolutionary algorithm in the inspyred package.
        """
        if self.continue_values is None:
            self.episode.ask_user (chromosome)
            values = [self.iteration_step (chromosome, index_evaluation) for index_evaluation in xrange (self.config.number_evaluations_per_chromosome)]
        else:
            first = True
            values = []
            for index_evaluation in xrange (self.config.number_evaluations_per_chromosome):
                if self.continue_values [0] is None:
                    if first:
                        first = False
                        self.episode.ask_user (chromosome)
                    values.append (self.iteration_step (chromosome, index_evaluation))
                else:
                    values.append (self.continue_values [0])
                self.continue_values = self.continue_values [1:]
        return sum (values) / self.config.number_evaluations_per_chromosome

    def iteration_step (self, candidate, index_evaluation):
        """
        Experimental step where a candidate chromosome evaluation is done.
        """
        self.episode.increment_evaluation_counter ()
        print "\n\nEpisode %d - Evaluation  %d" % (self.episode.episode_index, self.episode.current_evaluation_in_episode)
        picked_arena = self.episode.select_arena ()
        (recording_process, filename_real) = self.start_iteration_video ()
        print "         Starting vibration model: " + str (candidate) + "..."
        picked_arena.run_vibration_model (self.config, candidate)
        print "         Vibration model finished!"
        recording_process.wait ()
        print "Iteration video finished!"
        self.split_iteration_video (filename_real)
        self.compare_images (picked_arena)
        evaluation_score = self.compute_evaluation (picked_arena)
        self.write_evaluation (picked_arena, candidate, evaluation_score)
        print ("Evaluation of " + str (candidate) + " is " + str (evaluation_score))
        #raw_input ("\nPress ENTER to continue DEBUG.\n")
        return evaluation_score
                    
    def start_iteration_video (self):
        """
        Starts the iteration video.  This video will record a chromosome evaluation and the bee spreading period.

        :return: a tuple with the process that records the iteration the video filename
        """
        print "\n\n* ** Starting Iteration Video..."
        num_buffers = (self.config.evaluation_run_time + self.config.spreading_waiting_time) * self.config.frame_per_second
        filename_real = self.episode.current_path + 'iterationVideo_' + str (self.episode.current_evaluation_in_episode) + '.avi'
        bashCommand_video = 'gst-launch-0.10' + \
                            ' --gst-plugin-path=/usr/local/lib/gstreamer-0.10/' + \
                            ' --gst-plugin-load=libgstaravis-0.4.so' + \
                            ' -v aravissrc num-buffers=' + str (int (num_buffers)) + \
                            ' ! video/x-raw-yuv,width=' + str (self.config.image_width) + ',height=' + str (self.config.image_height) + ',framerate=1/' + str (int (1.0 / self.config.frame_per_second)) + \
                            ' ! jpegenc ! avimux name=mux ! filesink location=' + filename_real    # with time - everytime generate a new file
        return (subprocess.Popen (bashCommand_video, shell=True, executable='/bin/bash'), filename_real)


    def split_iteration_video (self, filename_real):
        """
        Split the iteration video into images.  We only need the images from the evaluation run time period.

        The images are written in folder tmp relative to 
        """
        print "\n\n* ** Starting Video Split..."
        bashCommandSplit = "ffmpeg" + \
                           " -i " + filename_real + \
                           " -r " + str (self.config.frame_per_second) + \
                           " -loglevel error" + \
                           " -frames " + str (self.number_analysed_frames) + \
                           " -f image2 tmp/iteration-image-%4d.jpg"
        p = subprocess.Popen (bashCommandSplit, shell=True, executable='/bin/bash') #to create and save the real images from the video depending on the iteration number
        p.wait ()
        print ("Finished spliting iteration " + str (self.episode.current_evaluation_in_episode) + " video.")
        
    def compare_images (self, picked_arena):
        """
        Compare images created in a chromosome evaluation and generate a CSV file.
        The first column has the pixel difference between the current iteration image and the background image in the first CASU.
        The second column has the pixel difference between the current iteration image and the previous iteration image in the first CASU.
        The third column has the pixel difference between the current iteration image and the background image in the second CASU.
        The fourth column has the pixel difference between the current iteration image and the previous iteration image in the second CASU.
        """
        print ("\n\n* ** Comparing Images...")
        fp = open (self.episode.current_path + "image-processing_" + str (self.episode.current_evaluation_in_episode) + ".csv", 'w')
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        f.writerow (["background_A", "previous_iteration_A", "background_B", "previous_iteration_B"])
        for i in xrange (1, self.number_analysed_frames + 1):
            f.writerow (picked_arena.compare_images (i))
        fp.close ()
        print ("Finished comparing images from iteration " + str (self.episode.current_evaluation_in_episode) + " video.")


    def compute_evaluation (self, picked_arena):
        """
        Compute the evaluation of the current chromosome.  This depends on the fitness function property of the configuration file.
        """
        if self.config.fitness_function == 'stopped_frames':
            return self.stopped_frames (picked_arena)
        elif self.config.fitness_function == 'penalize_passive_casu':
            return self.penalize_passive_casu (picked_arena)

    def stopped_frames (self, picked_arena):
        """
        In this function we see if the number of pixels that are different in two consecutive frames is lower than a certain threshold, and if there are many bees in that frame.
        """
        result = 0
        with open (self.episode.current_path + "image-processing_" + str (self.episode.current_evaluation_in_episode) + ".csv", 'r') as fp:
            freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
            freader.next ()
            freader.next ()
            for row in freader:
                if row [picked_arena.selected_worker_index * 2] > self.config.image_processing_pixel_count_background_threshold and row [picked_arena.selected_worker_index * 2 + 1] < self.config.image_processing_pixel_count_previous_frame_threshold:
                    result += row [picked_arena.selected_worker_index * 2]
            fp.close ()
        return result

    def penalize_passive_casu (self, picked_arena):
        """
        In this function we see if the number of pixels that are different in two consecutive frames is lower than a certain threshold, and if there are many bees in that frame.
        """
        result = 0
        with open (self.episode.current_path + "image-processing_" + str (self.episode.current_evaluation_in_episode) + ".csv", 'r') as fp:
            freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
            freader.next () # skip header row
            freader.next () # skip data from frame with LED on
            for row in freader:
                if row [picked_arena.selected_worker_index * 2] > self.config.image_processing_pixel_count_background_threshold and row [picked_arena.selected_worker_index * 2 + 1] < self.config.image_processing_pixel_count_previous_frame_threshold:
                    result += row [picked_arena.selected_worker_index * 2]
                if row [(1 - picked_arena.selected_worker_index) * 2] > self.config.image_processing_pixel_count_background_threshold and row [(1 - picked_arena.selected_worker_index) * 2 + 1] < self.config.image_processing_pixel_count_previous_frame_threshold:
                    result += -row [(1 - picked_arena.selected_worker_index) * 2]
            fp.close ()
        return result

    def write_evaluation (self, picked_arena, candidate, evaluation_score):
        """
        Save the result of a chromosome evaluation.
        """
        with open (self.config.experiment_folder + "evaluation.csv", 'a') as fp:
            f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
            f.writerow ([
                self.generation_number,
                self.episode.episode_index,
                self.episode.current_evaluation_in_episode,
                picked_arena.index,
                picked_arena.workers [picked_arena.selected_worker_index][0],  # active casu number
                evaluation_score] + candidate)
            fp.close ()

        
        
        
