'''
project: Rotator Rev2 
copyright 2017 NextGen RF Design
author Mike Collins
mike.collins@nextgenrf.com

The Setup class is a subclass of a QDialog dialog box. it creates
a dialog box that is used to setup basic test functions and locate 
the spectrum analyzer and turn-table.   

'''

import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import multiprocessing,logging

#TODO change for actual 3d plotting

from SignalHound import *
from worker import *
from specan import *
from arcus import *

import numpy as np
import math
import time
from pip._vendor.requests.packages.chardet.latin1prober import FREQ_CAT_NUM


class Setup(QDialog):#create setup dialog that finds specan and turntable, and sets basic specan parameters
    def __init__(self,parent=None,worker=None,cal=None):
#==================================================
#initialize all variables and functions for setup dialog
#==================================================
        super(Setup,self).__init__(parent)
        self.worker=worker
        self.cal=cal
        #setup base layout for dialog box
        self.setWindowTitle("Setup")
        self.vert = QVBoxLayout()
        self.form = QFormLayout()
        self.b_analyzer = QPushButton("Find Devices")#create push button to initialize search for devices
        
        self.b_box = QDialogButtonBox(QDialogButtonBox.Ok  | QDialogButtonBox.Cancel)#create "OK" and "Cancel" push buttons in dialog window
        self.b_box.addButton(self.b_analyzer,QDialogButtonBox.ActionRole)#create button instanciated above
        
        #setup GUI form and user interactions
        self.e_sweep = QLineEdit()                  #create one line text editor for sweep time
        self.e_cfreq = QLineEdit()                  #create one line text editor for sweep center frequency
        self.e_span=QLineEdit()                     #create one line text editor for span of sweep
        self.e_res = QLineEdit()
        self.e_offset = QLineEdit()                 #create one line text editor fo offrset
        self.c_siggen = QCheckBox(enabled=False)    #set up check box to use signal generrator
        self.c_maxhold=QCheckBox(checked=False)     #set up checkbox to use max hold
        
        self.e_specan=QLineEdit(enabled=False)      #create one line text editor for spectrum analyzer
        self.e_rotator=QLineEdit(enabled=False)     #create one line text editor for rotor
        self.cb_specan_type=QComboBox()
        
        #create spectrum analyzer selection combo box
        self.cb_specan_type.setToolTip("Select Cable Calibration Frequency")
        self.cb_specan_type.currentIndexChanged.connect(self.select_specan)
        self.cb_specan_type.setEnabled(True)
        self.specanDict={}#dictionary holds the identifiers of the different specans
        
        try:#import list of specans from specans.csv
            with open('specans/specans.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" spectrum analyzer file found")
                        self.specanDict[row[0]]=row[1];
                        self.cb_specan_type.addItem(row[0])
                        
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        
        
        
        
        #set up labels for input fields
        self.form.addRow("Sweep Time (ms)", self.e_sweep)
        self.form.addRow('Center Freq (MHz)',self.e_cfreq)
        self.form.addRow('Span (MHz)',self.e_span)
        self.form.addRow('Resolution (# of Data Points)',self.e_res)
        self.form.addRow('Offset (dB)',self.e_offset)
        self.form.addRow('Use Sig Gen',self.c_siggen)
        self.form.addRow('Use Max Hold',self.c_maxhold)
        self.form.addRow('Spectrum Analyzer Type', self.cb_specan_type)
        self.form.addRow('Spectrum Analyzer:',self.e_specan)
        self.form.addRow('Rotating Table:',self.e_rotator)
        
        #setup layout of GUI
        self.vert.addLayout(self.form)
        self.vert.addWidget(self.b_box)
        self.setLayout(self.vert)
        
        #set button behavior
        self.connect(self.b_box, SIGNAL('rejected()'),self.click_cancel)        #behavior when "cancel" is clicked
        self.connect(self.b_box, SIGNAL('accepted()'),self.click_ok)            #behavior when "ok" is clicked
        self.connect(self.b_analyzer, SIGNAL('clicked()'),self.click_analyzer)  #behavior when "Find Devices" is clicked
        
        
        #=======================================================================
        # Defaults - Order of appearance in get_values
        #=======================================================================
        self.num_st=0.025       #sweep time
        self.num_cfreq=100e6    #center frequency
        self.num_span=200e3     #frequency span
        self.num_res=100          #resolution (number of data points)
        self.num_offset=0       #dB offset
        self.maxhold=False      #use max hold
        self.usesig=False       #use signal generator
        
        #set text of input fields
        self.e_sweep.setText(str(self.num_st*1000))     #sweep time
        self.e_cfreq.setText(str(self.num_cfreq/1e6))   #center frequency
        self.e_span.setText(str(self.num_span/1e6))     #frequency span
        self.e_offset.setText(str(self.num_offset))     #dB offset
        self.e_res.setText(str(self.num_res)) 
        self.dev_connected=False
        self.worker.dev_found.connect(self.device_found)
        
    def select_specan(self):
        #=======================================================================
        #
        #          Name:    select_specan
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the spectrum analyzer identifier
        #                    so the "specan" object can run the correct behavior
        #
        #=======================================================================
        
        #get specan Identifier from specanDict
        spec=self.specanDict[str(self.cb_specan_type.currentText())]
        
        #set SpectrumAnalyzerType in specan object
        self.worker.specan.set_SpectrumAnalyzerType(str(spec))
        
        #enable/disable appropriate user interfaces based on specan type
        #===================================================================
        # SIGNALHOUND BB60C
        #===================================================================
        if(spec=="SH"):
            self.c_maxhold.setEnabled(False)
            self.c_maxhold.setChecked(False)
            self.c_siggen.setEnabled(False)
            self.c_siggen.setChecked(False)
        #=======================================================================
        # HP 8566B Specan
        #=======================================================================    
        if(spec=="HP"):
            self.c_maxhold.setEnabled(True)
            self.c_maxhold.setChecked(False)
            self.c_siggen.setEnabled(False)
            self.c_siggen.setChecked(False)
        #===================================================================
        # TODO: NEW SPECAN
        #===================================================================
        if(spec=="New_Specan_ID"):    
                pass
        
    def click_analyzer(self):
        #=======================================================================
        #
        #          Name:    click_analyzer
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function initiates a search for the spectrum analyzer and rotating table
        #
        #=======================================================================
        self.worker.do_work(self.worker.Functions.find_device)          #start search for spectrum analyzer
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(False)        #disable ok button
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(False)    #disable cancel button
        self.b_analyzer.setEnabled(False)                               #disable find device button
        self.b_analyzer.setText("Please wait...")
    
    def click_ok(self):
        #=======================================================================
        #
        #          Name:    click_ok
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    on clicking "OK" in setup dialog box execute this code
        #                   this accepts the test parameters
        #
        #=======================================================================
        """convert values to float, complain if get an exception
        """
        try:
        #set test parameters to memory
            self.num_st=float(self.e_sweep.text())
            self.num_cfreq=float(self.e_cfreq.text())
            self.num_span=float(self.e_span.text())
            self.num_offset=float(self.e_offset.text())
            self.num_res=float(self.e_res.text())
        #show problem with user input
        except ValueError:
            msg = "Non-numeric data entered!" 
            QMessageBox.critical(self, "Error", msg)
            return#exit function if incorrect user input
        
        #format user input for test
        self.num_st=self.num_st/1000
        self.num_cfreq = self.num_cfreq*1e6
        self.num_span=self.num_span*1e6
        self.maxhold=self.c_maxhold.isChecked()

        #if all input is good set up spectrum analyzer in worker class
        if self.dev_connected:
            self.worker.do_work(self.worker.Functions.setup_sa)
        #apply calibration values to calibrator    
        self.cal.get_setupDialogValues()    
        
        #update calibration values in calibrator object
        self.cal.update_calibration()
        
        
        self.close()
        
    def click_cancel(self):
        #=======================================================================
        #
        #          Name:    click_cancel
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function closes the setup dialog box when the user presses
        #                    the cancel button
        #
        #=======================================================================

        #exit setup dialog without saving values
        self.close()
        
    def get_values(self):
        #=======================================================================
        #
        #          Name:    get_values
        #
        #    Parameters:    None
        #
        #        Return:    (list)[num_st, num_cfreq, num_span, num_offset, maxhold, usesig]
        #
        #   Description: this function returns a list of the values of user inputted settings
        #
        #=======================================================================
        return [self.num_st,
                    self.num_cfreq,
                    self.num_span,
                    self.num_offset,
                    self.maxhold,
                    self.usesig,
                    self.num_res]
                    
    def device_found(self,devices=[False,'Not Found','Not Found']):
        #=======================================================================
        #
        #          Name:    device_found
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function creates the find device button and will
        #                    activate it when not searching for devices. 
        #
        #                    it will also set the text in the Spectrum analyzer and 
        #                    rotating table text edit boxes 
        #
        #=======================================================================
        print 'device update....'
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(True)         #enable OK button
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(True)     #enable Cancel button
        self.b_analyzer.setEnabled(True)                                #enable find device button
        self.b_analyzer.setText('Find Devices')                         #set find device button text
        
        #create a list of connected devices
        self.dev_connected=devices[0]
        
        #check length of device list and display 
        if len(devices)>1:
            self.e_rotator.setText(devices[1])  #display if rotator is found
            self.e_specan.setText(devices[2])   #display if spectrum analyzer is found
            
    def set_frequency(self,freq):#set test frequency externally
        #=======================================================================
        #
        #          Name:    set_frequency
        #
        #    Parameters:    (float)freq
        #
        #        Return:    None
        #
        #   Description:    this function allows external object to change the 
        #                    frequency setting of the setup dialog box
        #
        #=======================================================================
        'set testing frequency'
        self.num_cfreq = float(freq)
        self.e_cfreq.setText(str(float(freq)/1e6))
     
    def set_span(self,span):#set test frequency span externally
        #=======================================================================
        #
        #          Name:    set_span
        #
        #    Parameters:    (float)span
        #
        #        Return:    None
        #
        #   Description:    this function allows external objects to change the 
        #                    frequency setting of the setup dialog box
        #
        #=======================================================================
        'set testing frequency span'
        self.num_span = float(span)
        self.e_span.setText(str(float(span)/1e6))     
   
    def set_sweepTime(self,st):#set test frequency span externally
        #=======================================================================
        #
        #          Name:    set_sweepTime
        #
        #    Parameters:    (float)st
        #
        #        Return:    None
        #
        #   Description:    this fucntion allows external object to change the 
        #                    sweeptime setting of the setup dialog box
        #
        #=======================================================================
        'set testing frequency span'
        self.num_st = float(st)
        self.e_sweep.setText(str(float(st)*1e3)) 
        
    def set_resolution(self,resolution):
        self.num_res=float(resolution)
        self.e_res.setText(str(self.num_res))
            