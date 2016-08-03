#!/usr/bin/env python
# -*- coding: utf-8 -*-

# chromosomes used in the incremental evolution work.
# Pedro Mariano
# Ziad Salem
# Payam Zahadat

#from assisipy import casu

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
    MIN_PAUSE_PERIOD = 100 #assisipy.casu.VIBE_PERIOD_MIN
    MAX_PAUSE_PERIOD = 1000
    STEP_PAUSE_PERIOD = 10

    VIBRATION_FREQUENCY = 440
    VIBRATION_PERIOD = 1000
    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given SinglePulseGenePause chromosome.
        """
        pause_period = chromosome [0]
        vibe_periods = [SinglePulseGenePause.VIBRATION_PERIOD,    pause_period]
        vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY,            1]
        vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY,            0]
        casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_runtime)
        casu.speaker_standby ()

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple SinglePulseGenePause chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        pause_period = random.randrange (SinglePulseGenePause.MIN_PAUSE_PERIOD, SinglePulseGenePause.MAX_PAUSE_PERIOD + 1, SinglePulseGenePause.STEP_PAUSE_PERIOD)
        return [pause_period]


    @staticmethod
    def get_bounder ():
        from inspyred import ec
        r = range (SinglePulseGenePause.MIN_PAUSE_PERIOD, SinglePulseGenePause.MAX_PAUSE_PERIOD + 1, SinglePulseGenePause.STEP_PAUSE_PERIOD)
        return ec.DiscreteBounder (r)

if __name__ == '__main__':
    pass

