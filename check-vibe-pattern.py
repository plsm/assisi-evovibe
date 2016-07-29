#!/usr/bin/env python
# -*- coding: utf-8 -*-


from assisipy import casu

import time
import sys
import signal


CASU_TEMPERATURE = 28


# connect to CASU
rtc_file_name = 'casu-%03d.rtc' % (casu_number)
try:
        a_casu = casu.Casu (
                rtc_file_name = rtc_file_name,
                log = True,
                log_folder = '.')
except:
        print ("Failed connecting to casu #%d." % (casu_number))
        sys.exit (2)

frame_per_second = 1.0

# prepare the CASU (turn the IR sensor off to make the background image)
a_casu.set_temp (CASU_TEMPERATURE)
a_casu.diagnostic_led_standby ()
a_casu.airflow_standby ()
a_casu.ir_standby ()
a_casu.speaker_standby ()

def blip_casu ():
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()


idle_runtime = 60
vibration_run_time = 45
number_repeats = 5
for _ in xrange (number_repeats):
        blip_casu ()
        vibe_periods = [900,  100]
        vibe_freqs   = [440,    1]
        vibe_amps    = [ 50,    0]
        el_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (vibration_run_time)
        blip_casu ()
        a_casu.speaker_standby ()
        time.sleep (idle_runtime)

a_casu.stop ()
