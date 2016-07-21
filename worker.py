#!/usr/bin/env python
# -*- coding: utf-8 -*-

import zmq_sock_utils

from assisipy import casu

import time
import sys
import zmq
import signal

INITIALIZE             = 1
ACTIVE_CASU            = 5
PASSIVE_CASU           = 6
#RUN_VIBRATION_PATTERN  = 2
#SPREAD_BEES            = 3
CASU_STATUS            = 4
WORKER_OK              = 1000

CASU_TEMPERATURE = 28


def active_casu ():
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    chromosome.SinglePulseGenePause.run_vibration_pattern (message [1], a_casu, evaluation_run_time)
    a_casu.speaker_standby ()
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()

def passive_casu ():
    time.sleep (2.0 / frame_per_second)
    time.sleep (evaluation_run_time)
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()

def signal_handler (signal, frame):
    print ('You pressed Ctrl+C!')
    a_casu.stop ()
    sys.exit (0)


if __name__ == '__main__':

    # parse arguments
    if len (sys.argv) != 3:
        print ('Missing number!\nUsage:\npython worker.py CASU_NUMBER ZMQ_ADDRESS\n')
        sys.exit (1)
    zmq_address = sys.argv [2]
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

    # open ZMQ server socket
    context = zmq.Context ()
    socket = context.socket (zmq.REP)
    socket.bind (zmq_address)

    # wait for initialisation message
    print ("Waiting for initialisation message...")
    message = zmq_sock_utils.recv (socket)
    if message [0] != INITIALIZE or len (message) != 4:
        print ("Invalid initialisation message!\n" + str (message))
        a_casu.stop ()
        sys.exit (3)
    else:
        evaluation_run_time = message [1]
        spreading_waiting_time = message [2]
        frame_per_second = message [3]
        zmq_sock_utils.send (socket, [WORKER_OK])

    # prepare the CASU (turn the IR sensor off to make the background image)
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()

    # install signal handler to exit worker gracefully
    signal.signal (signal.SIGINT, signal_handler)

    # main loop
    print ("Entering main loop.")
    while True:
        message = zmq_sock_utils.recv (socket)
        print ("Received request: %s" % str (message))
        command = message [0]
        if command == ACTIVE_CASU:
            active_casu ()
        elif command == PASSIVE_CASU:
            passive_casu ()
        elif command == CASU_STATUS:
            print (a_casu.get_temp (casu.ARRAY))
            zmq_sock_utils.send (socket, a_casu.get_temp (casu.TEMP_WAX))
        elif command == RUN_VIBRATION_PATTERN:
            pass
        elif command == SPREAD_BEES:
            pass
        else:
            print ("Unknown command:\n%s" % (str (message)))
