import chromosome
import experiment
import config
import evaluator
import episode
import incremental_evolution

import sys


class AnES:
    def __init__ (self):
        self.num_generations = 0

config_filename = sys.argv [1]
cfg = config.Config (config_filename)
experiment.create_directories (cfg)
experiment.connect_casu (cfg)
epsd = episode.Episode (cfg)
experiment.initialize_files (cfg)
counter = incremental_evolution.IncrementalEvolution.Counter ()
eva = evaluator.Evaluator (cfg, counter, AnES (), epsd)
eva.run_vibration_model = chromosome.GP_F440.run_vibration_model
population = [[0.1]]
epsd.initialise ()
pop_fits = eva.population_evaluator (population, None)
epsd.finish ()
print pop_fits

