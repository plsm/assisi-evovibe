#!/usr/bin/env python
# -*- coding: utf-8 -*-

import chromosome
import zmq_sock_utils

from assisipy import casu

import time
import sys
import zmq
import signal

INITIALISE                   = 1
ACTIVE_CASU                  = 5
PASSIVE_CASU                 = 6
CASU_STATUS                  = 4
VIBRATION_PATTERN_440_09_01  = 7
STANDBY_CASU                 = 8
SPREAD_BEES                  = 10
TERMINATE                    = 31
WORKER_OK              = 1000

CASU_TEMPERATURE = 28

evaluation_run_time = None
vibration_run_time = None
no_stimuli_run_time = None
number_repetitions = None
spreading_waiting_time = None
frame_per_second = None
run_vibration_model = None

keep_going = True

def blip_casu ():
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    
def cmd_initialise ():
    if len (message) != 8:
        print ("Invalid initialisation message!\n" + str (message))
        a_casu.stop ()
        sys.exit (3)
    global evaluation_run_time
    global vibration_run_time
    global no_stimuli_run_time
    global number_repetitions
    global spreading_waiting_time
    global frame_per_second
    global run_vibration_model
    print ("W%dC Initialisation message..." % casu_number)
    vibration_run_time     = message [1]
    no_stimuli_run_time   = message [2]
    number_repetitions     = message [3]
    spreading_waiting_time = message [4]
    frame_per_second       = message [5]
    sound_hardware         = message [6]
    chromosome_type        = message [7]
    if sound_hardware == 'Zagreb':
        run_vibration_model = chromosome.CHROMOSOME_METHODS [chromosome_type].run_vibration_model [sound_hardware]
    elif sound_hardware == 'Graz':
        run_vibration_model = None
    evaluation_run_time = number_repetitions * (vibration_run_time + no_stimuli_run_time) + vibration_run_time
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_active_casu ():
    print ("W%dC Active CASU..." % casu_number)
    # a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    # time.sleep (2.0 / frame_per_second)
    # a_casu.diagnostic_led_standby ()
    blip_casu ()
    if run_vibration_model is None:
        time.sleep (evaluation_run_time) # sound hardware by Graz
    else:
        run_vibration_model (message [1], a_casu, vibration_run_time, no_stimuli_run_time, number_repetitions)
    a_casu.speaker_standby ()
    # a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    # time.sleep (2.0 / frame_per_second)
    # a_casu.diagnostic_led_standby ()
    blip_casu ()
    print ("W%dC Spreading..." % (casu_number))
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_passive_casu ():
    print ("W%dC Passive CASU..." % casu_number)
    time.sleep (2.0 / frame_per_second)
    time.sleep (evaluation_run_time)
    # a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    # time.sleep (2.0 / frame_per_second)
    # a_casu.diagnostic_led_standby ()
    blip_casu ()
    print ("W%dC Spreading..." % (casu_number))
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_vibration_pattern_440_09_01 ():
    print ("W%dC Running vibration pattern: frequency 440Hz, duration 0.9s, pause 0.1s" % (casu_number))
    number_repeats = message [1]
    for n in xrange (number_repeats):
        print ("W%dC Repeat #%d" % (casu_number, n + 1))
        blip_casu ()
        vibe_periods = [900,  100]
        vibe_freqs   = [440,    1]
        vibe_amps    = [ 50,    0]
        el_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        blip_casu ()
        a_casu.speaker_standby ()
        time.sleep (spreading_waiting_time)
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_standby_casu ():
    print ("W%dC Putting CASU in standby" % (casu_number))
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_spread_bees ():
    print ("W%dC Spreading bees..." % (casu_number))
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.set_airflow_intensity (1)
    time.sleep (message [1])
    a_casu.airflow_standby ()
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_terminate ():
    global keep_going
    print ("W%dC Terminating..." % (casu_number))
    a_casu.airflow_standby () # this is not done by casu.stop()
    a_casu.stop ()
    keep_going = False
    print ("W%dC Done!" % (casu_number))
    zmq_sock_utils.send (socket, [WORKER_OK])

def signal_handler (signum, frame):
    if signum == signal.SIGINT:
        print ('W%dC You pressed Ctrl+C!' % (casu_number))
    else:
        print ("W%dC Received signal number %d!" % (casu_number, signum))
    a_casu.airflow_standby () # this is not done by casu.stop()
    a_casu.stop ()
    sys.exit (0)

if __name__ == '__main__':

    # parse arguments
    usage = 'Usage:\npython worker.py RTC_FILENAME CASU_NUMBER ZMQ_ADDRESS\n'
    if len (sys.argv) != 4:
        print ('Invalid number of options!\n' + usage)
        sys.exit (1)
    zmq_address = sys.argv [3]
    try:
        casu_number = int (sys.argv [2])
    except:
        print ('Option is not a number!\n' + usage)
        sys.exit (1)

    # connect to CASU
    rtc_file_name = sys.argv [1]
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

    # prepare the CASU (turn the IR sensor off to make the background image)
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    
    # install signal handler to exit worker gracefully
    signal.signal (signal.SIGINT, signal_handler)
    signal.signal (signal.SIGTERM, signal_handler)
    signal.signal (signal.SIGQUIT, signal_handler)
    signal.signal (signal.SIGHUP, signal_handler)

    # main loop
    print ("W%dC Entering main loop." % (casu_number))
    while keep_going:
        message = zmq_sock_utils.recv (socket)
        print ("W%dC Received request: %s" % (casu_number, str (message)))
        command = message [0]
        if command == INITIALISE:
            cmd_initialise ()
        elif command == ACTIVE_CASU:
            cmd_active_casu ()
        elif command == PASSIVE_CASU:
            cmd_passive_casu ()
        elif command == CASU_STATUS:
            print ("W%dC temperature readins: %s" % (casu_number, str (a_casu.get_temp (casu.ARRAY))))
            zmq_sock_utils.send (socket, a_casu.get_temp (casu.TEMP_WAX))
        elif command == VIBRATION_PATTERN_440_09_01:
            cmd_vibration_pattern_440_09_01 ()
        elif command == STANDBY_CASU:
            cmd_standby_casu ()
        elif command == SPREAD_BEES:
            cmd_spread_bees ()
        elif command == TERMINATE:
            cmd_terminate ()
        else:
            print ("W%dC Unknown command:\n%s" % (casu_number, str (message)))
