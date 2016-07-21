"""
Parameter sweep of the frequency using chromosome class GF_SCAI
"""

import experiment
import config
import episode
import evaluator
import chromosome
import incremental_evolution

import argparse

class AnES:
    def __init__ (self):
        self.num_generations = 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser (
        description = 'Incremental Evolution of vibration models to aggregate bees.',
        argument_default = None
    )
    parser.add_argument (
        '--config-file',
        default = 'config.txt',
        type = str,
        help = 'the file name with the experiment configuration')
    args = parser.parse_args ()
    print args
    cfg = config.Config (args.config_file)
    experiment.create_directories (cfg)
    epsd = episode.Episode (cfg)
    experiment.initialize_files (cfg)
    (active_casu, passive_casu) = experiment.connect_casu (cfg)
    counter = incremental_evolution.IncrementalEvolution.Counter ()
    evltr = evaluator.Evaluator (cfg, active_casu, passive_casu, counter, AnES (), epsd)
    evltr.run_vibration_model = chromosome.GF_SCAI.run_vibration_model
    population = [[300], [450], [500], [550], [600], [650], [700], [800]]
    epsd.initialise ()
    evltr.population_evaluator (population, None)
    epsd.finish ()
