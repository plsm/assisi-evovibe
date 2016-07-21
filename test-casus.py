import time
import sys
from assisipy import casu

casus = []
for rtc_file_name in sys.argv[1:]:
    try:
        a_casu = casu.Casu (
            rtc_file_name = rtc_file_name,
            log = False)
        casus.append ((rtc_file_name, a_casu))
    except :
        print "Failed connecting to casu:", rtc_file_name

for (rtc_file_name, casu) in casus:
    raw_input ("Press ENTER to test " + rtc_file_name)
    for i in xrange (4):
        casu.ir_standby ("Activate")
        time.sleep (1)
        casu.ir_standby ("Standby")
        time.sleep (1)
    for i in xrange (3):
        casu.set_diagnostic_led_rgb (r = 1, g = 0, b = 0)
        time.sleep (1)
        casu.set_diagnostic_led_rgb (r = 1, g = 1, b = 0)
        time.sleep (1)
        casu.set_diagnostic_led_rgb (r = 1, g = 1, b = 1)
        time.sleep (1)
    casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
    for i in xrange (9):
        casu.set_speaker_vibration (freq = 440, intens = 100)
        time.sleep (0.9)
        casu.set_speaker_vibration (freq = 0, intens = 0)
        time.sleep (0.1)
    casu.set_airflow_intensity (1)
    time.sleep (9)
    casu.airflow_standby ()

