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
    casu.ir_standby ("Standby")
    casu.set_temp (28)
    casu.set_diagnostic_led_rgb (r = 0, g = 0, b = 0)
    casu.speaker_standby ()
    casu.set_airflow_intensity (1)
    time.sleep (9)
    casu.airflow_standby ()
    casu.stop ()


