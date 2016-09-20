#!/usr/bin/env python
# -*- coding: utf-8 -*-

# chromosomes used in the incremental evolution work.
# Pedro Mariano
# Ziad Salem
# Payam Zahadat

#from assisipy import casu

import random
import time
import copy

BITRATE = 16

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
    STDDEV_PAUSE_PERIOD = 300

    VIBRATION_FREQUENCY = 440
    VIBRATION_PERIOD = 1000
    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, bocasu, evaluation_runtime):
        """
        Run the vibration model represented by the given SinglePulseGenePause chromosome.
        """
        pause_period = chromosome [0]
        if pause_period < casu.VIBE_PERIOD_MIN:
            vibe_periods = [SinglePulseGenePause.VIBRATION_PERIOD]
            vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY]
            vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY]
        else:
            vibe_periods = [SinglePulseGenePause.VIBRATION_PERIOD,    pause_period]
            vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY,            1]
            vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY,            0]
        bocasu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_runtime)
        bocasu.speaker_standby ()

    @staticmethod
    def run_vibration_model_v2 (chromosome, evaluation_runtime):
        import math
        import pyaudio #pyaudio is available via pip
        import wave
        data = ''
        freq = SinglePulseGenePause.VIBRATION_FREQUENCY  #Hz, Frequency
        v_length = SinglePulseGenePause.VIBRATION_PERIOD #Milliseconds of the active part of the vibration pattern
        p_length = chromosome [0]                        #Milliseconds of the pause phase of the vibration pattern
        t_length = evaluation_runtime                    #Seconds of the total length of the vibration pattern. Accuracy ~1Sec
        for i in xrange((int(float(t_length) / ((v_length + p_length) / 1000.0)))):
            for x in xrange(int(BITRATE * v_length)):
                data = data+chr(int(math.sin(x/(((1000 * BITRATE)/(freq))/(math.pi*2)))*127+ 128))
            for x in xrange(int(BITRATE * p_length)):
                data = data+chr(128)
        stream = pyaudio.PyAudio().open(format = pyaudio.PyAudio().get_format_from_width(1),
                                        channels = 1,
                                        rate = 1000 * BITRATE,
                                        output = True)
        stream.write(data)
        stream.stop_stream()
        stream.close()
        pyaudio.PyAudio().terminate()

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

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args):
            result = int (candidate [0] + random.gauss (0, SinglePulseGenePause.STDDEV_PAUSE_PERIOD))
            result = result - (result % SinglePulseGenePause.STEP_PAUSE_PERIOD)
            result =  max (SinglePulseGenePause.MIN_PAUSE_PERIOD - SinglePulseGenePause.STEP_PAUSE_PERIOD, min (result, SinglePulseGenePause.MAX_PAUSE_PERIOD))
            return [result, 0]
        return variator


def geometric_perturbation (random, success):
    result = 0
    while random.random () > success:
        result += 1
    if random.random () < 0.5:
        return result
    else:
        return -result


from assisipy import casu

class SinglePulseGenesPulse (AbstractChromosome):
    """
    This chromosome contains three genes that represent the pulse frequency, duration time and pause time.
    """
    MIN_FREQUENCY = 300
    MAX_FREQUENCY = 1500  # assisipy.casu.VIBE_FREQ_MAX
    STEP_FREQUENCY = 10
    SUCCESS_PERIOD = 1 / 60.0
    
    STEP_PERIOD = 10
    MIN_PERIOD = casu.VIBE_PERIOD_MIN
    MAX_PERIOD = 1000
    SUCCESS_FREQUENCY = 1.0 / 30

    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, bocasu, evaluation_runtime):
        """
        Run the vibration model represented by the given SinglePulseGenesPulse chromosome.
        """
        from assisipy import casu #?!
        frequency       = chromosome [0]
        duration_period = chromosome [1]
        pause_period    = chromosome [2]
        if pause_period < casu.VIBE_PERIOD_MIN:
            vibe_periods = [duration_period]
            vibe_freqs   = [frequency]
            vibe_amps    = [SinglePulseGenesPulse.VIBRATION_INTENSITY]
        else:
            vibe_periods = [duration_period,                           pause_period]
            vibe_freqs   = [frequency,                                            1]
            vibe_amps    = [SinglePulseGenesPulse.VIBRATION_INTENSITY,            0]
        bocasu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_runtime)
        bocasu.speaker_standby ()

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple SinglePulseGenesPulse chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        frequency       = random.randrange (SinglePulseGenesPulse.MIN_FREQUENCY, SinglePulseGenesPulse.MAX_FREQUENCY,  SinglePulseGenesPulse.STEP_FREQUENCY)
        duration_period = random.randrange (SinglePulseGenesPulse.MIN_PERIOD,    SinglePulseGenesPulse.MAX_PERIOD + 1, SinglePulseGenesPulse.STEP_PERIOD)
        pause_period    = random.randrange (SinglePulseGenesPulse.MIN_PERIOD,    SinglePulseGenesPulse.MAX_PERIOD + 1, SinglePulseGenesPulse.STEP_PERIOD)
        return [frequency, duration_period, pause_period]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args):
            result = copy.copy (candidate)
            gene_index = random.randrange (3)
            if gene_index == 0:
                new_gene = result [0] + SinglePulseGenesPulse.STEP_FREQUENCY * geometric_perturbation (random, SinglePulseGenesPulse.SUCCESS_FREQUENCY)
                result [0] = max (SinglePulseGenesPulse.MIN_FREQUENCY, min (new_gene, SinglePulseGenesPulse.MAX_FREQUENCY))
            elif gene_index == 1:
                new_gene = result [1] + SinglePulseGenesPulse.STEP_PERIOD * geometric_perturbation (random, SinglePulseGenesPulse.SUCCESS_PERIOD)
                result [1] = max (SinglePulseGenesPulse.MIN_PERIOD, min (new_gene, SinglePulseGenesPulse.MAX_PERIOD))
            else:
                new_gene = result [2] + SinglePulseGenesPulse.STEP_PERIOD * geometric_perturbation (random, SinglePulseGenesPulse.SUCCESS_PERIOD)
                result [2] = max (SinglePulseGenesPulse.MIN_PERIOD - SinglePulseGenesPulse.STEP_PERIOD, min (new_gene, SinglePulseGenesPulse.MAX_PERIOD))
            return result
        return variator

if __name__ == '__main__':
    pass
