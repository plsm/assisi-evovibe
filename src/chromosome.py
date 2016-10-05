#!/usr/bin/env python
# -*- coding: utf-8 -*-

# chromosomes used in the incremental evolution work.
# Pedro Mariano
# Ziad Salem
# Payam Zahadat

import assisipy.casu

import random
import time
import copy
import math

# vibration frequency domain
MIN_FREQUENCY = 300
MAX_FREQUENCY = 1500  # assisipy.casu.VIBE_FREQ_MAX
STEP_FREQUENCY = 10
STDDEV_FREQUENCY = (MAX_FREQUENCY - MIN_FREQUENCY) / 10.0
# only for geometric perturbation # SUCCESS_FREQUENCY = 1.0 / (((MAX_FREQUENCY - MIN_FREQUENCY) // STEP_FREQUENCY + 1) / 10 + 1.0)

# vibration period domain, pause period domain
MIN_PERIOD = 100  # assisipy.casu.VIBE_PERIOD_MIN
MAX_PERIOD = 1000
STEP_PERIOD = 10
STDDEV_PERIOD = 300 # (MAX_PERIOD - MIN_PERIOD) / 10.0
# only for geometric perturbation # SUCCESS_PERIOD = 1.0 / (((MAX_PERIOD - MIN_PERIOD) // STEP_PERIOD + 1) / 10 + 1.0)

# vibration intensity domain
MIN_INTENSITY = 5
STEP_INTENSITY = 5
MAX_INTENSITY = 50 # assisipy.casu.VIBE_AMP_MAX
STDDEV_INTENSITY = 10

BITRATE = 16

def geometric_perturbation (prng, current_value, min_value, max_value, step_value, success):
    change = 0
    while prng.random () >= success:
        change += step_value
    if prng.random () < 0.5:
        change = -change
    return ((current_value + change - min_value) % (max_value - min_value)) + min_value

def gaussian_perturbation (prng, current_value, min_value, max_value, step_value, stddev):
    change = prng.gauss (0, stddev)
    new_value = int (round (current_value + change))
    remainder = (new_value - min_value) % step_value
    new_value += -remainder + (step_value if 2 * remainder >= step_value > 1 else 0)
    new_value = (new_value - min_value) % (max_value - min_value + step_value) + min_value
    return new_value

class AbstractChromosome:
    """
    All chromosomes used by the incremental evolution algorithm must have the following set of static methods:
    run_vibration_model (chromosome, casu, evaluation_run_time)
    random_generator (random, args)
    """
    pass


class SinglePulseGenePause (AbstractChromosome):
    """
    This chromosome contains one gene that represents the pause time.  The vibration frequency is 440 Hz.  The vibration duration is 1 second.
    """
    VIBRATION_FREQUENCY = 440
    VIBRATION_PERIOD = 1000
    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, the_casu, evaluation_run_time):
        """
        Run the vibration model represented by the given SinglePulseGenePause chromosome.
        """
        pause_period = chromosome [0]
        if pause_period < assisipy.casu.VIBE_PERIOD_MIN:
            vibe_periods = [SinglePulseGenePause.VIBRATION_PERIOD]
            vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY]
            vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY]
        else:
            vibe_periods = [SinglePulseGenePause.VIBRATION_PERIOD,    pause_period]
            vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY,            1]
            vibe_amps    = [SinglePulseGenePause.VIBRATION_INTENSITY,            0]
        the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        the_casu.speaker_standby ()

    @staticmethod
    def run_vibration_model_v2 (chromosome, index, evaluation_run_time):
        import pyaudio # beagle bones do not need this
        data = ''
        freq = SinglePulseGenePause.VIBRATION_FREQUENCY  #Hz, Frequency
        v_length = SinglePulseGenePause.VIBRATION_PERIOD #Milliseconds of the active part of the vibration pattern
        p_length = chromosome [0] if chromosome [0] >= assisipy.casu.VIBE_PERIOD_MIN else 0 #Milliseconds of the pause phase of the vibration pattern
        t_length = evaluation_run_time                    #Seconds of the total length of the vibration pattern. Accuracy ~1Sec
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
        pause_period = random.randrange (MIN_PERIOD, MAX_PERIOD + 1, STEP_PERIOD)
        return [pause_period]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args = None):
            result = copy.copy (candidate)
            new_gene = gaussian_perturbation (random, candidate [0], MIN_PERIOD - STEP_PERIOD, MAX_PERIOD, STEP_PERIOD, STDDEV_PERIOD)
            result [0] = new_gene
            return result
        return variator


