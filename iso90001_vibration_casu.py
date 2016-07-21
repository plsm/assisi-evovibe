# This script tests CASUs to see if they can be used in an evolutionary
# algorithm to evolve vibration patterns.
#
# The script expects the numbers of the CASUs to be tested.  Usage example:
#
# python iso90001_vibration_casu.py 1 2 5
#
# The commands are run locally.
#
# Pedro Mariano 2016-07-01
#


import os
import datetime
import sys
import assisipy
import time
import signal
import sys

now = datetime.datetime.now ()
directory = "iso90001_vibration_casu_%4d-%02d-%02d-%02d-%02d-%02d/" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
os.makedirs (directory)

if len (sys.argv) == 1:
    indexes = [str (i) for i in xrange (1, 10)]
else:
    indexes = sys.argv[1:]

casus = []
for sindex in indexes:
    index = int (sindex)
    try:
        rtc_file_name = "casu-%03d.rtc" % (index)
        a_casu = assispy.casu.Casu (
            rtc_file_name = rtc_file_name,
            log = True,
            log_folder = directory
            )
        casus.append ((index, a_casu))
    except BaseException as e:
        print "Failed connecting to casu index %d, rtc filename %s" % (index, rtc_file_name)
        print e

if casus == []:
    print ("No casus to test!")
    sys.exit (1)

signal.signal(signal.SIGINT, signal_handler)

raw_input ("Press ENTER to actively cool down the CASUs ")
cool_temperature = 28
for (_, el_casu) in casus:
    el_casu.set_temp (cool_temperature)
    el_casu.speaker_standby ()

test_duration = 20
for (index, the_casu) in casus:
    test_casu (index, the_casu)

for (_, o_casu) in casus:
    o_casu.stop ()

print ("Test finished!")

sys.exit (0)

def test_casu (index, le_casu):
    frequencies = [440]
    pause_times = [0.1, 0.5]
    pause_times = [0.5]
    vibration_times = [1, 0.5]
    vibration_times = [1, 0.5, 0.1]
    print ("\nCASU %d is going to be tested." % (index))
    print ("Put the microphone in the arena.")
    raw_input ("Press ENTER to start testing ")
    for vibration_frequency in frequencies:
        for pause_time in pause_time:
            for vibration_time in vibration_times:
                repeat = True
                while repeat:
                    raw_input ("Press ENTER to test vibration pattern %fHz %fs - %fs " % (vibration_frequency, vibration_time, pause_time))
                    le_casu.set_diagnostic_led_rgb (r = 1, g = 0, b = 1)
                    le_casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
                    zero_time = time.time ()
                    warning_flag = False
                    while time.time () - zero_time < test_duration:
                        print "\rTake a picture in %ds" % (int (test_duration - (time.time () - zero_time))),
                        sys.stdout.flush ()
                        casu_temp = le_casu.get_temp (casu.TEMP_WAX)
                        if casu_temp > cool_temperature + 1 and not warning_flag:
                            print "\nTemperature of casu %d is %f!" % (index, casu_temp)
                            warning_flag = True
                        else:
                            warning_flag = casu_temp > cool_temperature + 1
                        le_casu.set_speaker_vibration (freq = vibration_frequency, intens = 100)
                        time.sleep (vibration_time)
    #                    le_casu.set_speaker_vibration (freq = 0, intens = 0) # sometimes it does not work!!!
                        le_casu.speaker_standby ()
                        time.sleep (pause_time)
                    le_casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
                    le_casu.set_diagnostic_led_rgb (r = 0, g = 1, b = 1)
                    le_casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
                    print " Finished!"
                    answer = raw_input ("Do you want to repeat the test (y/n)? ").upper ()
                    repeat = answer == 'Y'

def signal_handler (signal, frame):
    print ('You pressed Ctrl+C!')
    for (_, das_casu) in casus:
        das_casu.stop ()
    sys.exit(0)
