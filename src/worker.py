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
WORKER_OK              = 1000

CASU_TEMPERATURE = 28

evaluation_run_time = None
spreading_waiting_time = None
frame_per_second = None
run_vibration_model = None

def blip_casu ():
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    
def cmd_initialise ():
    if len (message) != 5:
        print ("Invalid initialisation message!\n" + str (message))
        a_casu.stop ()
        sys.exit (3)
    global evaluation_run_time
    global spreading_waiting_time
    global frame_per_second
    global run_vibration_model
    print ("Initialisation message...")
    evaluation_run_time = message [1]
    spreading_waiting_time = message [2]
    frame_per_second = message [3]
    if message [4] == "SinglePulseGenePause":
        run_vibration_model = chromosome.SinglePulseGenePause.run_vibration_model
    elif message [4] == "SinglePulseGenesPulse":
        run_vibration_model = chromosome.SinglePulseGenesPulse.run_vibration_model
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_active_casu ():
    print ("Active CASU...")
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    run_vibration_model (message [1], a_casu, evaluation_run_time)
    a_casu.speaker_standby ()
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    print ("Spreading...")
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()
    print ("Done!")
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_passive_casu ():
    print ("Passive CASU...")
    time.sleep (2.0 / frame_per_second)
    time.sleep (evaluation_run_time)
    a_casu.set_diagnostic_led_rgb (0.5, 0, 0)
    time.sleep (2.0 / frame_per_second)
    a_casu.diagnostic_led_standby ()
    print ("Spreading...")
    a_casu.set_airflow_intensity (1)
    time.sleep (spreading_waiting_time)
    a_casu.airflow_standby ()
    print ("Done!")
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_vibration_pattern_440_09_01 ():
    print ("Running vibration pattern: frequency 440Hz, duration 0.9s, pause 0.1s")
    number_repeats = message [1]
    for n in xrange (number_repeats):
        print ("Repeat #%d" % (n + 1))
        blip_casu ()
        vibe_periods = [900,  100]
        vibe_freqs   = [440,    1]
        vibe_amps    = [ 50,    0]
        el_casu.set_vibration_pattern (vibe_periods, vibe_freqs, vibe_amps)
        time.sleep (evaluation_run_time)
        blip_casu ()
        a_casu.speaker_standby ()
        time.sleep (spreading_waiting_time)
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_standby_casu ():
    print ("Putting CASU in standby")
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.diagnostic_led_standby ()
    a_casu.airflow_standby ()
    a_casu.ir_standby ()
    a_casu.speaker_standby ()
    zmq_sock_utils.send (socket, [WORKER_OK])

def cmd_spread_bees ():
    print ("Spreading bees...")
    a_casu.set_temp (CASU_TEMPERATURE)
    a_casu.set_airflow_intensity (1)
    time.sleep (message [1])
    a_casu.airflow_standby ()
    print ("Done!")
    zmq_sock_utils.send (socket, [WORKER_OK])

def signal_handler (signal, frame):
    print ('You pressed Ctrl+C!')
    a_casu.airflow_standby () # this is not done by casu.stop()
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
        if command == INITIALISE:
            cmd_initialise ()
        elif command == ACTIVE_CASU:
            cmd_active_casu ()
        elif command == PASSIVE_CASU:
            cmd_passive_casu ()
        elif command == CASU_STATUS:
            print (a_casu.get_temp (casu.ARRAY))
            zmq_sock_utils.send (socket, a_casu.get_temp (casu.TEMP_WAX))
        elif command == VIBRATION_PATTERN_440_09_01:
            cmd_vibration_pattern_440_09_01 ()
        elif command == STANDBY_CASU:
            cmd_standby_casu ()
        elif command == SPREAD_BEES:
            cmd_spread_bees ()
        else:
            print ("Unknown command:\n%s" % (str (message)))