class SinglePulseGeneFrequency (AbstractChromosome):
    """
    This chromosome contains one gene that represents the vibration frequency.
    The vibration period is 1s.  The pause duration is 0.1 second.
    """

    VIBRATION_PERIOD = 900
    VIBRATION_INTENSITY = 50
    PAUSE_PERIOD = 100

    @staticmethod
    def run_vibration_model (chromosome, the_casu, evaluation_run_time):
        """
        Run the vibration model represented by the given SinglePulseGeneFrequency chromosome.
        """
        vibration_frequency = chromosome [0]
        vibe_periods = [SinglePulseGeneFrequency.VIBRATION_PERIOD,    SinglePulseGeneFrequency.PAUSE_PERIOD]
        vibe_freqs   = [vibration_frequency,                          1]
        vibe_amps    = [SinglePulseGeneFrequency.VIBRATION_INTENSITY, 0]
        the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        the_casu.speaker_standby ()

    @staticmethod
    def run_vibration_model_v2 (chromosome, index, evaluation_run_time):
        import pyaudio # beagle bones do not need this
        data = ''
        freq = chromosome [0]                                #Hz, Frequency
        v_length = SinglePulseGeneFrequency.VIBRATION_PERIOD #Milliseconds of the active part of the vibration pattern
        p_length = SinglePulseGeneFrequency.PAUSE_PERIOD     #Milliseconds of the pause phase of the vibration pattern
        t_length = evaluation_run_time                        #Seconds of the total length of the vibration pattern. Accuracy ~1Sec
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
        Return a random instance of a simple SinglePulseGeneFrequency chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        frequency = random.randrange (MIN_FREQUENCY, MAX_FREQUENCY + 1,  STEP_FREQUENCY)
        return [frequency]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args = None):
            result = copy.copy (candidate)
            new_gene = gaussian_perturbation (random, candidate [0], MIN_FREQUENCY, MAX_FREQUENCY, STEP_FREQUENCY, STDDEV_FREQUENCY)
            result [0] = new_gene
            return result
        return variator


class SinglePulseGenesPulse (AbstractChromosome):
    """
    This chromosome contains three genes that represent the pulse frequency, duration time and pause time.
    """
    VIBRATION_INTENSITY = 50

    @staticmethod
    def run_vibration_model (chromosome, the_casu, evaluation_run_time):
        """
        Run the vibration model represented by the given SinglePulseGenesPulse chromosome.
        """
        frequency       = chromosome [0]
        duration_period = chromosome [1]
        pause_period    = chromosome [2]
        intensity       = chromosome [3]
        if pause_period < assisipy.casu.VIBE_PERIOD_MIN:
            vibe_periods = [duration_period]
            vibe_freqs   = [frequency]
            vibe_amps    = [intensity]
        else:
            vibe_periods = [duration_period,  pause_period]
            vibe_freqs   = [frequency,        1]
            vibe_amps    = [intensity,        0]
        the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        the_casu.speaker_standby ()

    @staticmethod
    def run_vibration_model_v2 (chromosome, index, evaluation_run_time):
        import pyaudio # beagle bones do not need this
        data = ''
        freq = chromosome [0]         #Hz, Frequency
        v_length = chromosome [1]     #Milliseconds of the active part of the vibration pattern
        p_length = chromosome [2] if chromosome [2] >= assisipy.casu.VIBE_PERIOD_MIN else 0    #Milliseconds of the pause phase of the vibration pattern
        t_length = evaluation_run_time #Seconds of the total length of the vibration pattern. Accuracy ~1Sec
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
        Return a random instance of a simple SinglePulseGenesPulse chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        frequency       = random.randrange (MIN_FREQUENCY, MAX_FREQUENCY + 1,  STEP_FREQUENCY)
        duration_period = random.randrange (MIN_PERIOD,    MAX_PERIOD + 1,     STEP_PERIOD)
        pause_period    = random.randrange (MIN_PERIOD,    MAX_PERIOD + 1,     STEP_PERIOD)
        intensity       = random.randrange (MIN_INTENSITY, MAX_INTENSITY + 1,  STEP_INTENSITY)
        return [frequency, duration_period, pause_period, intensity]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args = None):
            result = copy.copy (candidate)
            gene_index = random.randrange (4)
            if gene_index == 0:
                new_gene = gaussian_perturbation (random, candidate [0], MIN_FREQUENCY, MAX_FREQUENCY, STEP_FREQUENCY, STDDEV_FREQUENCY)
                result [0] = new_gene
            elif gene_index == 1:
                new_gene = gaussian_perturbation (random, candidate [1], MIN_PERIOD, MAX_PERIOD, STEP_PERIOD, STDDEV_PERIOD)
                result [1] = new_gene
            elif gene_index == 2:
                new_gene = gaussian_perturbation (random, candidate [2], MIN_PERIOD - STEP_PERIOD, MAX_PERIOD, STEP_PERIOD, STDDEV_PERIOD)
                result [2] = new_gene
            elif gene_index == 3:
                new_gene = gaussian_perturbation (random, candidate [3], MIN_INTENSITY, MAX_INTENSITY, STEP_INTENSITY, STDDEV_INTENSITY)
                result [3] = new_gene
            return result
        return variator

