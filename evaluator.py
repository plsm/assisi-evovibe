#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import subprocess #spawn new processes
import csv
import Image
import assisipy

class Counter:
    """
    Maintains a counter on the current state of the incremental evolution algorithm.
    Since the program has to be stopped at the end of the day and resumed in the following day, we need to compute where we are when we resume.
    Namely, we need to know the current generation number, and in a generation which chromosome is being evaluated.
    """
    def __init__ (self, first_iteration = True):
        if first_iteration:
            self.base_generation = 0
            self.base_evaluation_in_generation = 0
        else:
            self.base_generation = -999
            self.base_evaluation_in_generation = -999

class Evaluator:
    """
    Class that implements the evaluator used by the inspyred evolutionary algorithm classes.
    The evaluator computes the fitness function.  Each chromosome represents a vibration model.

    :param config: A Python object with the following attributes
    """
    def __init__ (self, config, es, episode, counter = Counter ()):
        self.config = config
        self.es = es
        self.episode = episode
        self.counter = counter
        self.number_analysed_frames = (int) (self.config.evaluation_run_time * self.config.frame_per_second)

    def population_evaluator (self, population, args = None):
        """
        Evaluate a population.  This is main method of this class and the one that is used by the evaluator function of the ES class of inspyred package.
        """
        with open (self.config.experiment_folder + "population.csv", 'a') as fp:
            f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
            for chromosome in population:
                row = [
                    self.es.num_generations + self.counter.base_generation,
                    self.episode.episode_index,
                    ] + chromosome
                f.writerow (row)
            fp.close ()
        result = [self.chromosome_fitness (chromosome) for chromosome in population]
        print ("Population fitness: " , result)
        return result
#        population_fitnesses = []
#        for chromosome in population:
#            population_fitnesses.append (self.chromosome_fitness (chromosome))
#        return population_fitnesses

    def chromosome_fitness (self, chromosome):
        """
        Compute the fitness of chromosome.  This is the value that is going to be
        used by the evolutionary algorithm in the inspyred package.
        """
        values = [self.iteration_step (chromosome, index_evaluation) for index_evaluation in xrange (self.config.number_evaluations_per_chromosome)]
        return sum (values) / self.config.number_evaluations_per_chromosome
        # result = 0.0
        # fits = []
        # for index_evaluation in xrange (self.config.number_evaluations_per_chromosome):
        #     f = self.iteration_step (chromosome, index_evaluation)
        #     result += f
        #     fits.append (f)
        # result = result / self.config.number_evaluations_per_chromosome
        # self.write_fitness (chromosome, result)
        # ########################### check code at this point
        # return result

        
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
        fp = open ("tmp/image-processing.csv", 'w')
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

    def stopped_frames (self, picked_arena):
        """
        In this function we see if the number of pixels that are different in two consecutive frames is lower than a certain threshold, and if there are many bees in that frame.
        """
        result = 0
        with open ("tmp/image-processing.csv", 'r') as fp:
            freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
            freader.next ()
            freader.next ()
            for row in freader:
                if row [picked_arena.selected_worker_index * 2] > 100 and row [picked_arena.selected_worker_index * 2 + 1] < 100:
                    result += 1
            fp.close ()
        return result

    def old_timeToAggregate (self, imgpath, imgname_incomplete):
        n = (int) (self.config.evaluation_run_time * self.config.frame_per_second)
        for i in range (1, n + 1):
            fname = imgname_incomplete + "{:04d}.jpg.csv".format (i)
            with open (imgpath + fname, 'rb') as csvfile:
                freader = csv.reader (csvfile, delimiter=';')
                #first row header, second row values
                row = freader.next()
                row = freader.next()
                bcount = float (row [0])   #-float(row[0])   ### MAKE SURE ABOUT THE ORDER OF THE CASUS: WHICH ONE IS VIBRATING ACCORDING TO GERALDS SOFTWARE
                if bcount >= self.config.aggregation_threhsoldN:
                    return i
            # Check with Ziad: why this sleep?
            #time.sleep (1);
        return -1

    def timeToAggregate (self):
        """
        Read the CSV file that resulted from processing an iteration images.
        """
        fname = self.config.experimentpath + "iteration-" + str (self.episode.current_evaluation_in_episode) + "-data.csv"
        fp = open (fname, 'r')
        freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        freader.next () # skip header row
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for i in range (1, n + 1):
            row = freader.next ()
            bcount = float (row [0])
            dcount = float (row [1])
            if bcount >= self.config.aggregation_threhsoldN and dcount <= self.config.stopped_threshold:
                fp.close ()
                return i
        fp.close ()
        return -1

    def timeToAggregate_andStay (self):
        agg_status = False
        agg_start = -1
        #aggregation_happend_at = -1
        
        fname = self.config.experimentpath + "iteration-" + str (self.episode.current_evaluation_in_episode) + "-data.csv"
        fp = open (fname, 'r')
        freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        freader.next () # skip header row
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for i in range(1,n+1):
                row = freader.next()
                bcount = float (row [0])   #-float(row[0])   ### MAKE SURE ABOUT THE ORDER OF THE CASUS: WHICH ONE IS VIBRATING ACCORDING TO GERALDS SOFTWARE
                dcount = float (row [1])
                if bcount >= self.config.aggregation_threhsoldN and dcount <= self.config.stopped_threshold:
                    if agg_status==False:
                        agg_status = True
                        agg_start = i
                    elif agg_status==True and i - agg_start >= self.config.aggregation_minDuration_thresh:
                        #aggregation_happend_at = agg_start
                        return aggregation_happend_at
                else:
                    agg_status = False
                    agg_start = -1
        return -1

    def fitness_non_moving_pixels_bee_blobs (self):
        """This function computes the sum of the number of non-moving pixels in frames
        where there are bee blobs
        in the active CASU.

        This fitness function depends on the aggregation threshold which is
        the percentage of pixels that are different when considering the
        background and an iteration.

        """
        result = 0
        fname = self.config.experimentpath + "iteration-" + str (self.episode.current_evaluation_in_episode) + "-data.csv"
        fp = open (fname, 'r')
        freader = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        freader.next () # skip header row
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for i in xrange (1, n + 1):
            row = freader.next ()
            bcount = float (row [0])   #-float(row[0])   ### MAKE SURE ABOUT THE ORDER OF THE CASUS: WHICH ONE IS VIBRATING ACCORDING TO GERALDS SOFTWARE
            dcount = float (row [1])
            if bcount >= self.config.aggregation_threhsoldN:
                result += self.config.stopped_threshold - dcount
        return result

    def write_evaluation (self, picked_arena, candidate, evaluation_score):
        with open (self.config.experiment_folder + "evaluation.csv", 'a') as fp:
            f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
            f.writerow ([
                self.es.num_generations + self.counter.base_generation,
                self.episode.episode_index,
                picked_arena.index,
                picked_arena.workers [picked_arena.selected_worker_index][0],  # active casu number
                evaluation_score] + candidate)
            fp.close ()
    
    def write_fitness (self, chromosome, fitness):
        """
        Save the result of a chromosome evaluation.
        """
        with open (self.config.experiment_folder + "population.csv", 'a') as fp:
            f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
            row = [
                self.es.num_generations + self.counter.base_generation,
                self.episode.episode_index,
                fitness
                ] + chromosome
            print (row)
            f.writerow (row)
            fp.close ()
            print ("Chromosome evaluation saved")            

        
        
        
