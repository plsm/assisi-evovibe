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

class GF_SCAI (AbstractChromosome):
    """
    This chromosome contains a single gene that represents the vibration frequency.  The vibration intensity is determined by a static class attribute.
    """
    MIN_FREQUENCY = 50
    MAX_FREQUENCY = 800
    RESOLUTION_FREQUENCY = 100
    INTENSITY = 100
    pausetimeA = 0.1
    vibtimeA = 0.9

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given chromosome.
        """
        frequency = chromosome [0]
        print ("vibration starts.....")
        zero_time = time.time ()
        while time.time () - zero_time < evaluation_runtime:
            casu.set_speaker_vibration (freq = frequency, intens = GF_SCAI.INTENSITY)
            time.sleep (GF_SCAI.vibtimeA)
            casu.speaker_standby ()
            time.sleep (GF_SCAI.pausetimeA)
        print ("vibration stops")

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        print "random_generator (%s, %s)" % (str (random), str (args))
        frequency = random.randrange (GF_SCAI.MIN_FREQUENCY, GF_SCAI.MAX_FREQUENCY, GF_SCAI.RESOLUTION_FREQUENCY)
        return [frequency]

    @staticmethod
    def bound_frequency (value):
        r = int (value - GF_SCAI.MIN_FREQUENCY) % GF_SCAI.RESOLUTION_FREQUENCY
        if r > GF_SCAI.RESOLUTION_FREQUENCY / 2:
            value += GF_SCAI.RESOLUTION_FREQUENCY - r
        else:
            value -= r
        return max (GF_SCAI.MIN_FREQUENCY, min (value, GF_SCAI.MAX_FREQUENCY))

    class Bounder:
        def __call__ (self, candidate, args):
            return [GF_SCAI.bound_frequency (candidate [0])]

class GFPD_SCAI (AbstractChromosome):
    """
    This chromosome contains three genes that represents the vibration frequency, the vibration time and the pause time.  The vibration intensity is determined by a static class attribute.
    """
    MIN_TIME = 0.05
    MAX_TIME = 1.0

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given chromosome.
        """
        frequency = chromosome [0]
        vibration_time = chromosome [1]
        pause_time = chromosome [2]
        print ("vibration starts.....")
        zero_time = time.time ()
        while time.time () - zero_time < evaluation_runtime:
            casu.set_speaker_vibration (freq = frequency, intens = GF_SCAI.INTENSITY)
            time.sleep (vibration_time)
            casu.speaker_standby ()
            time.sleep (pause_time)
        print ("vibration stops")

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        print "random_generator (%s, %s)" % (str (random), str (args))
        frequency = random.randrange (GF_SCAI.MIN_FREQUENCY, GF_SCAI.MAX_FREQUENCY, GF_SCAI.RESOLUTION_FREQUENCY)
        vibration_time = random.uniform (GFPD_SCAI.MIN_TIME, GFPD_SCAI.MAX_TIME)
        pause_time = random.uniform (GFPD_SCAI.MIN_TIME, GFPD_SCAI.MAX_TIME)
        return [frequency, vibration_time, pause_time]

    class Bounder:
        def __init__ (self):
            self.lower_bound = [GF_SCAI.MIN_FREQUENCY, GFPD_SCAI.MIN_TIME, GFPD_SCAI.MIN_TIME]
            self.upper_bound = [GF_SCAI.MAX_FREQUENCY, GFPD_SCAI.MAX_TIME, GFPD_SCAI.MAX_TIME]

        def __call__ (self, candidate, args):
            return [
                GF_SCAI.bound_frequency (candidate [0]).
                max (GFPD_SCAI.MIN_TIME, min (candidate [1], GFPD_SCAI.MAX_TIME)),
                max (GFPD_SCAI.MIN_TIME, min (candidate [2], GFPD_SCAI.MAX_TIME)),
            ]


