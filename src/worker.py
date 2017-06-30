import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import multiprocessing,logging

#TODO change for actual 3d plotting

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

from SignalHound import *
from specan import *
from arcus import *


import numpy as np
import math
import time

from pip._vendor.requests.packages.chardet.latin1prober import FREQ_CAT_NUM


class Worker(QThread):#create thread that operates spectrum analyzer and turntable
#==================================================
#this class initializes all actions in the application
#==================================================

    #create and enumeration of tasks for worker to use
    class Functions:
        sleep,find_device,rotate,setup_sa,goto_location = range(5)
        
    #create signals for application to use to define behavior
    status_msg = pyqtSignal(object)
    data_pair = pyqtSignal(object)
    dev_found=pyqtSignal(object)
    worker_sleep=pyqtSignal(object)
    
    #movement constant
    degreeRes=3.6
    
    def __init__(self,setup=None):
        super(Worker,self).__init__()
        #QThread.__init__(self)
        self.cond = QWaitCondition()#wait condition for thread timing
        self.mut = QMutex()#control memory threading errors with this mutex
        
        self.specan = SpecAnalyzer(self._status)#create specanalyzer object with status defined by worker
        self.dmx=Arcus(self._status)#create arcus (turntable) object with status defined by worker
        
        self.ang=self.degreeRes#defined by hard coded constant in class definition
        self.task=-1
        self.work_data=[]#creat list to hold...
        self.cancel_work=False#used to stop current job when True
        self.task_awake=-1
        self.setup=setup
        
    def _status(self,msg):#send a status message to whatever 

        self.status_msg.emit(msg)

    def run(self):#run function operates the turntable and specanalyzer to get data
        'perform all data collection and rotation tasks'
    
        #===============================================================================
        # #this function runs the program in whatever task is currently assigned to self.task
        # #possibilities are in the self.Functions.(whatever task)
        #===============================================================================

        print 'started worker thread'
        while self.isRunning():#returns true if worker thread is running
            try:
                
                
                #===============================================================================
                # Find all devices for test dmx=motor,specan=spectrum analzyers
                #===============================================================================
                if self.task is self.Functions.find_device:
                    try:#try to find devices
                        #search for turntable
                        print 'worker is finding dmx'
                        foundDMX=False
                        foundDMX=self.dmx.find_device()
                        print foundDMX
                        
                        #search for specanalyzer
                        foundSpec=False
                        print 'worker finding specan'
                        foundSpec=self.specan.find_device()
                        print foundSpec
                    except:
                        foundDMX=False
                        foundSpec=False
                        
                    #===========================================================
                    # #report devices found to setup dialog and main application
                    #===========================================================
                    if foundDMX and not foundSpec:   
                        self._status("Spectrum Analyzer not found!")
                        self.dev_found.emit([True,self.dmx.name,'Not Found'])#allow the program to run without analyzer
                        #self.dmx.pos_home()
                    elif not foundDMX and foundSpec:
                        self._status("Rotating Table not found!")
                        #self.dev_found.emit([False,'Not Found',self.specan.device])
                        self.dev_found.emit([False,'Not Found',self.specan.sh_type])
                    elif foundDMX and foundSpec:
                        self._status("Ready!")
                        #self.dev_found.emit([True,self.dmx.name,self.specan.device])
                        self.dev_found.emit([True,self.dmx.name,self.specan.sh_type])
                        #self.dmx.pos_home()
                    else:
                        self._status("No devices found.")
                        self.dev_found.emit([False,'Not Found','Not Found'])
                    self.task = self.Functions.sleep
                    
                    
                #===============================================================
                # Rotate table and take measurements
                #===============================================================
                elif self.task is self.Functions.rotate:
                    print 'worker is rotating table'
                    #print time.time()
                    if self.ang-self.degreeRes < 0.1:
                        self.dmx.enable(True)
                        self._status("Returning to home position, please wait...")
                        #self.dmx.move(3) #work around in case sitting at home
                        while not self.dmx.pos_home():
                            pass
                    # print "time : "
                    # print  time.time()
                    settings=self.setup.get_values()
                    
                    #clear trace data from on specanalyzer
                    self.specan.clear_trace()

                    #print "time : "
                    #print time.time() 
                    while not self.dmx.move_nonblocking(self.ang):
                        pass
                    time.sleep(settings[0]) #sleeping while the trace loads allows other threads to run
                    stat=self.dmx.ask_cmd("SLS")
                    while stat is False:
                        stat=self.dmx.ask_cmd("SLS")
                    while stat.find('0') is -1 or stat.find('10') is not -1:
                        stat=self.dmx.ask_cmd("SLS")
                        self._status("At position " + str(self.dmx.get_pos_deg()))
                        # print "status : "
                        # print stat
                        if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
                            self.dmx.ask_cmd("CLR")
                            self._status("Problem moving, current position is " + str(self.dmx.get_pos_deg()))
                            print 'problem moving'
                    self._status("At position " + str(self.dmx.get_pos_deg()))
                    #print "At position " + str(self.dmx.get_pos_deg()) + " expect pos " + str(self.ang)
                    #print "time : "
                    #print time.time()
                    
                    #==========================================================
                    #spectrum analyzer gets test data here
                    #==========================================================
                    
                    #get magnitude of sample from specan
                    mag=self.specan.get_peak_power()
                    
                    print time.time()
                    
                    #send data via signal 
                    self.data_pair.emit([self.ang,mag])

                    #===========================================================
                    # Move to next location
                    #===========================================================
                    self.ang = self.ang+self.degreeRes
                    if self.ang >(360+1.5*self.degreeRes) or self.cancel_work:
                        self.task = self.Functions.sleep
                        self.ang=self.degreeRes
                        self._status("Returning to home position, please wait...")
