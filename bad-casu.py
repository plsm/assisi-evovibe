#!/usr/bin/env python
# -*- coding: utf-8 -*-


from assisipy import casu

import time
import sys
import zmq
import signal

CASU_TEMPERATURE = 28

if __name__ == '__main__':

    # parse arguments
    if len (sys.argv) != 2:
        print ('Missing number!\nUsage:\npython worker.py CASU_NUMBER ZMQ_ADDRESS\n')
        sys.exit (1)
    try:
        casu_number = int (sys.argv [1])
    except:
        print ('Option is not a number!\nUsage:\npython worker.py CASU_NUMBER\n')
        sys.exit (1)

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

    # prepare the CASU (turn the IR sensor off to make the background image)
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    

