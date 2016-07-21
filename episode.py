import subprocess #spawn new processes
import os
import os.path

class Episode:
    """
    An episode represents a set of evaluations with a set of bees.

    This class is responsible for managing the initialisation and finish phase of episodes.  This class also manages the evaluation counter used in an episode.  The increment of this counter should be done at the beginning of an evaluation phase (see method evaluator.exp_step).

    In the initialisation phase the characteristics of the arena image have to be computed before bees are placed in the arena.  Then we ask the user to place the bees in the arena.  For documentation about the arena images, see module 'image'.

    In the finish phase we ask the user to remove the bees from the arena.  Files that were produced during an episode are moved to the experiment repository.

    This class can be used by the incremental evolution or by a parameter sweep.
    """

    def __init__ (self, config):
        self.config = config
        self.current_evaluation_in_episode = 0
        self.episode_index = 1
        self.record_process_flag = False

    def initialise (self):
        """
        In the initialisation phase of an episode we:

        * create the background image;

        * ask the user for the characteristics of the arena image;

        * ask the user to put bees in the arena;

        * start the episode video process
        """
        self.make_background_image ()
        self.image_properties ()
        raw_input ('\nPlace %d bees in the arena and press ENTER' % self.config.number_of_bees)
        #self.start_episode_video ()

    def increment_evaluation_counter (self):
        """
        Increment the evaluation counter.  If we have reached the end of an episode, we finish it and start a new episode.
        """
        if (self.current_evaluation_in_episode == self.config.number_of_evaluations_per_episode):
            print "\n\n* ** New Episode ** *"
            self.finish ()
            self.episode_index += 1
            self.init ()
            self.current_evaluation_in_episode = 0
        else:
            self.current_evaluation_in_episode += 1

    def finish (self, last_finish = False):
        """
        In the finish phase of an episode we:

        * terminate the episode recording process;

        * tell the user to remove the bees from the arena;

        * essential files that were produced during an episode are moved to the experiment repository;

        * unneeded files or files that can be recreated from the essential files are deleted.
        """
        if self.record_process_flag:
            self.recording_process.terminate ()
        print "Remove the bees from the arena"
        self.save_episode_files (last_finish)
        self.remove_episode_files (last_finish)
        
    def make_background_image (self):
        """
        Create the background video and image.

        These are used by the bee
        aggregation functions to compute how bees are stopped.  The
        background video and images are created at start of an experiment
        and everytime we change bees.  Whenever we change bees, we may
        disturb the arena.  The bee aggregation is sensitive to changes between the background image and evaluation images.
        """
        print "\n\n* ** Creating background image..."
        filename = self.config.experimentpath + 'Background.avi'
        bashCommand = 'gst-launch-0.10 --gst-plugin-path=/usr/local/lib/gstreamer-0.10/ --gst-plugin-load=libgstaravis-0.4.so -v aravissrc num-buffers=1 ' + \
                      '! video/x-raw-yuv,width=' + str (self.config.arena_image.width) + ',height=' + str (self.config.arena_image.height) + ',framerate=1/' + str (int (1.0 / self.config.frame_per_second)) + \
                      ' ! jpegenc ! avimux name=mux ! filesink location=' + filename    # with time - everytime generate a new file
        p = subprocess.Popen (bashCommand, shell = True, executable = '/bin/bash') #run the recording stream
        p.wait ()
        bashCommandSplit = "ffmpeg" + \
            " -i " + filename + \
            " -r 0.1" + \
            " -f image2 " + self.config.experimentpath + "Images/Background.jpg" #definition to extract the single image for background from the video
        p = subprocess.Popen (bashCommandSplit, shell = True, executable = '/bin/bash') #run the script of the extracting
        p.wait ()
        print ("background image is ready")

    def image_properties (self):
        """
        Ask the user the image properties.  This depend on the arena type that is being used.
        """
        self.config.arena_image.ask_image_properties ()
        imgpath = self.config.experimentpath + "Images/"
        self.config.arena_image.create_measure_area_image (imgpath)
        print "Created measured area image"
        
    def start_episode_video (self):
        """
        Create the child process that is going to record a video of an episode.

        We have to take into account how many evaluations are done by episode,
        and the duration of an evaluation.  The latter depends on the run time
        of a chromosome vibration model, on the spreading wait time, but also
        on the time it takes to process the data of one evaluation.  The latter
        may be relevant if data is stored in a disk with a low latency.

        TODO:
        Check time it takes to process the data of one evaluation
        """
        num_buffers = \
            self.config.number_of_evaluations_per_episode \
            * (self.config.evaluation_runtime + self.config.spreading_waitingtime) \
            * self.config.frame_per_second
        filename_real = self.config.experimentpath + 'episodeVideo_' + str (self.episode_index) + '.avi' #reaL video
        bashCommand_video = 'gst-launch-0.10' + \
          ' --gst-plugin-path=/usr/local/lib/gstreamer-0.10/' + \
          ' --gst-plugin-load=libgstaravis-0.4.so' + \
          ' -v aravissrc num-buffers=' + str (int (num_buffers)) + \
          ' ! video/x-raw-yuv,width=' + str (self.config.arena_image.width) + ',height=' + str (self.config.arena_image.height) + ',framerate=1/' + str (int (1.0 / self.config.frame_per_second)) + \
          ' ! jpegenc ! avimux name=mux ! filesink location=' + filename_real    # with time - everytime generate a new file
        self.recording_process = subprocess.Popen (bashCommand_video, shell=True, executable='/bin/bash')
        self.record_process_flag = True

    def save_episode_files (self, last_finish):
        """
        Save the background video and the iteration videos images created in a bee
        evaluation episode.
        """
        print "\n\nSaving episode files..."
        episode_path = self.config.repositorypath + "episode_" + str (self.episode_index) + "/"
        try:
            os.mkdir (episode_path)
        except:
            pass
        files_to_save = [
            'Background.avi',
            'Images/Measured-Area.jpg',
            'episodeVideo_' + str (self.episode_index) + '.avi']
        for filename in files_to_save:
            try:
                os.rename (
                    self.config.experimentpath + filename,
                    episode_path               + os.path.basename (filename))
            except OSError:
                print ("Not found: " + filename)
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for evaluation_index in xrange (1, self.config.number_of_evaluations_per_episode + 1):
            iterationvid_file = "iterationVideo_" + str (evaluation_index) + ".avi"
            try:
                os.rename (
                    self.config.experimentpath + iterationvid_file,
                    episode_path               + iterationvid_file)
            except OSError:
                print ("Not found: " + iterationvid_file)
        print "Episode files saved!"

    def remove_episode_files (self, last_finish):
        """
        Remove the files in the Images/ directory that were created in a bee evaluation episode.
        """
        print "\n\nDeleting episode files..."
        imgpath_incomplete_1 = self.config.experimentpath + "Images/iterationimage_"
        n = (int) (self.config.evaluation_runtime * self.config.frame_per_second)
        for evaluation_index in xrange (1, self.config.number_of_evaluations_per_episode + 1):
            imgpath_incomplete_2 = imgpath_incomplete_1 + str (evaluation_index) + "_"
            for i in xrange (1, n + 1):
                try:
                    os.remove (imgpath_incomplete_2 + "{:04d}.jpg".format (i))
                except OSError:
                    if not last_finish:
                        print ("Not found: " + imgpath_incomplete_2 + "{:04d}.jpg".format (i))
        print "Episode files deleted!"
