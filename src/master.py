#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import arena
import episode
import evaluator
import chromosome
import worker

import assisipy.deploy
import assisipy.assisirun

import inspyred

import argparse
import os
import csv
import random
#import yaml
#import zmq
#import zmq_sock_utils

import worker_settings

# class WorkerSettings:
#     """
#     Worker settings used by the master program to deploy the workers.
#     These settings specify the CASU that the worker will control,
#     the ZMQ address where the worker will listen for commands from the master,
#     and the parameters of the RTC file.
#     """
#     def __init__ (self, dictionary):
#         self.casu_number = dictionary ['casu_number']
#         self.wrk_addr    = dictionary ['wrk_addr']
#         self.pub_addr    = dictionary ['pub_addr']
#         self.sub_addr    = dictionary ['sub_addr']
#         self.msg_addr    = dictionary ['msg_addr']
#         self.socket = None
#         self.in_use = False
#     def __key_ (self):
#         return 'casu-%03d' % (self.casu_number)
#     def to_dep (self):
#         return (
#             self.__key_ () ,
#             {
#                 'controller' : os.path.dirname (os.path.abspath (__file__)) + '/worker.py'
#               , 'extra'      : [
#                     os.path.dirname (os.path.abspath (__file__)) + '/chromosome.py'
#                   , os.path.dirname (os.path.abspath (__file__)) + '/zmq_sock_utils.py'
#                   ]
#               , 'args'       : [str (self.casu_number), 'tcp://*:%s' % (self.wrk_addr.split (':') [2])]
#               , 'hostname'   : self.wrk_addr.split (':') [1][2:]
#               , 'user'       : 'assisi'
#               , 'prefix'     : 'pedro/evovibe'
#               , 'results'    : []
#             })
#     def to_arena (self):
#         return (
#             self.__key_ () ,
#             {
#                 'pub_addr' : self.pub_addr
#               , 'sub_addr' : self.sub_addr
#               , 'msg_addr' : self.msg_addr
#             })
#     def connect_to_worker (self, config):
#         """
#         Connect to the worker and return a tuple with the CASU number and this instance.
#         """
#         context = zmq.Context ()
#         print ("Connecting to worker at %s responsible for casu #%d..." % (self.wrk_addr, self.casu_number))
#         self.socket = context.socket (zmq.REQ)
#         self.socket.connect (self.wrk_addr)
#         print ("Initializing worker responsible for casu #%d..." % (self.casu_number))
#         answer = zmq_sock_utils.send_recv (self.socket, [worker.INITIALISE, config.evaluation_run_time, config.spreading_waiting_time, config.frame_per_second, config.sound_hardware, config.chromosome_type])
#         print ("Worker responded with: %s" % (str (answer)))
#         return (self.casu_number, self)
#     def terminate_session (self):
#         """
#         Terminate the session with the worker, which causes the worker process to finish.
#         """
#         print ("Sending terminate command to worker at %s responsible for casu #%d..." % (self.wrk_addr, self.casu_number))
#         answer = zmq_sock_utils.send_recv (self.socket, [worker.TERMINATE])
#         print ("Worker responded with: %s" % (str (answer)))

# def load_worker_settings (filename):
#     """
#     Return a list with the worker settings loaded from a file with the given name.
#     """
#     file_object = open (filename, 'r')
#     dictionary = yaml.load (file_object)
#     file_object.close ()
#     worker_settings = [
#         WorkerSettings (dictionary ['worker-%02d' % (index)])
#         for index in xrange (1, dictionary ['number_workers'] + 1)]
#     print ("Loaded worker settings")
#     return worker_settings

# def deploy_workers (filename, run_number):
#     print ('\n\n* ** Worker Apps Launch')
#     # load worker settings
#     worker_settings = load_worker_settings (filename)
#     # create assisi file
#     fp_assisi = open ('tmp/workers.assisi', 'w')
#     yaml.dump ({'arena' : 'workers.arena'}, fp_assisi, default_flow_style = False)
#     yaml.dump ({'dep' : 'workers.dep'}, fp_assisi, default_flow_style = False)
#     fp_assisi.close ()
#     print ("Created assisi file")
#     # create dep file
#     fp_dep = open ('tmp/workers.dep', 'w')
#     yaml.dump ({'arena' : dict ([ws.to_dep () for ws in worker_settings])}, fp_dep, default_flow_style = False)
#     fp_dep.close ()
#     print ("Created dep file")
#     # create arena file
#     fp_arena = open ('tmp/workers.arena', 'w')
#     yaml.dump ({'arena' : dict ([ws.to_arena () for ws in worker_settings])}, fp_arena, default_flow_style = False)
#     fp_arena.close ()
#     print ("Created arena file")
#     # deploy the workers
#     d = assisipy.deploy.Deploy ('tmp/workers.assisi')
#     d.prepare ()
#     d.deploy ()
#     ar = assisipy.assisirun.AssisiRun ('tmp/workers.assisi')
#     ar.run ()
#     print ("Workers have finished")

