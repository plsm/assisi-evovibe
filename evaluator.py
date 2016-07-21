import time
import subprocess #spawn new processes
import csv
import Image

class Evaluator:
    """
    Class that implements the evaluator used by the inspyred evoluationary algorithm classes.
    The evaluator computes the fitness function.  Each chromosome represents a vibration model.
    """
    def __init__ (self, config, active_casu, passive_casu, counter, es, episode):
        self.config = config
        self.active_casu = active_casu
        self.passive_casu = passive_casu
        self.counter = counter
        self.es = es
        self.episode = episode
        self.run_vibration_model = None

    def population_evaluator (self, population, args):
        """
        Evaluate a population.  This is main method of this class and the one that is used by the evaluator function of the ES class of inspyred package.
        """
        population_fitnesses = []
        for chromosome in population:
            population_fitnesses.append (self.chromosome_fitness (chromosome))
        return population_fitnesses

    def chromosome_fitness (self, chromosome):
        """
        Compute the fitness of chromosome.  This is the value that is going to be
        used by the evolutionary algorithm in the inspyred package.
        """
        result = 0.0
        fits = []
        for index_evaluation in xrange (self.config.number_evaluations_per_chromosome):
            f = self.exp_step (chromosome, index_evaluation)
            result += f
            fits.append (f)
        self.log_chromosome (chromosome, fits)
        result = result / self.config.number_evaluations_per_chromosome
        return result

        
    def exp_step(self, candidate, index_evaluation):
        """
        Experimental step where a candidate chromosome evaluation is done.
        """
        self.episode.increment_evaluation_counter ()
        print "Episode %d - Evaluation  %d" % (self.episode.episode_index, self.episode.current_evaluation_in_episode)
        (recording_process, filename_real) = self.start_iteration_video ()
        print "         Starting vibration model: " + str (candidate) + "..."
        self.run_vibration_model (candidate, self.active_casu, self.config.evaluation_runtime)
        print "         Vibration model finished!"
        self.spread_bees ()
        recording_process.wait ()
        print "Iteration video finished!"
        (imgpath, imgname_incomplete) = self.split_iteration_video (filename_real)
        self.compare_images (imgpath, imgname_incomplete)
        evaluation_score = self.computeFitness (imgpath, imgname_incomplete)
        print ("\n\niteration " + str (self.episode.current_evaluation_in_episode)+" is finished\n")
        print ("Evaluation of " + str (candidate) + " is " + str (evaluation_score))
        #raw_input ("Press ENTER to continue DEBUG")
        return evaluation_score

    def start_iteration_video (self):
        """
        Starts the iteration video.  This video will record a chromosome evaluation and the bee spreading period.

        :return: a tuple with the process that records the iteration the video filename
        """
        print "\n\n* ** Starting Iteration Video..."
        num_buffers = (self.config.evaluation_runtime + self.config.spreading_waitingtime) * self.config.frame_per_second
        filename_real = self.config.experimentpath + 'iterationVideo_' + str (self.episode.current_evaluation_in_episode) + '.avi'
        bashCommand_video = 'gst-launch-0.10' + \
                            ' --gst-plugin-path=/usr/local/lib/gstreamer-0.10/' + \
                            ' --gst-plugin-load=libgstaravis-0.4.so' + \
                            ' -v aravissrc num-buffers=' + str (int (num_buffers)) + \
                            ' ! video/x-raw-yuv,width=' + str (self.config.arena_image.width) + ',height=' + str (self.config.arena_image.height) + ',framerate=1/' + str (int (1.0 / self.config.frame_per_second)) + \
                            ' ! jpegenc ! avimux name=mux ! filesink location=' + filename_real    # with time - everytime generate a new file
        return (subprocess.Popen (bashCommand_video, shell=True, executable='/bin/bash'), filename_real)

    def spread_bees (self):
        """
        After an evaluation has finished we have to make sure that bees are spread.
        """
        print ("now waiting for " + str (self.config.spreading_waitingtime) + " sec for the bees to spread")
        self.active_casu.set_airflow_intensity (1)
        self.passive_casu.set_airflow_intensity (1)
        self.active_casu.set_diagnostic_led_rgb(r=1,g=0,b=0)
        self.passive_casu.set_diagnostic_led_rgb(r=1,g=0,b=0)
        time.sleep (2) # this should be value dependent on the frame rate (we want to have the led on in the video)
        self.active_casu.diagnostic_led_standby() # to turn the top led off
        self.passive_casu.diagnostic_led_standby() # to turn the top led off
        time.sleep (self.config.spreading_waitingtime - 2) # Time necessary for bees to spread again      
        self.active_casu.airflow_standby ()
        self.passive_casu.airflow_standby ()

    def split_iteration_video (self, filename_real):
        """
        Split the iteration video into images.  We only need the images from the evaluation run time period.

        TODO:
        See how to use the ffmpeg program to only split a part of a video.
        """
        print "\n\n* ** Starting Image Split..."
        imgpath = self.config.experimentpath + "Images/"
        imgname_incomplete = "iterationimage_" + str (self.episode.current_evaluation_in_episode) + "_"
        bashCommandSplit = "ffmpeg" + \
                           " -i " + filename_real + \
                           " -r " + str (self.config.frame_per_second) + \
                           " -f image2 " + imgpath + imgname_incomplete + "%4d.jpg"
        p = subprocess.Popen (bashCommandSplit, shell=True, executable='/bin/bash') #to create and save the real images from the video depending on the iteration number
        p.wait ()
        print ("iteration " + str (self.episode.current_evaluation_in_episode) + " video is splitted")
        print "Image split finished!"
        return (imgpath, imgname_incomplete)
        
    def compare_images (self, imgpath, imgname_incomplete):
        """
        Compare images created in a chromosome evaluation and generate a CSV file.
        The first column has the pixel difference between the current iteration image and the background image in the active CASU.
        The second column has the pixel difference between the current iteration image and the previous iteration image in the active CASU.
        The third column has the pixel difference between the current iteration image and the background image in the passive CASU.
        The fourth column has the pixel difference between the current iteration image and the previous iteration image in the passive CASU.
        """
        fname = self.config.experimentpath + "iteration-" + str (self.episode.current_evaluation_in_episode) + "-data.csv"
        fp = open (fname, 'w')
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        f.writerow (["background_active", "previous_iteration_active", "background_passive", "previous_iteration_passive"])
        background_data = Image.open (imgpath + "Background.jpg").getdata ()
        previous_data = None
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for i in range (1, n + 1):
            fname = imgname_incomplete + "{:04d}.jpg".format (i)
            iteration_data = Image.open (imgpath + fname).getdata ()
            bp = self.config.arena_image.bee_percentage_around_casus (background_data, iteration_data)
            if previous_data != None:
                mb = self.config.arena_image.moving_bees_around_casus (previous_data, iteration_data)
            else:
                mb = (-1, -1)
            row = [bp [0], mb [0], bp [1], mb [1]]
            # row = []
            # for active_casu_flag in [True, False]:
            #     row.append (self.config.arena_image.pixel_count_difference (background_data, iteration_data, active_casu_flag))
            #     if previous_data != None:
            #         row.append (self.config.arena_image.pixel_count_difference (previous_data, iteration_data, active_casu_flag))
            #     else:
            #         row.append (-1)
            f.writerow (row)
            previous_data = iteration_data
        fp.close ()


    def computeFitness (self, imgpath, imgname_incomplete):

        #self.fitness = self.averageBeeCountDifference(imgpath,imgname_incomplete)

        if self.config.fitness_function == 'timeToAggregate':
            time_to_agg = self.timeToAggregate (imgpath, imgname_incomplete)
            print ("time to aggregate:" + str (time_to_agg))
            if time_to_agg > -1:
                result = (self.config.evaluation_runtime - (time_to_agg / self.config.frame_per_second)) / (1.0 * self.config.evaluation_runtime)
            else: # if time_to_agg == -1 it means the aggregation has never happend, so we set the fitness to zero
                result = 0
        elif self.config.fitness_function == 'timeToAggregate_andStay':
            time_to_agg = self.timeToAggregate_andStay (imgpath, imgname_incomplete)
            print ("time to aggregate:" + str (time_to_agg))
            if time_to_agg > -1:
                result = (self.config.evaluation_runtime - (time_to_agg / self.config.frame_per_second)) / (1.0 * self.config.evaluation_runtime)
            else: # if time_to_agg == -1 it means the aggregation has never happend, so we set the fitness to zero
                result = 0
        else:
            raise "Unknown fitness function: " + str (self.config.fitness_function)
            
        print ("fitness: " + str (result))
        return result

    def old_timeToAggregate (self, imgpath, imgname_incomplete):
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
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

    def timeToAggregate (self, imgpath, imgname_incomplete):
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

    def timeToAggregate_andStay(self, imgpath, imgname_incomplete):
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
                if bcount >= self.aggregation_threhsoldN and dcount <= self.config.stopped_threshold:
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

    
    def log_chromosome (self, chromosome, fitnesses):
        """
        Save the result of a chromosome evaluation.
        """
        # Print configurations
#        with open (self.config.experimentpath + "populations/pop_" + str (self.config.num_generations) + ".csv", 'a') as fp:
        with open (self.config.experimentpath + "populations/pop.csv", 'a') as fp:
            f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
            row = [self.es.num_generations + self.counter.base_generation]
            row.extend (chromosome)
            row.extend (fitnesses)
            print (row)
            f.writerow (row)
            fp.close ()
            print ("Chromosome evaluation saved")            

        
        
        
