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
    return parser.parse_args ()


def calculate_experiment_folder_for_new_run (config):
    """
    Compute the experiment folder for a new experimental run.  This folder is where all the files generated by an experimental run are stored.
    """
    run_number = 1
    while True:
        result = 'run-%03d/' % (run_number)
        if not os.path.isdir (result) and not os.path.exists (result):
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
        row = ["generation", "episode", "selected_arena", "active_casu", "value", "chromosome_genes"]
        f.writerow (row)
        fp.close ()

def run_evolutionary_strategy_algorithm (config, worker_zmqs):
    """
    Run the Evolutionary Strategy for the given configuration.
    """
    epsd = episode.Episode (config, worker_zmqs)
    epsd.initialise ()
    es = inspyred.ec.ES (random.Random ())
    evltr = evaluator.Evaluator (config, es, epsd)
    es.evolve (
        generator = chromosome.SinglePulseGenePause.random_generator,
        evaluator = evltr.population_evaluator,
        pop_size = config.population_size,
        bounder = chromosome.SinglePulseGenePause.get_bounder (),
        maximize = True,
        max_generations = config.number_generations)
    epsd.finish ()
    print ("Evolutionary Strategy algorithm finished!")

args = parse_arguments ()
if args.command in ['new-run', 'new_run']:
    cfg = config.Config ()
    cfg.status ()
    worker_zmqs = arena.connect_workers (arena.load_worker_settings (), cfg)
    calculate_experiment_folder_for_new_run (cfg)
    create_directories_for_experimental_run (cfg)
    create_experimental_run_files (cfg)
    run_evolutionary_strategy_algorithm (cfg, worker_zmqs)
elif args.command == None:
    print ("Nothing to do!\n")
else:
    print ("Unknown command: %s" % args.command)
