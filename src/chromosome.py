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
    @staticmethod
    def run_vibration_model_Zagreb_SinglePulse (the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions, pulse):
        '''
        Run a vibration model that has a single pulse.  The CASU vibrates for
        vibration_run_time seconds followed by no_stimuli_run_time seconds
        where there is no stimuls from the CASUs.  This is repeated
        number_repetitions times.  Finally the CASU vibrates for vibration_run_time seconds.
        '''
        print 'running vibration model', vibration_run_time, no_stimuli_run_time, number_repetitions, pulse
        vibe_periods = [pulse.vibration_period,  pulse.pause_period]
        vibe_freqs   = [       pulse.frequency,                   1]
        vibe_amps    = [       pulse.amplitude,                   0]
        for _ in xrange (number_repetitions):
            the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
            time.sleep (vibration_run_time)
            the_casu.speaker_standby ()
            time.sleep (no_stimuli_run_time)
        print the_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (vibration_run_time)
        the_casu.speaker_standby ()

    @staticmethod
    def run_vibration_model_Graz_SinglePulse (chromosome, index, vibration_run_time, no_stimuli_run_time, number_repetitions, pulse):
        import pyaudio # beagle bones do not need this
        data = ''
        for i in xrange((int(float(vibration_run_time) / ((pulse.vibration_period + pulse.pause_period) / 1000.0)))):
            for x in xrange(int(BITRATE * pulse.vibration_period)):
                data = data+chr(int(math.sin(x/(((1000 * BITRATE)/(pulse.frequency))/(math.pi*2)))*127+ 128))
            for x in xrange(int(BITRATE * pulse.pause_period)):
                data = data+chr(128)
        stream = pyaudio.PyAudio().open(format = pyaudio.PyAudio().get_format_from_width(1),
                                        channels = 1,
                                        rate = 1000 * BITRATE,
                                        output = True)
        for _ in xrange (number_repetitions):
            stream.write (data)
            time.sleep (no_stimuli_run_time)
        stream.write(data)
        stream.stop_stream()
        stream.close()
        pyaudio.PyAudio().terminate()


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
            vibe_freqs   = [SinglePulseGenePause.VIBRATION_FREQUENCY,            0]
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

    @staticmethod
    def get_genes ():
        return [Gene (name = 'pause period',     unit = 'ms', min_value = MIN_PERIOD,    max_value = MAX_PERIOD,    step = STEP_PERIOD,    stddev = STDDEV_PERIOD)]


class SinglePulseGeneFrequency (AbstractChromosome):
    """
    This chromosome contains one gene that represents the vibration frequency.
    The vibration period is 1s.  The pause duration is 0.1 second.
    """

    VIBRATION_PERIOD = 900
    VIBRATION_INTENSITY = 50
    PAUSE_PERIOD = 100

    @staticmethod
    def run_vibration_model (chromosome, the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions):
        """
        Run the vibration model represented by the given SinglePulseGeneFrequency chromosome.
        """
        AbstractChromosome.run_vibration_model_Zagreb_SinglePulse (
            the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions,
            Pulse (
                frequency        = chromosome [0],
                pause_period     = SinglePulseGeneFrequency.PAUSE_PERIOD,
                vibration_period = SinglePulseGeneFrequency.VIBRATION_PERIOD,
                amplitude        = SinglePulseGeneFrequency.VIBRATION_INTENSITY))

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

    @staticmethod
    def get_genes ():
        return [Gene (name = 'frequency', unit = 'Hz', min_value = MIN_FREQUENCY, max_value = MAX_FREQUENCY, step = STEP_FREQUENCY, stddev = STDDEV_FREQUENCY)]


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

    @staticmethod
    def get_genes ():
        return [Gene (name = 'frequency',        unit = 'Hz', min_value = MIN_FREQUENCY, max_value = MAX_FREQUENCY, step = STEP_FREQUENCY, stddev = STDDEV_FREQUENCY),
                Gene (name = 'vibration period', unit = 'ms', min_value = MIN_PERIOD,    max_value = MAX_PERIOD,    step = STEP_PERIOD,    stddev = STDDEV_PERIOD),
                Gene (name = 'pause period',     unit = 'ms', min_value = MIN_PERIOD,    max_value = MAX_PERIOD,    step = STEP_PERIOD,    stddev = STDDEV_PERIOD),
                Gene (name = 'amplitude',        unit = '%',  min_value = MIN_INTENSITY, max_value = MAX_INTENSITY, step = STEP_INTENSITY, stddev = STDDEV_INTENSITY)]

class SinglePulse1sGenesFrequencyPause (AbstractChromosome):
    """
    This chromosome contains two genes that represent the pulse frequency, and pause time.  The pulse period is always 1s.
    """
    VIBRATION_AMPLITUDE = 50
    PULSE_PERIOD = 1000

    @staticmethod
    def run_vibration_model (chromosome, the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions):
        """
        Run the vibration model represented by the given SinglePulseGenesPulse chromosome.
        """
        AbstractChromosome.run_vibration_model_Zagreb_SinglePulse (
            the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions,
            Pulse (
                frequency        = chromosome [0],
                pause_period     = chromosome [1],
                vibration_period = SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - chromosome [1],
                amplitude        = SinglePulse1sGenesFrequencyPause.VIBRATION_AMPLITUDE))

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
        pause_period    = random.randrange (MIN_PERIOD,    SinglePulse1sGenesFrequencyPause.max_period () + 1,     STEP_PERIOD)
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
                new_gene = gaussian_perturbation (random, candidate [1], MIN_PERIOD, SinglePulse1sGenesFrequencyPause.max_period (), STEP_PERIOD, STDDEV_PERIOD)
                result [1] = new_gene
            return result
        return variator

    @staticmethod
    def get_genes ():
        return [Gene (name = 'frequency',    unit = 'Hz', min_value = MIN_FREQUENCY, max_value = MAX_FREQUENCY, step = STEP_FREQUENCY, stddev = STDDEV_FREQUENCY),
                Gene (name = 'pause period', unit = 'ms', min_value = MIN_PERIOD,    max_value = SinglePulse1sGenesPulse.max_period (), step = STEP_PERIOD, stddev = STDDEV_PERIOD)]

    @staticmethod
    def max_period ():
        return max (MIN_PERIOD, min (SinglePulse1sGenesFrequencyPause.PULSE_PERIOD - MIN_PERIOD, MAX_PERIOD))