def parse_arguments ():
    """
    Parse the command line arguments.
    """
    parser = argparse.ArgumentParser (
        description = 'Incremental Evolution of vibration models to aggregate bees.',
        argument_default = None
    )
    parser.add_argument (
        '--command', '-c',
        default = None,
        type = str,
        help = 'what should we do?\n\tnew-run: perform a new experimental run\n\tcontinue-run: continue a previous run')
    parser.add_argument (
        '--run', '-r',
        default = None,
        type = int,
        help = "run number to use")
    parser.add_argument (
        '--debug',
        action = 'store_true',
        help = "enable debug mode")
    parser.add_argument (
        '--deploy',
        action = 'store_true',
        help = "deploy the workers automatically")
    parser.add_argument (
        '--workers',
        default = 'workers',
        type = str,
        help = 'worker settings file to load')
    return parser.parse_args ()


def calculate_experiment_folder_for_new_run (args):
    """
    Compute the experiment folder for a new experimental run.
    This folder is where all the files generated by an experimental run are stored.
    """
    run_number = 1
    while True:
        result = 'run-%03d/' % (run_number)
        if args.debug or not os.path.isdir (result) and not os.path.exists (result):
            return result
        run_number += 1

def create_directories_for_experimental_run (experiment_folder, args):
    """
    Create the directories for an experimental run.
    """
    for path in [
            experiment_folder,
            experiment_folder + "logs/",
            experiment_folder + "episodes/"]:
        try:
            os.makedirs (path)
        except:
            if not args.debug:
                raise

