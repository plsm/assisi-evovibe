#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import arena
import episode
import evaluator
import chromosome

import inspyred

import argparse
import os
import csv
import random

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
        help = 'what should we do? new-run: perform a new experimental run')
    parser.add_argument (
        '--run', '-r',
        default = None,
        type = int,
        help = "run number to use")
    parser.add_argument (
        '--debug',
        action = 'store_true',
        help = "enable debug mode")
    return parser.parse_args ()


def calculate_experiment_folder_for_new_run (config, args):
    """
    Compute the experiment folder for a new experimental run.  This folder is where all the files generated by an experimental run are stored.
    """
    run_number = 1
    print args.debug, ("sim" if args.debug else "não")
    while True:
        result = 'run-%03d/' % (run_number)
        if args.debug or not os.path.isdir (result) and not os.path.exists (result):
            config.experiment_folder = result
            return
        run_number += 1

def create_directories_for_experimental_run (config):
    """
    Create the directories for an experimental run.
    """
    for path in [
            "tmp/",
            config.experiment_folder,
            config.experiment_folder + "logs/",
            config.experiment_folder + "episodes/"]:
        try:
            os.makedirs (path)
        except OSError:
            print ("Someone as already created path %s." % (path))

def create_experimental_run_files (config):
    """
    Create the files that are going to store the data produced by an experimental run.  The data is stored in CSV files.  The files are initialized with a header row.
    """
    with open (config.experiment_folder + "population.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        row = ["generation", "episode", "chromosome_genes"]
        f.writerow (row)
        fp.close ()
    with open (config.experiment_folder + "evaluation.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        row = ["generation", "episode", "iteration", "selected_arena", "active_casu", "value", "chromosome_genes"]
        f.writerow (row)
        fp.close ()

def run_evolutionary_strategy_algorithm (config, worker_zmqs):
    """
    Run the Evolutionary Strategy for the given configuration.
    """
    epsd = episode.Episode (config, worker_zmqs)
    epsd.initialise ()
    es = inspyred.ec.ES (random.Random ())
    evltr = evaluator.Evaluator (config, epsd)
    es.terminator = [inspyred.ec.terminators.generation_termination]
    es.variator = [chromosome.SinglePulseGenePause.get_variator ()]
    es.evolve (
        generator = chromosome.SinglePulseGenePause.random_generator,
        evaluator = evltr.population_evaluator,
        pop_size = config.population_size,
        bounder = chromosome.SinglePulseGenePause.get_bounder (),
        maximize = True,
        max_generations = config.number_generations)
    epsd.finish ()
    print ("Evolutionary Strategy algorithm finished!")

def check_run (config, args):
    run_number = args.run
    result = 'run-%03d/' % (run_number)
    if os.path.isdir (result):
        config.experiment_folder = result
    else:
        print "There is no run ", run_number

def load_population_and_evaluation (config):
    with open (config.experiment_folder + "population.csv", "r") as fp:
        f = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        f.next () #skip header_row
        rows = [row for row in f]
        initial_population = [row [evaluator.POP_CHROMOSOME_GENES:] for row in rows]
        print (initial_population)
        current_generation = int (rows [-1][evaluator.POP_GENERATION])
        current_episode = int (rows [-1][evaluator.POP_EPISODE])
        s = initial_population [-config.population_size:]
        seeds = [[int(c[0])] for c in s]
        fp.close ()
    with open (config.experiment_folder + "evaluation.csv", "r") as fp:
        f = csv.reader (fp, delimiter = ',', quoting = csv.QUOTE_NONNUMERIC, quotechar = '"')
        f.next () #skip header_row
        eva_values = []
        for row in f:
            if row [evaluator.EVA_GENERATION] == current_generation:
                eva_values.append (row [evaluator.EVA_VALUE])
        eva_values += [None] * (config.population_size * config.number_evaluations_per_chromosome - len (eva_values))
        fp.close ()
    return (current_generation, current_episode, seeds, eva_values)

def continue_evolutionary_strategy_algorithm (config, worker_zmqs, current_generation, episode_index, seeds, eva_values):
    """
    Run the Evolutionary Strategy for the given configuration.
    """
    epsd = episode.Episode (config, worker_zmqs, episode_index)
    epsd.initialise ()
    es = inspyred.ec.ES (random.Random ())
    evltr = evaluator.Evaluator (config, epsd, current_generation, eva_values)
    es.terminator = [inspyred.ec.terminators.generation_termination]
    es.variator = [chromosome.SinglePulseGenePause.get_variator ()]
    es.evolve (
        generator = chromosome.SinglePulseGenePause.random_generator,
        evaluator = evltr.population_evaluator,
        pop_size = config.population_size,
        bounder = chromosome.SinglePulseGenePause.get_bounder (),
        maximize = True,
        max_generations = config.number_generations,
        seeds = seeds)
    epsd.finish ()
    print ("Evolutionary Strategy algorithm finished!")

args = parse_arguments ()
if args.command in ['new-run', 'new_run']:
    cfg = config.Config ()
    cfg.status ()
    worker_zmqs = arena.connect_workers (arena.load_worker_settings (), cfg)
    calculate_experiment_folder_for_new_run (cfg, args)
    create_directories_for_experimental_run (cfg)
    create_experimental_run_files (cfg)
    run_evolutionary_strategy_algorithm (cfg, worker_zmqs)
elif args.command in ['continue-run', 'continue-run']:
    cfg = config.Config ()
    cfg.status ()
    check_run (cfg, args)
    current_generation, current_episode, seeds, eva_values = load_population_and_evaluation (cfg)
    worker_zmqs = arena.connect_workers (arena.load_worker_settings (), cfg)
    continue_evolutionary_strategy_algorithm (cfg, worker_zmqs, current_generation, current_episode + 1, seeds, eva_values)
elif args.command == None:
    print ("Nothing to do!\n")
else:
    print ("Unknown command: %s" % args.command)
