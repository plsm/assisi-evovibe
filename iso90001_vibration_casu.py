# This script tests CASUs to see if they can be used in an evolutionary algorithm to evolve vibration patterns.

# The script expects the numbers of the CASUs to be tested.

# We can run the commands locally, or run the comands in the beagle bones.

import os
import datetime
import sys
from assisipy import casu
import time

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
        a_casu = casu.Casu (
            rtc_file_name = rtc_file_name,
            log = True,
            log_folder = directory
            )
        casus.append ((index, a_casu))
    except BaseException as e:
        print "Failed connecting to casu index %d, rtc filename %s" % (index, rtc_file_name)
        print e

if casus == []:
    sys.exit (1)

raw_input ("Press ENTER to actively cool down the CASUs ")
cool_temperature = 28
for (_, el_casu) in casus:
    el_casu.set_temp (cool_temperature)

test_duration = 45
for (index, le_casu) in casus:
    raw_input ("Put the microphone in casu %d and press ENTER to start test " % index)
    for vibration_frequency in [440]:
        for pause_time in [0.1, 0.5, 1]:
            for vibration_time in [1, 0.5, 0.1]:
                raw_input ("Press ENTER to test vibration pattern %fHz %fs - %fs" % (vibration_frequency, vibration_time, pause_time))
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
                    # le_casu.set_speaker_vibration (freq = 0, intens = 0) # sometimes it does not work!!! It cause CASUs to heat.
                    le_casu.speaker_standby ()
                    time.sleep (pause_time)
                print " Finished!"

for (_, o_casu) in casus:
    o_casu.stop ()

print ("Test finished!")