class SinglePulse1sGenesFrequencyPause (AbstractChromosome):
    """
    This chromosome contains two genes that represent the pulse frequency, and pause time.  The pulse period is always 1s.
    """
    VIBRATION_AMPLITUDE = 50
    PULSE_PERIOD = 1000

    @staticmethod
    def run_vibration_model (chromosome, the_casu, evaluation_run_time):
        """
        Run the vibration model represented by the given SinglePulseGenesPulse chromosome.
        """
        frequency    = chromosome [0]
        pause_period = chromosome [1]
        vibration_period = SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - pause_period
        vibe_periods = [vibration_period,  pause_period]
        vibe_freqs   = [frequency,                    1]
        vibe_amps    = [SinglePulse1sGenesFrequencyPause.VIBRATION_AMPLITUDE,          0]
        print the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        the_casu.speaker_standby ()

    @staticmethod
    def run_vibration_model_v2 (chromosome, index, evaluation_run_time):
        import pyaudio # beagle bones do not need this
        data = ''
        freq = chromosome [0]         #Hz, Frequency
        v_length = SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - chromosome [1]     #Milliseconds of the active part of the vibration pattern
        p_length = chromosome [1]    #Milliseconds of the pause phase of the vibration pattern
        t_length = evaluation_run_time #Seconds of the total length of the vibration pattern. Accuracy ~1Sec
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
        Return a random instance of a simple SinglePulseGenesPulse chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        frequency       = random.randrange (MIN_FREQUENCY, MAX_FREQUENCY + 1,  STEP_FREQUENCY)
        pause_period    = random.randrange (MIN_PERIOD,    min (SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - MIN_PERIOD, MAX_PERIOD) + 1,     STEP_PERIOD)
        return [frequency, pause_period]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args = None):
            result = copy.copy (candidate)
            gene_index = random.randrange (2)
            if gene_index == 0:
                new_gene = gaussian_perturbation (random, candidate [0], MIN_FREQUENCY, MAX_FREQUENCY, STEP_FREQUENCY, STDDEV_FREQUENCY)
                result [0] = new_gene
            elif gene_index == 1:
                new_gene = gaussian_perturbation (random, candidate [1], MIN_PERIOD, min (SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - MIN_PERIOD, MAX_PERIOD), STEP_PERIOD, STDDEV_PERIOD)
                result [1] = new_gene
            return result
        return variator

class Method:
    def __init__ (self, class_name):
        self.run_vibration_model = {
            'Zagreb' : class_name.run_vibration_model    ,
            'Graz'   : class_name.run_vibration_model_v2 }
        self.variator = class_name.get_variator
        self.generator = class_name.random_generator

    def __str__ (self):
        return 'run: ' + str (self.run_vibration_model) + ' variator: ' + str (self.variator) + ' generator: ' + str (self.generator)
    # def __init__ (self, run_vibration_model, variator, generator):
    #     self.run_vibration_model = run_vibration_model
    #     self.variator = variator
    #     self.generator = generator

CHROMOSOME_METHODS = {
    'SinglePulseGenePause'             : Method (SinglePulseGenePause)     ,
    'SinglePulseGeneFrequency'         : Method (SinglePulseGeneFrequency) ,
    'SinglePulseGenesPulse'            : Method (SinglePulseGenesPulse)    ,
    'SinglePulse1sGenesFrequencyPause' : Method (SinglePulse1sGenesFrequencyPause)
    }

if __name__ == '__main__':
    pass