def create_experimental_run_files (experiment_folder):
    """
    Create the files that are going to store the data produced by an experimental run.
    The data is stored in CSV files.  The files are initialized with a header row.
    """
    with open (experiment_folder + "population.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        row = ["generation", "episode", "chromosome_genes"]
        f.writerow (row)
        fp.close ()
    with open (experiment_folder + "evaluation.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        row = ["generation", "episode", "iteration", "selected_arena", "active_casu", "value", "chromosome_genes"]
        f.writerow (row)
        fp.close ()
    with open (experiment_folder + "fitness.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        row = ["generation", "fitness", "chromosome_genes"]
        f.writerow (row)
        fp.close ()

def check_run (args):
    run_number = args.run
    result = 'run-%03d/' % (run_number)
    if os.path.isdir (result):
        return result
    else:
        print "There is no run ", run_number
        sys.exit (1)

def load_population_and_evaluation (config, experiment_folder):
    with open (experiment_folder + "population.csv", "r") as fp:
        f = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        f.next () #skip header_row
        rows = [row for row in f]
        initial_population = [row [evaluator.POP_CHROMOSOME_GENES:] for row in rows]
        print (initial_population)
        current_generation = int (rows [-1][evaluator.POP_GENERATION])
        current_episode = int (rows [-1][evaluator.POP_EPISODE])
        s = initial_population [-config.population_size:]
        seeds = [[int (g) for g in c] for c in s]  # I'm assuming that all genes are integers.
        fp.close ()
    with open (experiment_folder + "evaluation.csv", "r") as fp:
        f = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        f.next () #skip header_row
        eva_values = []
        for row in f:
            if row [evaluator.EVA_GENERATION] == current_generation:
                eva_values.append (row [evaluator.EVA_VALUE])
        eva_values += [None] * (config.population_size * config.number_evaluations_per_chromosome - len (eva_values))
        fp.close ()
    return (current_generation, current_episode + 1, seeds, eva_values)

def fitness_save_observer (population, num_generations, num_evaluations, args):
    """
    Observer passed to inspyred evolutionary algorithm to save the data to file fitness.csv.
    """
    config_experiment_folder = args ['config_experiment_folder']
    with open (config_experiment_folder + "fitness.csv", 'a') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        for individual in population:
            row = [num_generations, individual.fitness] + individual.candidate
            f.writerow (row)
        fp.close ()

def run_inspyred_ES (config, worker_stubs, experiment_folder, current_generation = 1, episode_index = 1, seeds = None, eva_values = None):
    """
    Run the Evolutionary Strategy for the given configuration.
    """
    epsd = episode.Episode (config, worker_stubs, experiment_folder, episode_index)
    epsd.initialise ()
    es = inspyred.ec.ES (random.Random ())
    evltr = evaluator.Evaluator (config, epsd, experiment_folder, current_generation, eva_values)
    es.terminator = [inspyred.ec.terminators.generation_termination]
    es.observer = [fitness_save_observer]
    if config.chromosome_type == "SinglePulseGenePause":
        es.variator = [chromosome.SinglePulseGenePause.get_variator ()]
        generator = chromosome.SinglePulseGenePause.random_generator
    elif config.chromosome_type == "SinglePulseGeneFrequency":
        es.variator = [chromosome.SinglePulseGeneFrequency.get_variator ()]
        generator = chromosome.SinglePulseGeneFrequency.random_generator
    elif config.chromosome_type == "SinglePulseGenesPulse":
        es.variator = [chromosome.SinglePulseGenesPulse.get_variator ()]
        generator = chromosome.SinglePulseGenesPulse.random_generator
    es.evolve (
        generator = generator,
        evaluator = evltr.population_evaluator,
        pop_size = config.population_size,
        bounder = None,
        maximize = True,
        max_generations = config.number_generations,
        seeds = seeds,
        config_experiment_folder = experiment_folder)
    print ("\n\n* ** The End")
    epsd.finish (True)
    for ws in worker_stubs.values ():
        ws.terminate_session ()
    print ("Evolutionary Strategy algorithm finished!")
    
def run_inspyred (config, worker_stubs, experiment_folder, current_generation = 1, episode_index = 1, seeds = None, eva_values = None):
    """
    Run the Evolutionary Strategy for the given configuration.
    """
    epsd = episode.Episode (config, worker_stubs, experiment_folder, episode_index)
    epsd.initialise ()
    evocom = inspyred.ec.EvolutionaryComputation (random.Random ())
    evltr = evaluator.Evaluator (config, epsd, experiment_folder, current_generation, eva_values)
    evocom.terminator = [inspyred.ec.terminators.generation_termination]
    evocom.observer = [fitness_save_observer]
    evocom.replacer = inspyred.ec.replacers.generational_replacement
    if config.chromosome_type == "SinglePulseGenePause":
        evocom.variator = [chromosome.SinglePulseGenePause.get_variator ()]
        generator = chromosome.SinglePulseGenePause.random_generator
    elif config.chromosome_type == "SinglePulseGeneFrequency":
        evocom.variator = [chromosome.SinglePulseGeneFrequency.get_variator ()]
        generator = chromosome.SinglePulseGeneFrequency.random_generator
    elif config.chromosome_type == "SinglePulseGenesPulse":
        evocom.variator = [chromosome.SinglePulseGenesPulse.get_variator ()]
        generator = chromosome.SinglePulseGenesPulse.random_generator
    evocom.evolve (
        generator = generator,
        evaluator = evltr.population_evaluator,
        pop_size = config.population_size,
        bounder = None,
        maximize = True,
        max_generations = config.number_generations,
        seeds = seeds,
        config_experiment_folder = experiment_folder,
        num_elites = 1 if config.elitism else 0
    )
    print ("\n\n* ** The End")
    epsd.finish (True)
    for ws in worker_stubs.values ():
        ws.terminate_session ()
    print ("Evolutionary Strategy algorithm finished!")
    
try:
    os.makedirs ("tmp")
except OSError:
    pass
args = parse_arguments ()
if args.command in ['new-run', 'new_run']:
    cfg = config.Config ()
    cfg.status ()
    worker_stubs = dict ([ws.connect_to_worker (cfg) for ws in worker_settings.load_worker_settings (args.workers)])
    print worker_stubs
    experiment_folder = calculate_experiment_folder_for_new_run (args)
    create_directories_for_experimental_run (experiment_folder, args)
    create_experimental_run_files (experiment_folder)
    run_inspyred (cfg, worker_stubs, experiment_folder)
elif args.command in ['continue-run', 'continue_run']:
    cfg = config.Config ()
    cfg.status ()
    experiment_folder = check_run (args)
    current_generation, current_episode, seeds, eva_values = load_population_and_evaluation (cfg, experiment_folder)
    worker_stubs = dict ([ws.connect_to_worker (cfg) for ws in worker_settings.load_worker_settings (args.workers)])
    print worker_stubs
    run_inspyred (cfg, worker_stubs, experiment_folder, current_generation, current_episode + 1, seeds, eva_values)
elif args.command in ['deploy']:
    worker_settings.deploy_workers (args.workers, None)
elif args.command == None:
    print ("Nothing to do!\n")
else:
    print ("Unknown command: %s" % args.command)
