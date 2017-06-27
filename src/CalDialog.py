import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import multiprocessing,logging

#TODO change for actual 3d plotting

from SignalHound import *
from worker import *
from specan import *
from arcus import *


class CalDialog(QDialog):#create setup dialog that finds specan and turntable, and sets basic specan parameters
    def __init__(self,parent=None,worker=None,fType=None):
#==================================================
#initialize all variables and functions for setup dialog
#==================================================
        super(CalDialog,self).__init__(parent)
        
        
        self.worker=worker
        self.parent=parent
        self.fType=fType
        print self.fType
        #setup base layout for dialog box
        self.setWindowTitle("Setup")
        self.vert = QVBoxLayout()
        
        #create "OK" and "Cancel" push buttons in dialog window
        self.b_box = QDialogButtonBox(QDialogButtonBox.Ok  | QDialogButtonBox.Cancel)
                
        #setup item specific Gui layout of Dialog box
        if self.fType=='antenna':
            self._init_antenna()
        elif self.fType=='cable':
            self._init_cable()
        elif self.fType=='amp':
            self._init_amplifier()
        elif self.fType=='fspl':
            self._init_fspl()
        elif self.fType=='input':
            self._init_sigGen()
        elif self.fType=='specAn':
            self._init_specAn()
        elif self.fType=='sigGen':
            self._init_sigGen()
            
        #set up layouts    
        #self.vert.addLayout(self.form)
        self.vert.addWidget(self.b_box)
        self.setLayout(self.vert)

        
        #set button behavior
        self.connect(self.b_box, SIGNAL('rejected()'),self.click_cancel)#behavior when "cancel" is clicked
        self.connect(self.b_box, SIGNAL('accepted()'),self.click_ok)#behavior when "ok" is clicked
        
        
        self.dev_connected=False
        #self.worker.dev_found.connect(self.device_found)
        
    def setLayout(self,fType):
        pass
               
    def _init_antenna(self):
        "Initialze antenna setting dialog box"
        fbox = QFormLayout()
        #=================================
        # calibrated Antenna selection buttons
        #=================================
        
        #create dictionaries to hold cal data
        self.parent.cal_antFile={}#dictionary thats holds list of file names of calibrated antennas
        self.parent.cal_antennaFreqGain={}#dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_antennaSel=QComboBox()#create combo box to select antenna
        self.cb_antennaSel.addItem('Manual')
        self.cb_antennaSel.setToolTip("Select Calibrated Antenna")
        self.cb_antennaSel.currentIndexChanged.connect(self.parent.on_cal_selectAntenna)
        
        self.cb_antennaFreqSel=QComboBox()#create combo box to select antenna calibration frequency
        self.cb_antennaFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_antennaFreqSel.currentIndexChanged.connect(self.parent.on_cal_selectAntennaGain)
        self.cb_antennaFreqSel.setEnabled(False)
        
        #==========================================
        # import list of antennas from antennas.csv
        #=========================================
        
        try:#import list of calibrated antennas from antennas.csv
            with open('calibration/antennaList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Antenna found")
                        self.cb_antennaSel.addItem(row[0])
                        self.parent.cal_antFile[row[0]]='calibration/antennas/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox.addRow('Antenna Type', self.cb_antennaSel)
        fbox.addRow('Antenna calibration frequency (MHz)',self.cb_antennaFreqSel)
        
        #====================================
        # Manual gain line edit box
        #====================================
        self.e_cal_txGain = QLineEdit('0')
        self.e_cal_txGain.connect(self.e_cal_txGain,SIGNAL('returnPressed()'),self.parent.on_cal_selectAntennaGain)
        try:
            fbox.addRow(QLabel("Rx-Antenna Gain (dBi)"),self.e_cal_txGain)
        except:
            print "couldn't open form"

        self.vert.addLayout(fbox)
    def _init_amplifier(self):
        "Initialze amplifer setting dialog box"
        fbox = QFormLayout()
        #=================================
        # calibrated PreAmp selection buttons
        #=================================
        fbox.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Amplifier</span>'))
        
        #create dictionaries to hold cal data
        self.parent.cal_ampFile={}#dictionary thats holds list of file names of calibrated antennas
        self.parent.cal_ampFreqGain={}#dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_ampSel=QComboBox()#create combo box to select antenna
        self.cb_ampSel.addItem('Manual')
        self.cb_ampSel.setToolTip("Select Calibrated Antenna")
        self.cb_ampSel.currentIndexChanged.connect(self.parent.on_cal_selectAmp)
        
        self.cb_ampFreqSel=QComboBox()#create combo box to select antenna calibration frequency
        self.cb_ampFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_ampFreqSel.currentIndexChanged.connect(self.parent.on_cal_selectAmpGain)
        self.cb_ampFreqSel.setEnabled(False)
        
        #==========================================
        # import list of Preamps from antennas.csv
        #=========================================
        
        try:#import list of calibrated antennas from antennas.csv
            with open('calibration/preampList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_ampSel.addItem(row[0])
                        self.parent.cal_ampFile[row[0]]='calibration/preamps/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox.addRow('Amplifier Type', self.cb_ampSel)
        fbox.addRow('Amplifier calibration frequency (MHz)',self.cb_ampFreqSel)
        
        #====================================
        # Manual amplifier line edit boxes
        #====================================
          
        self.e_cal_ampGain = QLineEdit('0')
        self.e_cal_ampGain.connect(self.e_cal_ampGain,SIGNAL('returnPressed()'),self.parent.on_cal_selectAmpGain)
        fbox.addRow(QLabel("Amplifier Gain (dB)"),self.e_cal_ampGain)
        self.vert.addLayout(fbox)
           
    def _init_cable(self):
        "Initialze cable setting dialog box"
        fbox = QFormLayout()
        self.vert.addLayout(fbox)
    
    def _init_sigGen(self):
        "Initialze signal generator setting dialog box"
        fbox = QFormLayout()
        self.vert.addLayout(fbox)
    
    def _init_specAn(self):
        "Initialze spectrum analyzer setting dialog box"
        fbox = QFormLayout()
        self.vert.addLayout(fbox)
    
    def _init_fspl(self):
        "Initialze spectrum analyzer setting dialog box"
        fbox = QFormLayout()
        self.vert.addLayout(fbox)
        
        
    def click_analyzer(self):
#==================================================
#activates search for spectrum analyzer
#==================================================
        self.worker.do_work(self.worker.Functions.find_device)# start search for spectrum analyzer
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(False)#sdisable ok button
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(False)#disable cancel button
        self.b_analyzer.setEnabled(False)#disable find device button
        self.b_analyzer.setText("Please wait...")
    
    def click_ok(self):
#==================================================
#on clicking "OK" in setup dialog box execute this code
# this accepts the test parameters
#==================================================
        """convert values to float, complain if get an exception
        """
        try:
        #set test parameters to memory
            self.num_st=float(self.e_sweep.text())
            self.num_cfreq=float(self.e_cfreq.text())
            self.num_span=float(self.e_span.text())
            self.num_offset=float(self.e_offset.text())
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
        self.close()
        
    def click_cancel(self):
#==================================================
#on clicking "cancel" in setup dialog box execute this code
#==================================================

        #exit setup dialog without saving values
        self.close()
        
    def get_values(self):
#==================================================
#returns the values that the user input to setup dialog box
#==================================================
        return [self.num_st,
                    self.num_cfreq,
                    self.num_span,
                    self.num_offset,
                    self.maxhold,
                    self.usesig]
                    
    def device_found(self,devices=[False,'Not Found','Not Found']):
#==================================================
#return wheter DMX and Spec Analyzer are found
#enables buttons for setup dialog
#==================================================
        print 'device update....'
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(True)#enable OK button
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(True)#enable Cancel button
        self.b_analyzer.setEnabled(True)#enable find device button
        self.b_analyzer.setText('Find Devices')#set find device button text
        
        #create a list of connected devices
        self.dev_connected=devices[0]
        
        #check length of device list and display 
        if len(devices)>1:
            self.e_rotator.setText(devices[1])#display if rotator is found
            self.e_specan.setText(devices[2])#display if spectrum analyzer is found