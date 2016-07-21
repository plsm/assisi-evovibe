#!/usr/bin/env python
# -*- coding: utf-8 -*-

# chromosomes used in the incremental evolution work.
# Pedro Mariano
# Ziad Salem
# Payam Zahadat

from assisipy import casu

from inspyred import ec

import random
import time

class AbstractChromosome:
    """
    All chromosomes used by the incremental evolution algorithm must have the following set of static methods:
    run_vibration_model (chromosome, casu, evaluation_runtime)
    random_generator (random, args)
    """
    pass


class SinglePulseGenePause (AbstractChromosome):
    """
    This chromosome contains one gene that represents the pause time.  The vibration frequency is 440 Hz.  The vibration duration is 1 second.
    """
    MIN_TIME = 0.0
    MAX_TIME = 1.0

    VIBRATION_FREQUENCY = 440
    VIBRATION_TIME = 1.0
    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given SinglePulseGenePause chromosome.
        """
        pause_time = chromosome [0]
        vibe_periods = [SinglePulseGenePause.VIBRATION_TIME,       pause_time]
        vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY,  0]
        vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY,  0]
        casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_runtime)
        casu.speaker_standby ()

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple SinglePulseGenePause chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        pause_time = random.uniform (SinglePulseGenePause.MIN_TIME, SinglePulseGenePause.MAX_TIME)
        return [pause_time]

    bounder = ec.Bounder (MIN_TIME, MAX_TIME)

if __name__ == '__main__':
    pass

vibration_models = {}
vibration_models ['single_pulse_gene_pause'] = (SinglePulseGenePause.random_generator, SinglePulseGenePause.bounder, SinglePulseGenePause.run_vibration_model)

