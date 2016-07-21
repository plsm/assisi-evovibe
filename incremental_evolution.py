import config
import chromosome
import evaluator
import episode
import experiment

from assisipy import casu

import inspyred

import copy
import time
import random
import subprocess #spawn new processes
import os
import csv

class IncrementalEvolution:
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

    def __init__ (self, cfg, epsd):
        """Constructs an incremental evolution algorithm"""
        self.config = cfg
        self.episode = epsd
        prng = random.Random ()
        self.es = inspyred.ec.ES (prng)
        self.es.experimentpath = self.config.experimentpath
        self.counter = IncrementalEvolution.Counter ()

    def load_initial_population (self, population_filename):
        """Reads a CSV file with population"""
        pass

    def exp_init (self):
        """Initialize the experimental setup.  Check folder existance, connect to CASU."""
        #check if the experimentlog and repository folders are created by the user
        if not os.path.isdir (self.config.experimentpath):
            print "Experiment log folder does not exists: " + self.config.experimentpath
            exit (1)
        if not os.path.isdir (self.config.repositorypath):
            print "Repository folder does not exist: " + self.config.repositorypath
            exit (2)

        self.iteration_zero = -1    #to know if it is the first attiration at the beggeining allocate to -1
        while self.iteration_zero == -1: #it does not know yet
            isInitial = raw_input('\nis this an initial iteration (Y/N)? ')
            if isInitial=='y' or isInitial=='Y':
                self.iteration_zero = True
            elif isInitial=='n' or isInitial=='N':
                self.iteration_zero = False
            else:
                self.iteration_zero = -1

        dirs = os.listdir( self.config.experimentpath )  #looks for the folder and makes a list of the files in the folder
        if self.iteration_zero:    # this to make sure that the files are not overwritten
            for a in dirs:
                filename_base = "configdata"
                ind = a.find(filename_base)
                if ind>-1:
                    print("There is already a logdata in this folder")
                    exit()
            #self.iteration_num = 0 #first iteration start new experement
        #else:    # read settings from files and proceed if not itration 0...
            #self.loadDataFromFile()
            #self.iteration_num += 1

        #raw_input('\nPlease switch off the CASUs (to make the background image for the image processing software) and then enter when ready')
        
        self.connect_casu ()
        self.episode.initialise ()

    def connect_casu (self):
        """
        Create the CASU instances that are going to be used by the chromosome evaluation functions.
        Initialise the CASUs so that we can create the background image.
        """
        self.casu1 = casu.Casu (
            rtc_file_name = self.config.active_casu_rtc_file_name,
            log = True,
            log_folder = "logs")
        self.casu2 = casu.Casu (
            rtc_file_name = self.config.passive_casu_rtc_file_name,
            log = True,
            log_folder = "logs")
        for a_casu in [self.casu1, self.casu2]:
            a_casu.diagnostic_led_standby () # turn the top led off
            a_casu.set_speaker_vibration (freq = 0, intens = 0)
            a_casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
            a_casu.ir_standby ()             # turn the IR sensor off to make the background image
            a_casu.set_temp (28)
            a_casu.airflow_standby ()

    def random_evaluator (self, candidates, args):
        """
        Random chromosome evaluator that is used for debugging purposes.
        """
        fit = []
        print ("candidates length: " + str (len (candidates)))
        for c in candidates:
            f = random.uniform (0, 1)
            print (str (c) + " @ " + str (f))
            fit.append (f)
        return fit

    def steps_all_chromosomes (self):
        return [
        (
        "chromosome with only frequency gene",             # t title
        self.config.generations_with_chromosome_frequency, # n number of generations
        chromosome.GF_SCAI.random_generator,               # r random generator
        chromosome.GF_SCAI.Bounder (),                     # b chromosome bounder
        chromosome.GF_SCAI.run_vibration_model,            # f used by fitness function
        chromosome.GFI.promote_GF_SCAI),                   # p promote chromosome to next step
                    ("chromosome with frequency and intensity gene",
                  self.config.generations_with_chromosome_freq_inten,
                  chromosome.GF_SCAI.random_generator,
                  chromosome.GF_SCAI.Bounder (),
                  chromosome.GF_SCAI.run_vibration_model,
                  chromosome.NatureDraftChromosome.promote_GFI),
                ("chromosome with nature draft paper genes",
                 self.config.generations_with_chromosome_nature_draft,
                  chromosome.NatureDraftChromosome.random_generator,
                  chromosome.NatureDraftChromosome.bounder,
                  chromosome.NatureDraftChromosome.run_vibration_model,
                  None)]
    
    def steps_only_frequency (self):
        return [(
            "chromosome with only frequency gene",
            self.config.generations_with_chromosome_frequency,
            chromosome.GF_SCAI.random_generator,
            chromosome.GF_SCAI.Bounder (),
            chromosome.GF_SCAI.run_vibration_model,
            None)]

    def steps_only_frequency_with_vibration_pause (self):
        return [(
            "chromosome with frequency gene, vibration time gene, pause time gene",
            self.config.generations_with_chromosome_frequency_with_vibration_pause,
            chromosome.GFPD_SCAI.random_generator,
            chromosome.GFPD_SCAI.Bounder (),
            chromosome.GFPD_SCAI.run_vibration_model,
            None)]
            
    def steps_GP_GP450 (self):
        return [(
            "chromosome with pause time gene",
            self.config.generations_GP_F450,
            chromosome.GP_F450.random_generator,
            chromosome.GP_F450.bounder,
            chromosome.GP_F450.run_vibration_model,
            None)]
    
    def steps_GP_GP440 (self):
        return [(
            "chromosome with pause time gene",
            self.config.generations_GP_F440,
            chromosome.GP_F440.random_generator,
            chromosome.GP_F440.bounder,
            chromosome.GP_F440.run_vibration_model,
            None)]
    

    def main (self):
        #print self.config
        self.connect_casu ()
        eva = evaluator.Evaluator (self.config, self.casu1, self.casu2, self.counter, self.es, self.episode)
        the_evaluator = eva.population_evaluator
        # the steps of the incremental evolution algorithm
        # a list with tuple (t,n,r,b,f,p)
        #
        # t title
        # n number of generations
        steps = self.steps_GP_GP440 ()
        previous_population = None
        self.episode.initialise ()
        for (t, n, r, b, f, p) in steps:
            if n > 0:
                print "running", n, "generations of", t
                eva.run_vibration_model = f
                next_population = self.es.evolve (
                    generator = r,
                    evaluator = the_evaluator,
                    pop_size = self.config.population_size,
                    bounder = b,
                    maximize = True,
                    max_generations = n,
                    seeds = previous_population)
            else:
                print "skipping", t
                next_population = copy.copy (previous_population)
            if p is not None:
                previous_population = []
                for i in next_population:
                    print "Promoting", i
                    previous_population.extend ([p (i)])
                print previous_population
        self.episode.finish (True)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser (
        description = 'Incremental Evolution of vibration models to aggregate bees.',
        argument_default = None
    )
    parser.add_argument (
        '--config-file',
        default = 'experiment_repository/config.txt',
        type = str,
        help = 'the file name with the experiment configuration')
    args = parser.parse_args ()
    cfg = config.Config (args.config_file)
    experiment.create_directories (cfg)
    cfg.status ()
    epsd = episode.Episode (cfg)
    experiment.initialize_files (cfg)
    ie = IncrementalEvolution (cfg, epsd)
    ie.main ()
