import zmq_sock_utils
import worker

import assisipy.deploy
import assisipy.assisirun

import yaml
import zmq
import os

class WorkerSettings:
    """
    Worker settings used by the master program to deploy the workers.
    These settings specify the CASU that the worker will control,
    the ZMQ address where the worker will listen for commands from the master,
    and the parameters of the RTC file.
    """
    def __init__ (self, dictionary):
        self.casu_number = dictionary ['casu_number']
        self.wrk_addr    = dictionary ['wrk_addr']
        self.pub_addr    = dictionary ['pub_addr']
        self.sub_addr    = dictionary ['sub_addr']
        self.msg_addr    = dictionary ['msg_addr']
        self.socket = None
        self.in_use = False

    def __key_ (self):
        return 'casu-%03d' % (self.casu_number)

    def to_dep (self):
        return (
            self.__key_ () ,
            {
                'controller' : os.path.dirname (os.path.abspath (__file__)) + '/worker.py'
              , 'extra'      : [
                    os.path.dirname (os.path.abspath (__file__)) + '/chromosome.py'
                  , os.path.dirname (os.path.abspath (__file__)) + '/zmq_sock_utils.py'
                  ]
              , 'args'       : [str (self.casu_number), 'tcp://*:%s' % (self.wrk_addr.split (':') [2])]
              , 'hostname'   : self.wrk_addr.split (':') [1][2:]
              , 'user'       : 'assisi'
              , 'prefix'     : 'pedro/evovibe'
              , 'results'    : []
            })

    def to_arena (self):
        return (
            self.__key_ () ,
            {
                'pub_addr' : self.pub_addr
              , 'sub_addr' : self.sub_addr
              , 'msg_addr' : self.msg_addr
            })

    def connect_to_worker (self, config):
        """
        Connect to the worker and return a tuple with the CASU number and this instance.
        """
        context = zmq.Context ()
        print ("Connecting to worker at %s responsible for casu #%d..." % (self.wrk_addr, self.casu_number))
        self.socket = context.socket (zmq.REQ)
        self.socket.connect (self.wrk_addr)
        print ("Initializing worker responsible for casu #%d..." % (self.casu_number))
        answer = zmq_sock_utils.send_recv (self.socket, [
            worker.INITIALISE,
            config.vibration_run_time,
            config.no_stimulus_run_time,
            config.number_repetitions,
            config.spreading_waiting_time,
            config.frame_per_second,
            config.sound_hardware,
            config.chromosome_type])
        print ("Worker responded with: %s" % (str (answer)))
        return (self.casu_number, self)
    def terminate_session (self):
        """
        Terminate the session with the worker, which causes the worker process to finish.
        """
        print ("Sending terminate command to worker at %s responsible for casu #%d..." % (self.wrk_addr, self.casu_number))
        answer = zmq_sock_utils.send_recv (self.socket, [worker.TERMINATE])
        print ("Worker responded with: %s" % (str (answer)))

    def __str__ (self):
        return 'casu_number : %d , wrk_addr : %s , pub_addr : %s , sub_addr : %s , msg_addr : %s , socket : %s , in_use : %s' % (
            self.casu_number, self.wrk_addr, self.pub_addr, self.sub_addr, self.msg_addr, str (self.socket), str (self.in_use))

def load_worker_settings (filename):
    """
    Return a list with the worker settings loaded from a file with the given name.
    """
    file_object = open (filename, 'r')
    dictionary = yaml.load (file_object)
    file_object.close ()
    worker_settings = [
        WorkerSettings (dictionary ['worker-%02d' % (index)])
        for index in xrange (1, dictionary ['number_workers'] + 1)]
    print ("Loaded worker settings")
    return worker_settings

def deploy_workers (filename, run_number):
    print ('\n\n* ** Worker Apps Launch')
    # load worker settings
    worker_settings = load_worker_settings (filename)
    # create assisi file
    fp_assisi = open ('tmp/workers.assisi', 'w')
    yaml.dump ({'arena' : 'workers.arena'}, fp_assisi, default_flow_style = False)
    yaml.dump ({'dep' : 'workers.dep'}, fp_assisi, default_flow_style = False)
    fp_assisi.close ()
    print ("Created assisi file")
    # create dep file
    fp_dep = open ('tmp/workers.dep', 'w')
    yaml.dump ({'arena' : dict ([ws.to_dep () for ws in worker_settings])}, fp_dep, default_flow_style = False)
    fp_dep.close ()
    print ("Created dep file")
    # create arena file
    fp_arena = open ('tmp/workers.arena', 'w')
    yaml.dump ({'arena' : dict ([ws.to_arena () for ws in worker_settings])}, fp_arena, default_flow_style = False)
    fp_arena.close ()
    print ("Created arena file")
    # deploy the workers
    d = assisipy.deploy.Deploy ('tmp/workers.assisi')
    d.prepare ()
    d.deploy ()
    ar = assisipy.assisirun.AssisiRun ('tmp/workers.assisi')
    ar.run ()
    print ("Workers have finished")

if __name__ == '__main__':
    lws = load_worker_settings ('workers')
    print "Loaded worker settings:"
    print lws
    print "\n\nResult of function to_dep():"
    for ws in lws:
        print ws.to_dep ()
    print "\n\nResult of function to_arena():"
    for ws in lws:
        print ws.to_arena ()
    deploy_workers ('workers', None)
    
