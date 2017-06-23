
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




class calibrator():
    def __init__(self,parent=None,worker=None):
        #function and Variable Ddeclaration   
        
        #=======================================================================
        # Setup calibration tab defaults
        #=======================================================================
        #input
        self.inputPwr=0#input to Tx in dB
        
        #antenna
        self.txGain=0#rx antenna gain in dB
        
        self.ampGain=0#input power to Tx
        #cable
        self.cableLoss=0#gain loss due to cable in dB
        #oats
        self.dist=10#testing distance in m
        self.fspl=0
        
        self.freq=100#initial value for test frequency in MHz
        
        self.additionalGain=0#user can add additional gain
        
        #configueAquisition
        self.aq_detector="min-max"#data retrieval setting for signal hound
        self.aq_scale="log-scale"#scaling type for data 
        #configureLevel
        self.level_atten="auto"#attenuation setting for signal hound
        self.level_ref=0#reference setting for signalhound attenuation
        #configure gain
        self.gain='auto'#gain setting for signalhound
        #configureSweepCoupling
        self.sc_rbw=10e3#resolution bandwidth setting
        self.sc_vbw=10e3#video bandwidth setting
        self.sc_sweepTime=.025#sweep time setting
        self.sc_rbwType="native"# resolution bandwidth type, see signal hound api-datasheet for details
        self.sc_rejection="no-spur-reject"#spurious data rejection setting
        #configure center/ span
        self.cp_center=100e6#sweep center frequency in Hz
        self.ccp_span=200e3#sweep span in Hz
        