#                        while not self.dmx.move_nonblocking(350):
#                            pass
#                        time.sleep(settings[0])
#                        stat=self.dmx.ask_cmd("SLS")
#                        while stat.find('0') is -1 and stat.find('10') is not -1:
#                            stat=self.ask_cmd("SLS")
#                            self._status("At position " + str(self.get_pos_deg()))
#                            print stat
#                            if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
#                                self.ask_cmd("CLR")
#                                self._status("Problem moving, current position is " + str(self.get_pos_deg()))
#                                print 'problem moving'
                        print 'home from end'
                        while not self.dmx.pos_home():
                            pass
                        
                        
                #===============================================================
                # Setup Spectrum analyzer
                #===============================================================
                elif self.task is self.Functions.setup_sa:
                    settings=self.setup.get_values()# get setup values from user input
                   
                    print 'worker is setting up sa'
                    print settings
                    try:
                        #self.specan.set_frequency(settings[1],settings[2])
                        self.specan.set_max_hold(settings[4])#set up max hold from user input (may be obsolete)
                        #self.specan.set_sweeptime(settings[0]*1000)
                        
                        #===========================================================================
                        # signal hound configuration
                        #===========================================================================
                        self.specan.sh.configureGain('auto')
                        self.specan.sh.configureLevel(ref = 0, atten = 'auto')
                        self.specan.sh.configureProcUnits("log")
                        self.specan.sh.configureAcquisition("average","log-scale")
                        #setup sweep coupling if maxhold is selected it will use 100ms for sweeptime
                        self.specan.sh.configureCenterSpan(settings[1],settings[2])
                        if settings[4]:
                            self.specan.sh.configureSweepCoupling(10e3,10e3,0.1,"native","spur-reject")#may need fixing form parent
                        else:
                            self.specan.sh.configureSweepCoupling(10e3,10e3,settings[0],"native","spur-reject")#may need fixing form parent
                        #==========================================
                        
                        
                    except:
                        print 'unexpected error:',sys.exc_info()
                    self.task = self.Functions.sleep
                    
                    
                #===============================================================
                # move table to location
                #===============================================================
                elif self.task is self.Functions.goto_location:
                    if self.dmx.name is "":
                        self.task = self.Functions.sleep
                    else:
                        while not self.dmx.move_nonblocking(self.work_data[0]):
                            pass
                        stat=self.dmx.ask_cmd("SLS")
                        while stat is False:
                            stat=self.dmx.ask_cmd("SLS")
                        print stat
                        print "stat find 10:",
                        print stat.find('10')
                        print "stat find 0:",
                        print stat.find('0')
                        while stat.find('0') is -1 or stat.find('10') is not -1:
                            stat=self.dmx.ask_cmd("SLS")
                            self._status("At position " + str(self.dmx.get_pos_deg()))
                            print stat
                            if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
                                self.dmx.ask_cmd("CLR")
                                self._status("Problem moving, current position is " + str(self.dmx.get_pos_deg()))
                                print 'problem moving'
                        self._status("At position " + str(self.dmx.get_pos_deg()))
                        self.task = self.Functions.sleep 
                        
                        
                #===============================================================
                # Put worker to sleep
                #===============================================================
                else:
                    if self.task is self.Functions.sleep:#check if current task is sleep if so send worker sleep true signal
                        self.worker_sleep.emit(True)
                        
                    self.cancel_work=False
                    print 'worker sleeping'
                    self.mut.lock()
                    self.cond.wait(self.mut)
                    self.mut.unlock()
                    print 'worker awake'
                    
                    
            #==================================================
            #report error in worker
            #==================================================
            except Exception,e:
                print 'exception in worker: ' + str(e)
            
    def do_work(self,work,work_data=[]):
        'initiate a task'
        self.task=work
        self.work_data=work_data
        print work
        self.cond.wakeAll()
    
    def pause_work(self,pause_pressed):
        'Pause mid-task'
        print pause_pressed
        print self.task
        if pause_pressed:
            #save off current work
            self.task_awake=self.task
            self.task=-1 
        else:
            #restore old task
            self.task = self.task_awake 
            self.cond.wakeAll() 
        print self.task
        print self.task_awake    

    def set_setup(self,setup):
        'holds setup dialog box'
        self.setup=setup
        
        
        
        
        
        