class SinglePulse1sGenesPulse (AbstractChromosome):
    """
    This chromosome contains the gene that control a vibration pulse with 1
    second of duration.  The genes are the frequency, pause period and
    amplitude.
    """
    PULSE_PERIOD = 1000

    @staticmethod
    def run_vibration_model (chromosome, the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions):
        """
        Run the vibration model represented by the given SinglePulseGenesPulse chromosome.
        """
        AbstractChromosome.run_vibration_model_Zagreb_SinglePulse (
            the_casu, vibration_run_time, no_stimuli_run_time, number_repetitions,
            Pulse (
                frequency        = chromosome [0],
                pause_period     = chromosome [1],
                vibration_period = SinglePulse1sGenesPulse.PULSE_PERIOD - chromosome [1],
                amplitude        = chromosome [2]))

    @staticmethod
    def run_vibration_model_v2 (chromosome, index, evaluation_run_time):
        pass

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple SinglePulseGenesPulse chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        frequency    = random.randrange (MIN_FREQUENCY , MAX_FREQUENCY + 1                         , STEP_FREQUENCY)
        pause_period = random.randrange (MIN_PERIOD    , SinglePulse1sGenesPulse.max_period () + 1 , STEP_PERIOD)
        amplitude    = random.randrange (MIN_INTENSITY , MAX_INTENSITY                             , STEP_INTENSITY)
        return [frequency, pause_period, amplitude]

    @staticmethod
    def get_variator ():
        import inspyred
        @inspyred.ec.variators.mutator
        def variator (random, candidate, args = None):
            result = copy.copy (candidate)
            gene_index = random.randrange (3)
            if gene_index == 0:
                new_gene = gaussian_perturbation (random, candidate [0], MIN_FREQUENCY, MAX_FREQUENCY, STEP_FREQUENCY, STDDEV_FREQUENCY)
                result [0] = new_gene
            elif gene_index == 1:
                new_gene = gaussian_perturbation (random, candidate [1], MIN_PERIOD, SinglePulse1sGenesPulse.max_period (), STEP_PERIOD, STDDEV_PERIOD)
                result [1] = new_gene
            elif gene_index == 2:
                new_gene = gaussian_perturbation (random, candidate [2], MIN_INTENSITY, MAX_INTENSITY, STEP_INTENSITY, STDDEV_INTENSITY)
                result [2] = new_gene
            return result
        return variator

    @staticmethod
    def get_genes ():
        return [Gene (name = 'frequency',    unit = 'Hz', min_value = MIN_FREQUENCY, max_value = MAX_FREQUENCY, step = STEP_FREQUENCY, stddev = STDDEV_FREQUENCY),
                Gene (name = 'pause period', unit = 'ms', min_value = MIN_PERIOD,    max_value = SinglePulse1sGenesPulse.max_period (), step = STEP_PERIOD, stddev = STDDEV_PERIOD),
                Gene (name = 'amplitude',    unit = '%',  min_value = MIN_INTENSITY, max_value = MAX_INTENSITY, step = STEP_INTENSITY, stddev = STDDEV_INTENSITY)]

    @staticmethod
    def max_period ():
        return max (MIN_PERIOD, min (SinglePulse1sGenesPulse.PULSE_PERIOD - MIN_PERIOD, MAX_PERIOD))

class Method:
    def __init__ (self, class_name):
        self.run_vibration_model = {
            'Zagreb' : class_name.run_vibration_model    ,
            'Graz'   : class_name.run_vibration_model_v2 }
        self.variator = class_name.get_variator
        self.generator = class_name.random_generator
        self.get_genes = class_name.get_genes

    def __str__ (self):
        return 'run: ' + str (self.run_vibration_model) + ' variator: ' + str (self.variator) + ' generator: ' + str (self.generator)

CHROMOSOME_METHODS = {
    'SinglePulseGenePause'             : Method (SinglePulseGenePause)     ,
    'SinglePulseGeneFrequency'         : Method (SinglePulseGeneFrequency) ,
    'SinglePulseGenesPulse'            : Method (SinglePulseGenesPulse)    ,
    'SinglePulse1sGenesFrequencyPause' : Method (SinglePulse1sGenesFrequencyPause) ,
    'SinglePulse1sGenesPulse'          : Method (SinglePulse1sGenesPulse)
    }

class Pulse:
    def __init__ (self, frequency, amplitude, vibration_period, pause_period):
        self.frequency = frequency
        self.amplitude = amplitude
        self.vibration_period = vibration_period
        self.pause_period = pause_period

    def __str__ (self):
        return '%dHz %d%% %dms %dms' % (self.frequency, self.amplitude, self.vibration_period, self.pause_period)
    

class Gene:
    '''
    Describes a gene in a chromosome.
    '''
    def __init__ (self, name, unit, min_value, max_value, step, stddev):
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.stddev = stddev

if __name__ == '__main__':
    pass
