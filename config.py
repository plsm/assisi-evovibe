import image

import yaml

class Config:
    """
    Configuration setup of an incremental evolutionary algorithm setup.
    """

    BEE_WORKDAY_LENGTH = 30 * 60
    """
    Length of bees workday length in seconds.  After this time has elapsed, bees have to go home to rest and get fed.
    """

    def __init__ (self, filename):
        file_object = open (filename, 'r')
        dictionary = yaml.load (file_object)
        file_object.close ()
        #DEBUG print dictionary
        try:
            self.number_of_bees                            = dictionary ['number_of_bees']
            """Number of bess in a chromosome evaluation"""
            self.generations_with_chromosome_frequency     = dictionary ['generations'] ['chromosome_frequency']
            self.generations_with_chromosome_freq_inten    = dictionary ['generations'] ['chromosome_freq_inten']
            self.generations_with_chromosome_nature_draft  = dictionary ['generations'] ['chromosome_nature_draft']
            self.generations_with_chromosome_frequency_with_vibration_pause = dictionary ['generations']['chromosome_frequency_with_vibration_pause']
            self.generations_GP_F450 = dictionary ['generations']['pause_freq_450']
            self.generations_GP_F440 = dictionary ['generations']['pause_freq_440']
            self.number_of_evaluations_per_episode         = dictionary ['number_of_evaluations_per_episode']
            """The number of iterations in one episode of experiment  (then change the bees)"""
            self.evaluation_runtime                        = dictionary ['evaluation_runtime']
            """The runtime of a single iteration / chromosome evaluation (in sec) (vibration)"""
            self.spreading_waitingtime                     = dictionary ['spreading_waitingtime']
            """Time (in sec) for the bees to spread after vibration (no vibration)"""
            self.population_size                           = dictionary ['population_size']
            self.number_evaluations_per_chromosome         = dictionary ['number_evaluations_per_chromosome']
            """How many experimental runs are made per chromosome evaluation"""
            self.active_casu_rtc_file_name                 = dictionary ['active_casu_rtc_file_name']
            self.passive_casu_rtc_file_name                = dictionary ['passive_casu_rtc_file_name']
            self.stopped_threshold                         = dictionary ['stopped_threshold']
            self.aggregation_minDuration_thresh            = dictionary ['aggregation_minDuration_thresh']
            self.fitness_function                          = dictionary ['fitness_function']
            self.arena_type                                = dictionary ['arena']
            self.constant_airflow                          = dictionary ['constant_airflow']
        except KeyError as e:
            print 'The configuration file does not have parameter ' + str (e)
            print
            raise
        self.num_generations = self.generations_with_chromosome_frequency + \
            self.generations_with_chromosome_freq_inten + \
            self.generations_with_chromosome_nature_draft
        self.aggregation_threhsoldN = 55 # Threshold for the number of bees aggregated around the vibrating CASU

        if self.arena_type == 'stadium':
            self.arena_image = image.StadiumArenaImage ()
        elif self.arena_type == 'circular':
            self.arena_image = image.CircularArenaImage ()

        self.image_width = 600
        self.image_height = 600
        self.frame_per_second = 1        # 1 frame per sec    #  1/10.0 #1 frame per 10 sec
        experimentstamp  = str (input ('\nPlease enter the run number: '))
        self.experimentpath = "./experiment_logs/learningexperiment_" + experimentstamp + "/" #the name of the folder that we will save data in
        self.repositorypath = "./experiment_repository/learningexperiment_" + experimentstamp + "/"

    def status (self):
        """
        Do a diagnosis of this experimental configuration.
        """
        print "\n\n\n* ** Configuration Status ** *"
        bwl = self.number_of_evaluations_per_episode * (self.evaluation_runtime + self.spreading_waitingtime)
        print "Bees are going to work %d:%d" % (bwl / 60, bwl % 60),
        if bwl > Config.BEE_WORKDAY_LENGTH:
            print ", which is %d%% more than their workday length" % (int ((bwl - Config.BEE_WORKDAY_LENGTH) * 100.0 / Config.BEE_WORKDAY_LENGTH))
        else:
            print ", which is below their workday length"
        if self.number_of_evaluations_per_episode % self.number_evaluations_per_chromosome == 0:
            print "When a chromosome is being evaluated, no bee change will occur.  Maybe you are assuming that there are changes from one bee set to another"
        else:
            print "When a chromosome is being evaluated, bee changes WILL occur.  You are assuming that all bee sets are equal."
        print "Configuration file read:"
        print self
        raw_input ('Press ENTER to continue')

    def __str__ (self):
        return """number_of_bees : %d
generations:
     chromosome_frequency: %d
     chromosome_freq_inten: %d
     chromosome_nature_draft: %d
     chromosome_frequency_with_vibration_pause: %d
     pause_freq_450: %d
     pause_freq_440: %d
number_of_evaluations_per_episode: %d
evaluation_runtime: %d
spreading_waitingtime: %d
idle_time: %d
population_size: %d
number_evaluations_per_chromosome: %d
active_casu_rtc_file_name : %s
passive_casu_rtc_file_name : %s
stopped_threshold : %d
aggregation_minDuration_thresh : %d
fitness_function : %s
constant_airflow : %s
""" % (self.number_of_bees,
       self.generations_with_chromosome_frequency,
       self.generations_with_chromosome_freq_inten,
       self.generations_with_chromosome_nature_draft,
       self.generations_with_chromosome_frequency_with_vibration_pause,
       self.generations_GP_F450,
       self.generations_GP_F440,
       self.number_of_evaluations_per_episode,
       self.evaluation_runtime,
       self.spreading_waitingtime,
       self.idle_time,
       self.population_size,
       self.number_evaluations_per_chromosome,
       self.active_casu_rtc_file_name,
       self.passive_casu_rtc_file_name,
       self.stopped_threshold,
       self.aggregation_minDuration_thresh,
       self.fitness_function,
       self.arena_type,
       self.constant_airflow)

if __name__ == '__main__':
    print "Debugging config.py"
    c = Config ('config.test')
    print c
