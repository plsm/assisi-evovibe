from assisipy import casu

import os
import csv

def create_directories (config):
    """
    Create the directories for the given experimental run.
    """
    warning = False
    for path in ["logs/", config.experimentpath, config.repositorypath, config.experimentpath + "populations/", config.experimentpath + "Images/"]:
        try:
            os.makedirs (path)
        except:
            print ("Folder '" + path + "' already exists!  If there are any files from a previous experiment they may be overwritten!")
            warning = True
    if warning:
        raw_input ("Press ENTER if you are sure about the run number. Otherwise press CONTROL-C")

def initialize_files (config):
    with open (config.experimentpath + "populations/pop.csv", 'w') as fp:
        f = csv.writer (fp, delimiter = ',', quoting = csv.QUOTE_NONE, quotechar = '"')
        row = ["generation", "chromosome_genes", "evaluation_values"]
        f.writerow (row)
        fp.close ()

def connect_casu (config):
    """
    Create the CASU instances that are going to be used by the chromosome evaluation functions.
    Initialise the CASUs so that we can create the background image.
    """
    active_casu = casu.Casu (
        rtc_file_name = config.active_casu_rtc_file_name,
        log = True,
        log_folder = "logs")
    passive_casu = casu.Casu (
        rtc_file_name = config.passive_casu_rtc_file_name,
        log = True,
        log_folder = "logs")
    for a_casu in [active_casu, passive_casu]:
        a_casu.diagnostic_led_standby () # turn the top led off
        a_casu.set_speaker_vibration (freq = 0, intens = 0)
        a_casu.ir_standby ()             # turn the IR sensor off to make the background image
        #        a_casu.set_temp (28)
        a_casu.airflow_standby ()
    return (active_casu, passive_casu)
