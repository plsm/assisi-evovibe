from assisipy import casu

import os
import csv
import time

CASU_TEMPERATURE = 28
"""
Casu temperature used in incremental evolution of vibration patterns. 
"""

def create_directories (config):
    """
    Create the directories for the given experimental run.
    """
    warning = False
    for path in [config.experimentpath + "logs/", config.experimentpath, config.repositorypath, config.experimentpath + "populations/", config.experimentpath + "Images/"]:
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
        log_folder = config.experimentpath + "logs")
    passive_casu = casu.Casu (
        rtc_file_name = config.passive_casu_rtc_file_name,
        log = True,
        log_folder = config.experimentpath + "logs")
    test_casus ([(config.active_casu_rtc_file_name, active_casu), (config.passive_casu_rtc_file_name, passive_casu)])
    for a_casu in [active_casu, passive_casu]:
        a_casu.diagnostic_led_standby () # turn the top led off
        a_casu.speaker_standby ()
        a_casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
        a_casu.ir_standby ()             # turn the IR sensor off to make the background image
        a_casu.set_temp (CASU_TEMPERATURE)
        a_casu.airflow_standby ()
    return (active_casu, passive_casu)
    
    
def test_casus (casus):
    print "\n\n* ** CASU test"
    for (rtc_file_name, casu) in casus:
        raw_input ("Press ENTER to test " + rtc_file_name)
        print "   Testing IR sensors..."
        for i in xrange (4):
            casu.ir_standby ("Activate")
            time.sleep (1)
            casu.ir_standby ("Standby")
            time.sleep (1)
        print "   Testing LED..."
        for i in xrange (3):
            casu.set_diagnostic_led_rgb (r = 1, g = 0, b = 0)
            time.sleep (1)
            casu.set_diagnostic_led_rgb (r = 1, g = 1, b = 0)
            time.sleep (1)
            casu.set_diagnostic_led_rgb (r = 1, g = 1, b = 1)
            time.sleep (1)
        casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
        print "   Testing vibration..."
        for i in xrange (9):
            casu.set_speaker_vibration (freq = 440, intens = 100)
            time.sleep (0.9)
            casu.speaker_standby ()
            time.sleep (0.1)
        print "   Testing air pump..."
        casu.set_airflow_intensity (1)
        time.sleep (9)
        casu.airflow_standby ()
        print "   Checking temperature..."
        for i in xrange (9):
            if casu.get_temp () > CASU_TEMPERATURE + 1:
                print "      temperature is %f" % casu.get_temp ()
            time.sleep (1)
    raw_input ("Press ENTER to continue ")