class GP_F450 (AbstractChromosome):
    """
    This chromosome contains one gene that represents the pause time.  The vibration frequency is 450.
    """
    MIN_TIME = 0.0
    MAX_TIME = 1.0

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given GP_F450 chromosome.
        """
        frequency = 450
        vibration_time = 1
        pause_time = chromosome [0]
        print ("vibration starts.....")
        zero_time = time.time ()
        while time.time () - zero_time < evaluation_runtime:
            casu.set_speaker_vibration (freq = frequency, intens = GF_SCAI.INTENSITY)
            time.sleep (vibration_time)
            if pause_time > 0:
                casu.speaker_standby ()
                time.sleep (pause_time)
        print ("vibration stops")

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple GP_F450 chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        pause_time = random.uniform (GP_F450 .MIN_TIME, GP_F450 .MAX_TIME)
        return [pause_time]

    bounder = ec.Bounder (MIN_TIME, MAX_TIME)


class GP_F440 (AbstractChromosome):
    """
    This chromosome contains one gene that represents the pause time.  The vibration frequency is 440.
    """
    MIN_TIME = 0.0
    MAX_TIME = 1.0

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given GP_F450 chromosome.
        """
        frequency = 440
        vibration_time = 1
        pause_time = chromosome [0]
        print ("vibration starts.....")
        zero_time = time.time ()
        while time.time () - zero_time < evaluation_runtime:
            casu.set_speaker_vibration (freq = frequency, intens = GF_SCAI.INTENSITY)
            time.sleep (vibration_time)
            if pause_time > 0:
                casu.speaker_standby ()
                time.sleep (pause_time)
        print ("vibration stops")

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple GP_F450 chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        pause_time = random.uniform (GP_F450 .MIN_TIME, GP_F450 .MAX_TIME)
        return [pause_time]

    bounder = ec.Bounder (MIN_TIME, MAX_TIME)






class GFI (AbstractChromosome):
    """
    This chromosome contains two genes that represent the vibration frequency and the frequency amplitude.
    This class augments class GF_SAI
    """
    MIN_INTENSITY = 1
    MAX_INTENSITY = 100

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        """
        Run the vibration model represented by the given chromosome.
        """
        frequency = chromosome [0]
        intensity = chromosome [1]
        print ("vibration starts.....")
        casu.set_speaker_vibration (freq = frequency, intens = intensity)
        time.sleep (evaluation_runtime)
        casu.speaker_standby ()
        print ("vibration stops")

    @staticmethod
    def random_generator (random, args = None):
        """
        Return a random instance of a simple chromosome.
        This method is used as a generator by the evolutionary algorithm.
        """
        print "random_generator (%s, %s)" % (str (random), str (args))
        frequency = random.randrange (GF_SCAI.MIN_FREQUENCY, GF_SCAI.MAX_FREQUENCY, GF_SCAI.RESOLUTION_FREQUENCY)
        intensity = random.uniform (GFI.MIN_INTENSITY, GFI.MAX_INTENSITY)
        return [frequency, intensity]

    @staticmethod
    def promote_GF_SCAI (chromosome):
        intensity = random.uniform (GFI.MIN_INTENSITY, GFI.MAX_INTENSITY)
        return [chromosome [0], intensity]

    @staticmethod
    def bound_intensity (value):
        return max (GFI.MIN_INTENSITY, min (value, GFI.MAX_INTENSITY))

    class Bounder:
        """Bounder used by the evolutionary algorithm to mutate chromosomes"""
        def __call__ (self, candidate, args):
            return [GF_SCAI.bound_frequency (candidate [0]), GFI.bound_intensity (candidate)]
        
class NatureDraftChromosome (AbstractChromosome):
    """
    """
    MIN_DELTA_FREQUENCY = -5
    MAX_DELTA_FREQUENCY = 5
    MIN_DELTA_INTENSITY = -5
    MAX_DELTA_INTENSITY = 5
    MIN_NUMBER_PULSES = 1
    MAX_NUMBER_PULSES = 10
    MIN_DURATION_PULSES = 1
    MAX_DURATION_PULSES = 2
    MIN_DURATION_PAUSES = 0
    MAX_DURATION_PAUSES = 2

    bounder = ec.Bounder (
        lower_bound = [GF_SCAI.MIN_FREQUENCY, MIN_DELTA_FREQUENCY, GFI.MIN_INTENSITY, MIN_DELTA_INTENSITY, MIN_NUMBER_PULSES, MIN_DURATION_PULSES, MIN_DURATION_PAUSES],
        upper_bound = [GF_SCAI.MAX_FREQUENCY, MAX_DELTA_FREQUENCY, GFI.MAX_INTENSITY, MAX_DELTA_INTENSITY, MAX_NUMBER_PULSES, MAX_DURATION_PULSES, MAX_DURATION_PAUSES])

    @staticmethod
    def promote_GFI (individual):
        frequency_first_pulse = individual [0]
        delta_frequency       = random.uniform (NatureDraftChromosome.MIN_DELTA_FREQUENCY, NatureDraftChromosome.MAX_DELTA_FREQUENCY)
        intensity_first_pulse = individual [1]
        delta_intensity       = random.uniform (NatureDraftChromosome.MIN_DELTA_INTENSITY, NatureDraftChromosome.MAX_DELTA_INTENSITY)
        number_pulses    = int (random.uniform (NatureDraftChromosome.MIN_NUMBER_PULSES,   NatureDraftChromosome.MAX_NUMBER_PULSES))
        duration_pulses       = random.uniform (NatureDraftChromosome.MIN_DURATION_PULSES, NatureDraftChromosome.MAX_DURATION_PULSES)
        duration_pauses       = random.uniform (NatureDraftChromosome.MIN_DURATION_PAUSES, NatureDraftChromosome.MAX_DURATION_PAUSES)
        return [frequency_first_pulse, delta_frequency, intensity_first_pulse, delta_intensity, number_pulses, duration_pulses, duration_pauses]

    @staticmethod
    def random_generator (random, args = None):
        frequency_first_pulse = random.uniform (GF_SCAI.MIN_FREQUENCY,            GF_SCAI.MAX_FREQUENCY)
        delta_frequency       = random.uniform (NatureDraftChromosome.MIN_DELTA_FREQUENCY, NatureDraftChromosome.MAX_DELTA_FREQUENCY)
        intensity_first_pulse = random.uniform (GFI.MIN_INTENSITY,            GFI.MAX_INTENSITY)
        delta_intensity       = random.uniform (NatureDraftChromosome.MIN_DELTA_INTENSITY, NatureDraftChromosome.MAX_DELTA_INTENSITY)
        number_pulses    = int (random.uniform (NatureDraftChromosome.MIN_NUMBER_PULSES,   NatureDraftChromosome.MAX_NUMBER_PULSES))
        duration_pulses       = random.uniform (NatureDraftChromosome.MIN_DURATION_PULSES, NatureDraftChromosome.MAX_DURATION_PULSES)
        duration_pauses       = random.uniform (NatureDraftChromosome.MIN_DURATION_PAUSES, NatureDraftChromosome.MAX_DURATION_PAUSES)
        return [frequency_first_pulse, delta_frequency, intensity_first_pulse, delta_intensity, number_pulses, duration_pulses, duration_pauses]

    @staticmethod
    def run_vibration_model (chromosome, casu, evaluation_runtime):
        frequency_first_pulse = chromosome [0]
        delta_frequency       = chromosome [1]
        intensity_first_pulse = chromosome [2]
        delta_intensity       = chromosome [3]
        number_pulses         = chromosome [4]
        duration_pulses       = chromosome [5]
        duration_pauses       = chromosome [6]
        print ("vibration starts.....")
        zero_time = time.time ()
        frequency = frequency_first_pulse
        intensity = intensity_first_pulse
        state = 0
        while time.time () - zero_time < evaluation_runtime:
            casu.set_speaker_vibration (freq = frequency, intens = intensity)
            time.sleep (duration_pulses)
            casu.speaker_standby ()
            time.sleep (duration_pauses)
            state += 1
            if state == number_pulses:
                frequency = frequency_first_pulse
                intensity = intensity_first_pulse
            else:
                frequency += delta_frequency
                intensity += delta_intensity
        print ("vibration stops")

if __name__ == '__main__':
    prng = random.Random ()
    sc = GF_SCAI.random_generator (prng)
    print sc
    print GF_SCAI.Bounder ().__call__ (sc, None)
    ndc = NatureDraftChromosome.random_generator (prng)
    print ndc
