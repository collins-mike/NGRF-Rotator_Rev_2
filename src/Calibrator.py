'''
project: Rotator Rev2 
copyright 2017 NextGen RF Design
author Mike Collins
mike.collins@nextgenrf.com

the Calibrator class holds all calibration variables and initiates 
dialog boxes that are used to set specific calibration settings.
the calibration dialog boxes are created in the CalDialog.py file.

'''

import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import numpy as np

import math

import sip 
from CalDialog import CalDialog


class Calibrator(QWidget):
    def __init__(self,parent=None):
        #function and Variable Ddeclaration   
        super(Calibrator,self).__init__(parent)
        
        #=======================================================================
        # Setup calibration tab defaults
        #=======================================================================
        #worker
        self.worker=None
        
        #input
        self.cal_inputPwr=0#input to Tx in dB
        
        #antenna
        self.cal_txGain=0#tx antenna gain in dB
        self.cal_rxGain=0#rx antenna gain in dB
        
        self.cal_ampGain=0#input power to Tx
        #cable
        self.cal_cableLoss=0#gain loss due to cable in dB
        self.cal_txCableLoss=0
        self.cal_rxCableLoss=0
        #oats
        self.cal_dist=10#testing distance in m
        self.cal_fspl=0
        
        self.cal_freq=100#initial value for test frequency in MHz
        
        self.cal_additionalGain=0#user can add additional gain
        
        #configueAquisition
        self.cal_aq_detector="min-max"#data retrieval setting for signal hound
        self.cal_aq_scale="log-scale"#scaling type for data 
        #configureLevel
        self.cal_level_atten="auto"#attenuation setting for signal hound
        self.cal_level_ref=0#reference setting for signalhound attenuation
        #configure gain
        self.cal_gain='auto'#gain setting for signalhound
        #configureSweepCoupling
        self.cal_sc_rbw=10e3#resolution bandwidth setting
        self.cal_sc_vbw=10e3#video bandwidth setting
        self.cal_sc_sweepTime=0.025#sweep time setting
        self.cal_sc_rbwType="native"# resolution bandwidth type, see signal hound api-datasheet for details
        self.cal_sc_rejection="no-spur-reject"#spurious data rejection setting
        #configure center/ span
        self.cal_cp_center=100e6#sweep center frequency in Hz
        self.cal_cp_span=200e3#sweep span in Hz

        #addGainLoss dictionary hold any extra gain elements the user adds
        self.addGainLoss={}
             
    def calibrate_data(self,data):#calibrate collected data
        'Calibrate Collected Data'
        
        temp=(data-self.cal_inputPwr)#subtract input power in dBm
        
        temp=temp-self.cal_ampGain#subtract preamp gain
        
        temp=temp-self.cal_txCableLoss#subtract cable loss
        
        temp=temp-self.cal_txGain#Subtract DUT(Tx) antenna gain
        
        temp=temp-self.cal_fspl#subtract free space  loss
        
        temp=temp-self.cal_rxGain#Subtract Calibrated (Rx) antenna gain
                
        temp=temp-self.cal_rxCableLoss#subtract cable loss
        
        temp=temp-self.cal_additionalGain#subtract any additional gain/loss

        return temp

    def create_GUICal(self,tab):#create GUI Calibration Tab
        "Create Graphical User Interface that uses nodes for eay readability"
        
        
        tab.setStyleSheet(self.createStylesheet('calTab'))
        #=======================================================================
        # Setup images
        #=======================================================================
        img_antenna=QIcon('images/antenna-2.png')                       #antenna symbol
        img_arrow=QPixmap('images/rt_arrow.png')                        #right arrow
        img_sigGen=QIcon('images/circuit_signal-generator-512.png')     #signal generator symbol
        img_preAmp=QIcon('images/Amplifier_symbol.png')                 #amp symbol
        img_upArrow=QPixmap('images/up_arrow.png')                      #up arrow
        img_dnArrow=QPixmap('images/dn_arrow.png')                      #dn arrow
        img_omega=QIcon('images/cable.png')                             #signal generator symbol
        img_add=QIcon('images/add.png')                                 #signal generator symbol
        #=======================================================================
        # setup constants
        #=======================================================================
        BUTTON_LENGTH=36
        BUTTON_HEIGHT=36
        #=======================================================================
        # Create Signal Generator (InPut)
        #=======================================================================
        self.dia_sigGen=CalDialog(self,self.worker,'sigGen')
        
        inptBox=QGroupBox("Input Generator")
        inptBox.setParent(tab)
        inptBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        
        inptBoxLayout=QFormLayout()
        inptBox.setLayout(inptBoxLayout)
        #create button 
        b_sigGen=QPushButton('')
        b_sigGen.clicked.connect(lambda: self.on_guiSettings(self.dia_sigGen))
        b_sigGen.setToolTip("Adjust settings for Signal Generator") 
        b_sigGen.setIcon(img_sigGen)
        b_sigGen.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        inptBoxLayout.addWidget(b_sigGen)
        
        self.gui_inputPwr=QLabel(str(self.cal_inputPwr)+" dBm")
        inptBoxLayout.addRow(QLabel("Power: "),self.gui_inputPwr)
        
        
        #=======================================================================
        # Create PreAmp layout
        #=======================================================================
        
        self.dia_preAmp=CalDialog(self,self.worker,'amp')
        preampBox=QGroupBox("PreAmp")
        preampBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        preampBoxLayout=QFormLayout()
        preampBox.setLayout(preampBoxLayout)
        #create button 
        b_preAmp=QPushButton('')
        b_preAmp.clicked.connect(lambda: self.on_guiSettings(self.dia_preAmp))
        b_preAmp.setToolTip("Adjust settings for Preamplifier") 
        preampBoxLayout.addWidget(b_preAmp)
        b_preAmp.setIcon(img_preAmp)
        b_preAmp.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        
        #create labels
        self.gui_ampCalFreq=QLabel()
        preampBoxLayout.addRow(QLabel("Calibration Frequency: "),self.gui_ampCalFreq)
        
        self.gui_ampType=QLabel()
        preampBoxLayout.addRow(QLabel("Type: "),self.gui_ampType)
        self.gui_ampGain=QLabel(str(self.cal_ampGain)+" dB")
        preampBoxLayout.addRow(QLabel("Gain: "),self.gui_ampGain)
        
        
        
        #=======================================================================
        # create cable loss layout
        #=======================================================================
        
        self.dia_txCable=CalDialog(self,self.worker,"cable",'tx')
        txCableBox=QGroupBox("Tx Cable")
        txCableBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        txCableBoxLayout=QFormLayout()
        txCableBox.setLayout(txCableBoxLayout)
        #create buttons
        b_txCable=QPushButton('')
        b_txCable.clicked.connect(lambda: self.on_guiSettings(self.dia_txCable))
        b_txCable.setToolTip("Adjust settings for Tx Cable") 
        txCableBoxLayout.addWidget(b_txCable)
        b_txCable.setIcon(img_omega)
        b_txCable.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        
        self.gui_txCableCalFreq=QLabel()
        txCableBoxLayout.addRow(QLabel("Calibration Frequency: "),self.gui_txCableCalFreq)
        
        self.gui_txCableType=QLabel()
        txCableBoxLayout.addRow(QLabel("Type: "),self.gui_txCableType)
        
        self.gui_txCableLoss=QLabel(str(self.cal_cableLoss)+" dB")
        txCableBoxLayout.addRow(QLabel("Loss: "),self.gui_txCableLoss)
        
        
        #=======================================================================
        # create DUT layout
        #=======================================================================
        
        self.dia_tx=CalDialog(self,self.worker,'antenna','tx')
        txBox=QGroupBox("DUT")
        txBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        txBoxLayout=QFormLayout()
        txBox.setLayout(txBoxLayout)
        #create buttons
        b_tx=QPushButton('')
        b_tx.clicked.connect(lambda: self.on_guiSettings(self.dia_tx))
        b_tx.setToolTip("Adjust settings for Device Under Test") 
        txBoxLayout.addWidget(b_tx)
        b_tx.setIcon(img_antenna)
        b_tx.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        
        #create Qlabels
        self.gui_txCalFreq=QLabel()
        txBoxLayout.addRow(QLabel("Calibration Frequency: "),self.gui_txCalFreq)
        
        self.gui_txType=QLabel()
        txBoxLayout.addRow(QLabel("Type: "),self.gui_txType)
        
        self.gui_txGain=QLabel(str(self.cal_txGain)+" dB")
        txBoxLayout.addRow(QLabel("Gain: "),self.gui_txGain)
        
        
        #=======================================================================
        # Create FSPL Layout
        #=======================================================================
        
        self.dia_fspl=CalDialog(self,self.worker,'fspl')
        fsplpBox=QGroupBox("Free Space Path Loss")
        fsplpBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        fsplpBoxLayout=QFormLayout()
        fsplpBox.setLayout(fsplpBoxLayout)
        #create buttons
        b_FSPL=QPushButton('FSPL')
        b_FSPL.clicked.connect(lambda: self.on_guiSettings(self.dia_fspl))
        b_FSPL.setToolTip("Adjust settings for FSPL") 
        fsplpBoxLayout.addWidget(b_FSPL)
        self.gui_fspl=QLabel(str(self.cal_fspl)+" dB")
        fsplpBoxLayout.addRow(QLabel("FSPL: "),self.gui_fspl)
        
        #=======================================================================
        # create Calibrated Antenna layout
        #=======================================================================
        
        self.dia_rx=CalDialog(self,self.worker,'antenna','rx')
        rxBox=QGroupBox("Calibrated Antenna")
        rxBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        rxBoxLayout=QFormLayout()
        rxBox.setLayout(rxBoxLayout)
        #create buttons
        b_rx=QPushButton('')
        b_rx.clicked.connect(lambda: self.on_guiSettings(self.dia_rx))
        b_rx.setToolTip("Adjust settings for Calibrated Antenna") 
        b_rx.setIcon(img_antenna)
        b_rx.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        rxBoxLayout.addWidget(b_rx)
        #create Qlabels
        self.gui_rxCalFreq=QLabel()
        rxBoxLayout.addRow(QLabel("Calibration Frequency: "),self.gui_rxCalFreq)
        self.gui_rxType=QLabel()
        rxBoxLayout.addRow(QLabel("Type: "),self.gui_rxType)
        self.gui_rxGain=QLabel(str(self.cal_rxGain)+" dBi")
        rxBoxLayout.addRow(QLabel("Gain: "),self.gui_rxGain)
        
        
        #=======================================================================
        # create Rx cable loss layout
        #=======================================================================
        
        self.dia_rxCable=CalDialog(self,self.worker,'cable','rx')
        rxCableBox=QGroupBox("Rx Cable")
        rxCableBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        rxCableBoxLayout=QFormLayout()
        rxCableBox.setLayout(rxCableBoxLayout)
        #create buttons
        b_rxCable=QPushButton('')
        b_rxCable.clicked.connect(lambda: self.on_guiSettings(self.dia_rxCable))
        b_rxCable.setToolTip("Adjust settings for Rx Cable") 
        rxCableBoxLayout.addWidget(b_rxCable)
        b_rxCable.setIcon(img_omega)
        b_rxCable.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        
        #create Qlabels
        self.gui_rxCableCalFreq=QLabel()
        rxCableBoxLayout.addRow(QLabel("Calibration Frequency: "),self.gui_rxCableCalFreq)
        
        self.gui_rxCableType=QLabel()
        rxCableBoxLayout.addRow(QLabel("Type: "),self.gui_rxCableType)
        
        self.gui_rxCableLoss=QLabel(str(self.cal_cableLoss)+" dB")
        rxCableBoxLayout.addRow(QLabel("Loss: "),self.gui_rxCableLoss)
        
        
        #=======================================================================
        # create Additional Gain/loss layout
        #=======================================================================
        
        self.dia_additional=CalDialog(self,self.worker,'add')
        additionalBox=QGroupBox("Additional Gain/Loss")
        additionalBox.setStyleSheet(self.createStylesheet('gain'))#apply styling
        additionalBoxLayout=QFormLayout()
        additionalBox.setLayout(additionalBoxLayout)
        #create buttons
        b_add=QPushButton('')
        b_add.clicked.connect(lambda: self.on_guiSettings(self.dia_additional))
        b_add.setToolTip("Add/Remove additional Gain/Loss elements") 
        b_add.setIcon(img_add)
        b_add.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        additionalBoxLayout.addWidget(b_add)
        
        #create Qlabels
        self.gui_additional=QLabel(str(self.cal_cableLoss)+" dB")
        additionalBoxLayout.addRow(QLabel("Total Additional Loss/Gain: "),self.gui_additional)
        
        self.gui_additionalCnt=QLabel('0')
        additionalBoxLayout.addRow(QLabel("Number of Additional Elements: "),self.gui_additionalCnt)
        
        self.gui_addNames=QLabel('')
        self.gui_addGains=QLabel('')
        additionalBoxLayout.addRow(self.gui_addNames,self.gui_addGains)
        
        #=======================================================================
        # create spectrum analyzer layout
        #=======================================================================
        
        self.dia_specAn=CalDialog(self,self.worker,'specAn')#create dialog box for specAn
        
        specanBox=QGroupBox("Spectrum Analyzer")
        specanBox.setStyleSheet(self.createStylesheet('specan'))#apply styling
        specanBoxLayout=QFormLayout()
        specanBox.setLayout(specanBoxLayout)
        #create button NOTE: b_specan.setEnable() is called from parent
        self.b_specan=QPushButton('Spectrum Analyzer')
        self.b_specan.clicked.connect(lambda: self.on_guiSettings(self.dia_specAn))
        self.b_specan.setToolTip("Adjust settings for Spectrum Analyzer")
        self.b_specan.setEnabled(False) 
        specanBoxLayout.addWidget(self.b_specan)
        
        #create Qlabels
        self.gui_specan=QLabel(str(self.cal_rxGain))
        specanBoxLayout.addRow(QLabel("model: "),self.gui_specan)
        
        #=======================================================================
        # Create inner calibration form
        #=======================================================================
        innerCalBox=QGroupBox("Calibration Setup")
        innerCalBox.setStyleSheet(self.createStylesheet('setup'))#apply styling

        innerCalBoxLayout=QGridLayout()
        innerCalBox.setLayout(innerCalBoxLayout)
        #=======================================================================
        # create OATS Layout
        #=======================================================================
        oatsBox=QGroupBox('OATS')
        oatsBoxLayout=QFormLayout()
        
        self.e_cal_dist = QLineEdit('3')
        self.e_cal_dist.connect(self.e_cal_dist,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        oatsBoxLayout.addRow(QLabel("Testing Distance (m)"),self.e_cal_dist)
        oatsBox.setLayout(oatsBoxLayout)
        
        #=======================================================================
        # create Test Configuration Layout
        #=======================================================================
        configBox=QGroupBox('Test Configuration')
        configBoxLayout=QFormLayout()
        
        self.e_cal_freq = QLineEdit(str(self.cal_cp_center/1e6))
        self.e_cal_freq.connect(self.e_cal_freq,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        configBoxLayout.addRow(QLabel("Testing Frequency (MHz)"),self.e_cal_freq)
        
        #TODO add center/span functionality
        self.e_cal_cp_span= QLineEdit(str(self.cal_cp_span/1e6))
        self.e_cal_cp_span.connect(self.e_cal_cp_span,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        configBoxLayout.addRow(QLabel("Testing Frequency Span (MHz)"),self.e_cal_cp_span)
        
        self.e_cal_sc_sweepTime= QLineEdit(str(self.cal_sc_sweepTime*1000))
        self.e_cal_sc_sweepTime.connect(self.e_cal_sc_sweepTime,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        configBoxLayout.addRow(QLabel("sweep Time (ms)"),self.e_cal_sc_sweepTime)
        
        configBox.setLayout(configBoxLayout)
    
        #=======================================================================
        # create calibration equation layout
        #=======================================================================
        calEqBox=QGroupBox('Calibration Equation')
        calEqBoxLayout=QHBoxLayout()
        calEqBox.setStyleSheet(self.createStylesheet('eq'))#apply styling
        self.calFunctionAnswerDisplay=QLabel()
        
        self.calFunctionAnswerDisplay.setAlignment(Qt.AlignCenter)
        self.calFunctionAnswerDisplay.setMargin(10)   
        
        self.calFunctionDisplay=QLabel()
        self.calFunctionDisplay.setAlignment(Qt.AlignLeft)
        self.calFunctionDisplay.setMargin(4) 
        self.calFunctionDisplay.setWordWrap(True)
        
        calEqBoxLayout.addWidget(self.calFunctionDisplay)
        calEqBoxLayout.addWidget(self.calFunctionAnswerDisplay)
        
        calEqBox.setLayout(calEqBoxLayout)
        
        self.updateCalFunction()
        #=======================================================================
        # set up GUI Grid outer layout
        #=======================================================================
        
        grid=QGridLayout()#create main box of tab
        #signal generator
        grid.addWidget(inptBox,6,0)
        grid.addWidget(QLabel(pixmap=img_upArrow.scaledToHeight(24),alignment=Qt.AlignCenter),5,0)
        #preamp
        grid.addWidget(preampBox,4,0)
        grid.addWidget(QLabel(pixmap=img_upArrow.scaledToHeight(24),alignment=Qt.AlignCenter),3,0)
        #tx cable
        grid.addWidget(txCableBox,2,0)
        grid.addWidget(QLabel(pixmap=img_upArrow.scaledToHeight(24),alignment=Qt.AlignCenter),1,0)
        #tx antenna
        grid.addWidget(txBox,0,0)
        grid.addWidget(QLabel(pixmap=img_arrow.scaledToHeight(100),alignment=Qt.AlignCenter),0,1)
        #fspl
        grid.addWidget(fsplpBox,0,2)
        grid.addWidget(QLabel(pixmap=img_arrow.scaledToHeight(100),alignment=Qt.AlignCenter),0,3)
        #rx antenna
        grid.addWidget(rxBox,0,4)
        #rx cable
        grid.addWidget(QLabel(pixmap=img_dnArrow.scaledToHeight(24),alignment=Qt.AlignCenter),1,4)
        grid.addWidget(rxCableBox,2,4)
        #rx specan
        grid.addWidget(QLabel(pixmap=img_dnArrow.scaledToHeight(24),alignment=Qt.AlignCenter),3,4)
        grid.addWidget(additionalBox,4,4)
        #rx specan
        grid.addWidget(QLabel(pixmap=img_dnArrow.scaledToHeight(24),alignment=Qt.AlignCenter),5,4)
        grid.addWidget(specanBox,6,4)
        
        
        
        #=======================================================================
        # set up GUI Grid inner layout
        #=======================================================================
        grid.addWidget(innerCalBox,1,1,6,3)
        
        innerCalBoxLayout.addWidget(oatsBox,0,0)
        innerCalBoxLayout.addWidget(calEqBox,1,0,1,2)
        innerCalBoxLayout.addWidget(configBox,0,1)
        
        #resize grid layout for better readability
        grid.setColumnStretch(0,1)
        grid.setColumnStretch(1,1)
        grid.setColumnStretch(2,1)
        grid.setColumnStretch(3,1)
        grid.setColumnStretch(4,1)
        
        grid.setRowStretch(0,2)
        grid.setRowStretch(2,2)
        grid.setRowStretch(4,2)
        grid.setRowStretch(6,2)
        grid.setRowStretch(8,2)
        
        #apply layout to calibration tab
        tab.setLayout(grid)
        
    def on_guiSettings(self,dialog):#Execute one of the calibration dialog boxes
        "Run execute item specific dialog box"
        if dialog==self.dia_additional:
            dialog.tempDict=self.addGainLoss.copy()
            dialog.tempCalValue=self.cal_additionalGain
            #self.dia_additional.refreshAddElements()
            
        dialog.exec_()
               
    def create_calibrationTab(self,tab):#Create Calibration TAB
        "Create calibration tab form"
        #=======================================================================
        # create  main buttons
        #=======================================================================
        
        self.b_applyCal= QPushButton("&Apply Calibration")
        self.b_applyCal.setEnabled(False)
        self.connect(self.b_applyCal, SIGNAL('clicked()'), self.on_cal_apply)
        self.b_applyCal.setToolTip("Apply Calibration to Spectrum Analyzer")
        
        self.b_resetCal= QPushButton("&Reset Calibration")
        self.b_resetCal.setEnabled(False)
        self.connect(self.b_resetCal, SIGNAL('clicked()'), self.on_cal_reset)
        self.b_resetCal.setToolTip('reset calibration to default you must click Apply Calibration for these changes to be implemented on Spectrum Analyzer')

        
        
        
        #===============================================================================
        # create calibration form (fbox)
        # ==============================================================================
        hbox1=QHBoxLayout()#create box to hold left and right side of form
        

        #======================================================================
        # Left side Form
        #======================================================================

        fbox1 = QFormLayout()
                
        fbox1.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">OATS setup</span>'))#add heading
        
        self.e_cal_freq = QLineEdit(str(self.cal_freq))
        self.e_cal_freq.connect(self.e_cal_freq,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        fbox1.addRow(QLabel("Testing Frequency (MHz)"),self.e_cal_freq)
        
        self.e_cal_dist = QLineEdit('3')
        self.e_cal_dist.connect(self.e_cal_dist,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        fbox1.addRow(QLabel("Testing Distance (m)"),self.e_cal_dist)
        
        
        self.e_cal_fspl = QLineEdit(str(self.cal_fspl))
        self.e_cal_fspl.connect(self.e_cal_fspl,SIGNAL('returnPressed()'),self.on_cal_setFspl)
        self.e_cal_fspl.setEnabled(False)
        hbox=QHBoxLayout()
        hbox.addWidget(QLabel("FSPL (dB)"))
        self.cb_cal_fspl=QComboBox()
        self.cb_cal_fspl.addItem('Derived')
        self.cb_cal_fspl.addItem('Manual')
        self.cb_cal_fspl.currentIndexChanged.connect(self.on_cal_selectFsplMode)
        
        hbox.addWidget(self.cb_cal_fspl)
        hbox.addWidget(self.e_cal_fspl)
        fbox1.addRow(hbox)
        
        self.e_cal_inputPwr = QLineEdit('0')
        self.e_cal_inputPwr.connect(self.e_cal_inputPwr,SIGNAL('returnPressed()'),self.on_cal_setInputPwr)
        fbox1.addRow(QLabel("Tx Input Power (dBm)"),self.e_cal_inputPwr)
        #=================================
        # Center form/ Antenna Calibration
        #=================================
        
        fbox2 = QFormLayout()
        fbox2.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Tx Antenna</span>'))
        
        #=================================
        # calibrated Antenna selection buttons
        #=================================
        
        #create dictionaries to hold cal data
        self.cal_antFile={}#dictionary thats holds list of file names of calibrated antennas
        self.cal_antennaFreqGain={}#dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_antennaSel=QComboBox()#create combo box to select antenna
        self.cb_antennaSel.addItem('Manual')
        self.cb_antennaSel.setToolTip("Select Calibrated Antenna")
        self.cb_antennaSel.currentIndexChanged.connect(self.on_cal_selectAntenna)
        
        self.cb_antennaFreqSel=QComboBox()#create combo box to select antenna calibration frequency
        self.cb_antennaFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_antennaFreqSel.currentIndexChanged.connect(self.on_cal_selectAntennaGain)
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
                        self.cal_antFile[row[0]]='calibration/antennas/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox2.addRow('Antenna Type', self.cb_antennaSel)
        fbox2.addRow('Antenna calibration frequency (MHz)',self.cb_antennaFreqSel)
        
        #====================================
        # Manual gain line edit box
        #====================================
        self.e_cal_txGain = QLineEdit('0')
        self.e_cal_txGain.connect(self.e_cal_txGain,SIGNAL('returnPressed()'),self.on_cal_selectAntennaGain)
        fbox2.addRow(QLabel("Rx-Antenna Gain (dBi)"),self.e_cal_txGain)
                
        #=================================
        # calibrated PreAmp selection buttons
        #=================================
        fbox2.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Amplifier</span>'))
        
        #create dictionaries to hold cal data
        self.cal_ampFile={}#dictionary thats holds list of file names of calibrated antennas
        self.cal_ampFreqGain={}#dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_ampSel=QComboBox()#create combo box to select antenna
        self.cb_ampSel.addItem('Manual')
        self.cb_ampSel.setToolTip("Select Calibrated Antenna")
        self.cb_ampSel.currentIndexChanged.connect(self.on_cal_selectAmp)
        
        self.cb_ampFreqSel=QComboBox()#create combo box to select antenna calibration frequency
        self.cb_ampFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_ampFreqSel.currentIndexChanged.connect(self.on_cal_selectAmpGain)
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
                        self.cal_ampFile[row[0]]='calibration/preamps/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox2.addRow('Amplifier Type', self.cb_ampSel)
        fbox2.addRow('Amplifier calibration frequency (MHz)',self.cb_ampFreqSel)
        
        #====================================
        # Manual amplifier line edit boxes
        #====================================
          
        self.e_cal_ampGain = QLineEdit('0')
        self.e_cal_ampGain.connect(self.e_cal_ampGain,SIGNAL('returnPressed()'),self.on_cal_selectAmpGain)
        fbox2.addRow(QLabel("Amplifier Gain (dB)"),self.e_cal_ampGain)

        #=================================
        # calibrated Cable selection buttons
        #=================================
        fbox2.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Cable Loss</span>'))
        
        #create dictionaries to hold cal data
        self.cal_cableFile={}#dictionary thats holds list of file names of calibrated antennas
        self.cal_cableFreqGain={}#dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_cableSel=QComboBox()#create combo box to select antenna
        self.cb_cableSel.addItem('Manual')
        self.cb_cableSel.setToolTip("Select Calibrated Cable")
        self.cb_cableSel.currentIndexChanged.connect(self.on_cal_selectCable)
        
        self.cb_cableFreqSel=QComboBox()#create combo box to select antenna calibration frequency
        self.cb_cableFreqSel.setToolTip("Select Cable Calibration Frequency")
        self.cb_cableFreqSel.currentIndexChanged.connect(self.on_cal_selectCableLoss)
        self.cb_cableFreqSel.setEnabled(False)
        
        #==========================================
        # import list of cables from cables.csv
        #=========================================
        
        try:#import list of calibrated antennas from antennas.csv
            with open('calibration/cableList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_cableSel.addItem(row[0])
                        self.cal_cableFile[row[0]]='calibration/cables/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox2.addRow('Cable Type', self.cb_cableSel)
        fbox2.addRow('Cable calibration frequency (MHz)',self.cb_cableFreqSel)
        
        #====================================
        # Manual cable line edit boxes
        #====================================
          
        self.e_cal_cableLoss = QLineEdit('0')
        self.e_cal_cableLoss.connect(self.e_cal_cableLoss,SIGNAL('returnPressed()'),self.on_cal_selectCableLoss)
        fbox2.addRow(QLabel("Cable Loss (dB)"),self.e_cal_cableLoss)
        
        #=======================================================================
        # Aditional gain line edit
        #=======================================================================
        fbox2.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Additional Gain/Loss</span>'))
        self.e_cal_additionalGain = QLineEdit('0')
        self.e_cal_additionalGain.connect(self.e_cal_additionalGain,SIGNAL('returnPressed()'),self.on_cal_setAdditionalGain)
        fbox2.addRow(QLabel("Additional Gain (dB)"),self.e_cal_additionalGain)
        
        #=======================================================================
        # Right Side/SignaHound calibration Form
        #=======================================================================
        fbox3 = QFormLayout()

        fbox3.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">SignalHound BB60C\nSpectrum Analyzer</span>'))#add heading
        #RBW
        self.e_cal_sc_rbw  =QLineEdit('10')
        fbox3.addRow(QLabel("RBW (kHz)"),self.e_cal_sc_rbw)
        #VBW
        self.e_cal_sc_vbw  =QLineEdit('10')
        fbox3.addRow(QLabel("VBW (kHz)"),self.e_cal_sc_vbw)
        
        #Gain MAX=3 TODO: add automatic value correction
        hbox=QHBoxLayout()#create child hbox
        self.cb_autoGain = QCheckBox("Auto",checked=True)
        self.connect(self.cb_autoGain, SIGNAL('stateChanged(int)'), self.on_cal_autoGain)
        self.cb_autoGain.setToolTip("Set Automatic Gain Control")
        
        self.e_cal_gain=QLineEdit("0")
        self.e_cal_gain.setEnabled(False)
        
        hbox.addWidget(QLabel('Gain: Auto or 0-3'))
        hbox.addWidget(self.cb_autoGain)
        hbox.addWidget(self.e_cal_gain)
        fbox3.addRow(hbox)
        
        #Attenuation MAX=30 TODO: add automatic value correction
        hbox=QHBoxLayout()#create child hbox
        self.cb_autoAtten = QCheckBox("Auto",checked=True)
        self.connect(self.cb_autoAtten, SIGNAL('stateChanged(int)'), self.on_cal_autoAtten)
        self.cb_autoAtten.setToolTip("Set Automatic Attenuation Control")
        
        self.cb_cal_attenRef=QComboBox()
        self.cb_cal_attenRef.addItem('0')
        self.cb_cal_attenRef.addItem('10')
        self.cb_cal_attenRef.addItem('20')
        self.cb_cal_attenRef.addItem('30')
        self.cb_cal_attenRef.currentIndexChanged.connect(self.on_cal_autoAtten_ref)
        
        self.cb_cal_attenRef.setEnabled(True)
        
        self.e_cal_atten=QLineEdit("30")
        self.e_cal_atten.setEnabled(False)
        
        hbox.addWidget(QLabel('Attenuation:'))
        hbox.addWidget(self.cb_autoAtten)
        hbox.addWidget(QLabel('Reference (dB)'))
        hbox.addWidget(self.cb_cal_attenRef)
        hbox.addWidget(QLabel('Manual (dB)'))
        hbox.addWidget(self.e_cal_atten)
        fbox3.addRow(hbox)
        
        #Aquisition Detector type and scale
        hbox=QHBoxLayout()#create child hbox

        self.cb_cal_aqDet=QComboBox()
        self.cb_cal_aqDet.addItem('average')
        self.cb_cal_aqDet.addItem('min-max')
        self.cb_cal_aqDet.currentIndexChanged.connect(self.on_cal_detectorType)
        
        self.cb_cal_aqScale=QComboBox()
        self.cb_cal_aqScale.addItem('log-scale')
        self.cb_cal_aqScale.addItem('log-full-scale')
        self.cb_cal_aqScale.addItem('lin-scale')
        self.cb_cal_aqScale.addItem('lin-full-scale')
        self.cb_cal_aqScale.currentIndexChanged.connect(self.on_cal_scale)
        
        
        hbox.addWidget(QLabel('Acquisition:'))
        hbox.addWidget(QLabel('Detector Type'))
        hbox.addWidget(self.cb_cal_aqDet)
        hbox.addWidget(QLabel('Scale'))
        hbox.addWidget(self.cb_cal_aqScale)
        fbox3.addRow(hbox)
        
        #sweep coupling
        
        
        
        #=======================================================================
        # add calibration form to parent hbox1
        #=======================================================================
        
        hbox1.addLayout(fbox1)
        hbox1.addLayout(fbox2)
        hbox1.addLayout(fbox3)
        
        
        #=======================================================================
        # create button bar at bottom of app
        #=======================================================================
        hbox2 = QHBoxLayout()
        hbox2.addStretch()
        for w in [self.b_applyCal,self.b_resetCal]:
            hbox2.addWidget(w)
            hbox2.setAlignment(w, Qt.AlignVCenter)
        hbox2.addStretch()
          
        #=======================================================================
        # Create Calibration Function Display
        #=======================================================================
        
        self.calFunctionAnswerDisplay=QLabel()
        
        self.calFunctionAnswerDisplay.setAlignment(Qt.AlignCenter)
        self.calFunctionAnswerDisplay.setAutoFillBackground(True)
        p = self.calFunctionAnswerDisplay.palette()
        p.setColor(self.calFunctionAnswerDisplay.backgroundRole(), Qt.darkGreen)
        self.calFunctionAnswerDisplay.setPalette(p) 
        self.calFunctionAnswerDisplay.setMargin(10)   
        
        self.calFunctionDisplay=QLabel()
        self.calFunctionDisplay.setAlignment(Qt.AlignLeft)
        self.calFunctionDisplay.setAutoFillBackground(True)
        p = self.calFunctionDisplay.palette()
        p.setColor(self.calFunctionDisplay.backgroundRole(), Qt.darkGreen)
        self.calFunctionDisplay.setPalette(p) 
        self.calFunctionDisplay.setMargin(4) 
        self.calFunctionDisplay.setWordWrap(True)
        
        self.updateCalFunction()  
            
        #=======================================================================
        # assemble layout inside of vbox.cb
        #=======================================================================
        vbox = QVBoxLayout()#create layout     
        vbox.addLayout(hbox1)
        vbox.addStretch()
        vbox.addWidget(QLabel('<span style=" font-size:10pt; font-weight:600;">Calibration Function:</span>'))
        hbox=QHBoxLayout()
        hbox.addWidget(self.calFunctionDisplay)
        hbox.addWidget(self.calFunctionAnswerDisplay)
        vbox.addLayout(hbox)
        vbox.addStretch()
        vbox.addLayout(hbox2)#add control buttons to display
        
        #self.on_cal_setFspl()#call function to display correct FSPL
        
        tab.setLayout(vbox)#set layout of calibration tab        
        
    def updateCalFunction(self):#uipdate displayed calibration function
        "Update the Calibration equation shown in the calibration tab"
        self.calFunctionDisplay.setText('''<span style=" color:black; font-size:10pt; font-weight:300;">
                                            (Data)<br/> - ('''+str(self.cal_inputPwr)+ ''' dBm): Input Power<t/><br/>
                                            - ('''+str(self.cal_ampGain)+''' dB): PreAmpGain<br/>
                                            - ('''+str(self.cal_txCableLoss)+''' dB): Tx Cable Loss<br/>
                                            - ('''+str(self.cal_txGain)+''' dBi): DUT Gain<br/>
                                             - (''' +str(self.cal_fspl)+''' dB): FSPL<br/>
                                              - ('''+str(self.cal_rxGain)+''' dBi): Calibrated Antenna Gain<br/>
                                                - ('''+str(self.cal_rxCableLoss)+''' dB): Rx Cable_Loss<br/>
                                                 - ('''+str(self.cal_additionalGain)+''' dB): Addidtional_Gain</span>''')
        
        
        
        
        #=======================================================================
        # add "+" or "-" to total calibration display
        #=======================================================================
        if self.calibrate_data(0)>=0:
            self.calFunctionAnswerDisplay.setText('''<span style=" color:black; font-size:20pt; font-weight:1000;">
                                                        Total Calibration:<br/>   +'''+str(self.calibrate_data(0))+''' (dB)</span>''')
        else:       
            self.calFunctionAnswerDisplay.setText('''<span style=" color:black; font-size:20pt; font-weight:1000;">
                                                        Total Calibration:<br/>   '''+str(self.calibrate_data(0))+''' (dB)</span>''')
            
        #update displayed values of gain elements 
        self.gui_inputPwr.setText(str(self.cal_inputPwr)+" dBm")
        self.gui_ampGain.setText(str(self.cal_ampGain)+" dB")
        self.gui_txCableLoss.setText(str(self.cal_txCableLoss)+" dB")
        self.gui_txGain.setText(str(self.cal_txGain)+" dBi")
        self.gui_fspl.setText(str(self.cal_fspl)+" dB")
        self.gui_rxGain.setText(str(self.cal_rxGain)+" dBi")
        self.gui_rxCableLoss.setText(str(self.cal_rxCableLoss)+" dB")
        self.gui_additional.setText(str(self.cal_additionalGain)+" dB")
        
        #TODO: add a way to find specans model type
        self.gui_specan.setText("needs input")
          
    def on_cal_reset(self):#reset calibration settings to default
        "reset calibration setting to default"
        #antennas
        #cable
        self.cal_cableLoss=0
        #configueAquisition
        self.cal_aq_detector="average"#data retrieval setting for signal hound
        self.cal_aq_scale="log-scale"#scaling type for data 
        #configureLevel
        self.cal_level_atten=30#attenuation setting for signal hound
        self.cal_level_ref=0#reference setting for signalhound attenuation
        #configure gain
        self.cal_gain=0#gain setting for signalhound
        #configureSweepCoupling
        self.cal_sc_rbw=300e3#resolution bandwidth setting
        self.cal_sc_vbw=100e3#video bandwidth setting
        self.cal_sc_sweepTime=.25#sweep time setting
        self.cal_sc_rbwType="native"# resolution bandwidth type, see signal hound api-datasheet for details
        self.cal_sc_rejection="no-spur-reject"#spurious data rejection setting
        #configure center/ span
        self.cal_cp_center=100e6#sweep center frequency in Hz
        self.cal_cp_span=200e3#sweep span in Hz
     
    def on_cal_setFspl(self):#calculate or manually setFSPL 
        "Calculate FSPL and update frequency for automatic frequency selection"
        if str(self.dia_fspl.cb_cal_fspl.currentText())=='Manual':
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_fspl=float(self.dia_fspl.e_cal_fspl.text())
            self.cal_freq=float(self.e_cal_freq.text())
        else:
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_freq=float(self.e_cal_freq.text())
            self.cal_fspl= -(20*math.log10(self.cal_freq*1000000)+(20*math.log10(float(self.e_cal_dist.text())))+20*math.log10((4*np.pi)/299792458))       
            self.dia_fspl.e_cal_fspl.setText(str(self.cal_fspl))

        self.updateAutoFrequencies()#update all automatically calibrated frequencies        
        self.updateCalFunction()
 
    def updateAutoFrequencies(self):#update frequency for calibration elements that are set to "auto"
        'Update the values of calibrated elements to correct gain at currently selected test frequency'
        self.dia_preAmp.on_cal_selectAmpGain()
        self.dia_tx.on_cal_selectAntennaGain()
        self.dia_txCable.on_cal_selectCableLoss()
        self.dia_rxCable.on_cal_selectCableLoss()
        self.dia_rx.on_cal_selectAntennaGain()
        
        self.gui_ampCalFreq.setText(str(self.dia_preAmp.calFreq))
        self.gui_txCableCalFreq.setText(str(self.dia_txCable.calFreq))
        self.gui_txCalFreq.setText(str(self.dia_tx.calFreq))
        self.gui_rxCalFreq.setText(str(self.dia_rx.calFreq))
        self.gui_rxCableCalFreq.setText(str(self.dia_rxCable.calFreq))
        #self.on_cal_selectAmpGain()
        #self.on_cal_selectAntennaGain()
        #self.on_cal_selectCableLoss()
 
    def on_cal_selectFsplMode(self):#set manual or derived mode for FSPL Loss
        'set FSPL mode to either manual or derived'
        if str(self.cb_cal_fspl.currentText())=='Manual':
            self.e_cal_fspl.setEnabled(True)
            self.on_cal_setFspl()
        else:
            self.e_cal_fspl.setEnabled(False)
            self.on_cal_setFspl() 
        
        self.updateCalFunction()
             
    def on_cal_apply(self):# apply calibration settings TODO: add class all calibration parameters to this function 
        'apply calibration settings to specturm alalyzer'
        
        #TODO: add automatic parameter correction in case of user error
        
        #=======================================================================
        # set calibration variables
        #=======================================================================
        #=======================================================================
        # #cable loss
        # self.cal_rcableLoss=float(self.e_cal_cableLoss.text())
        # #distance
        # self.cal_dist=float(self.e_cal_dist.text())
        # #antenna
        # self.cal_txGain=float(self.e_cal_txGain.text())
        # #input power
        # self.cal_ampGain=float(self.e_cal_ampGain.text())
        # #FSPL
        # self.cal_fspl=float(self.e_cal_fspl.text())
        #=======================================================================
        
        
        #=======================================================================
        # send calibration to signal hound
        #=======================================================================
        #gain
        if self.dia_specAn.cb_autoGain.isChecked():
            self.cal_gain='auto'
        else:
            #if user sets gain >3 it will be automatically corrected to 3
            if float(self.dia_specAn.e_cal_gain.text())>3:
                self.dia_specAn.e_cal_gain=3
                self.cal_gain=3
            else:
                self.cal_gain=int(self.dia_specAn.e_cal_gain.text())
        self.worker.specan.sh.configureGain(self.cal_gain)#set gain in specan
        
        #attenuation
        if self.dia_specAn.cb_autoAtten.isChecked():
            self.cal_level_atten="auto"
        else:
            self.cal_level_atten=float(self.dia_specAn.e_cal_atten.text())
            
        self.worker.specan.sh.configureLevel(self.cal_level_ref , self.cal_level_atten)#set attenuation in specan
        
        #log or linear units
        self.worker.specan.sh.configureProcUnits("log")
        
        #data units
        self.worker.specan.sh.configureAcquisition(str(self.cal_aq_detector),str(self.cal_aq_scale))
        self.worker.specan.sh.configureSweepCoupling((int(self.dia_specAn.e_cal_sc_rbw.text()))*1000,(int(self.dia_specAn.e_cal_sc_vbw.text()))*1000,0.1,"native","spur-reject") 
        
        self.updateCalFunction()
        
    def on_cal_autoGain(self):#toggle auto-gain settings
        'toggle auto attenuation setting'
        
        if self.dia_specAn.cb_autoGain.isChecked():
            print "Gain set to AUTO"
            self.cal_gain='auto'
            self.dia_specAn.e_cal_gain.setEnabled(False)
        else:
            print "Gain set to ManuaL"
            self.dia_specAn.e_cal_gain.setEnabled(True)
        self.updateCalFunction()
        
    def on_cal_autoAtten(self):#toggle auto-gain settings
        'Toggle Auto-Attenuation setting'
        if self.dia_specAn.cb_autoAtten.isChecked():
            print "Attenuation set to Auto"
            self.cal_level_atten='auto'
            self.dia_specAn.e_cal_atten.setEnabled(False)
            self.dia_specAn.cb_cal_attenRef.setEnabled(True)
        else:
            print "Attenuation set to Manual"
            self.dia_specAn.e_cal_atten.setEnabled(True)
            self.dia_specAn.cb_cal_attenRef.setEnabled(False)
        self.updateCalFunction()
            
    def on_cal_autoAtten_ref(self):#set reference for auto attenuation
        'set reference value for auto attenuation'
        
        self.cal_level_ref=int(self.dia_specAn.cb_cal_attenRef.currentText())
        print "Attenuation reference set to " + str(self.cal_level_ref)

    def on_cal_detectorType(self):#set detector type for acquisition
        'set spectrum analyzer detector type'
        self.cal_aq_detector=self.dia_specAn.cb_cal_aqDet.currentText()
        print "Aquisition detector type set to " + str(self.cal_aq_detector)
  
    def on_cal_setInputPwr(self):#set input power for calibration
        'Set input power for calibration'
        self.cal_inputPwr=float(self.dia_sigGen.e_cal_inputPwr.text())
        
        self.updateCalFunction()
  
    def get_bestValue(self,gainDict):#get closest value to selected test frequency
        'get closest value to selected test frequency, if value is between to frequencies the frequency with the highest gain will be chosen'
        
        bestVal=9999999#set very high initial value to be replaced on first iteration
        
        #iterate through all values in gain dictionary and test against current best value
        for freq in sorted(gainDict):
            if abs(int(freq)-self.cal_freq)<abs((int(bestVal)-self.cal_freq)):#if (current frequency)-(test frequency)<(best value)-(test frequency)
                bestVal=freq
            elif abs(int(freq)-self.cal_freq)==abs((int(bestVal)-self.cal_freq)):#if (current frequency)-(test frequency)==(best value)-(test frequency): get frequency with higher gain
                
                if gainDict[str(freq)]>=gainDict[str(int(bestVal))]:
                    bestVal=freq
        return int(bestVal)
    
        '''  
    def on_cal_selectAntenna(self):#import Calibrated antenna info
        
        currentAnt=self.cb_antennaSel.currentText()
        print "Calibrated Antenna Set to " + currentAnt
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_antennaFreqSel.clear()
        self.cal_antennaFreqGain.clear()
        
        #insert a blank space as default value
        self.cb_antennaFreqSel.addItem("")
        
        
        #populate 
        if self.cb_antennaSel.currentText()!='Manual':
            self.e_cal_txGain.setEnabled(False)
            self.cb_antennaFreqSel.setEnabled(True)
            try:
                with open(self.cal_antFile[str(currentAnt)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    
                    skipHeader=True
                    self.cb_antennaFreqSel.addItem('Auto')
                    
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_antennaFreqGain[row[0]]=row[1];
                            
                            self.cb_antennaFreqSel.addItem(row[0])
                            
                        skipHeader=False
                csvFile.close()
                
            except:
                print "Exception when attempting to open "+self.cal_antFile[str(currentAnt)]
        else:
            self.e_cal_txGain.setEnabled(True)
            self.cb_antennaFreqSel.setEnabled(False)
            
        self.updateCalFunction()
        
    def on_cal_selectAntennaGain(self):#select calibration Gain for antenna
        if self.cb_antennaFreqSel.currentText()!='Manual':
            
            if str(self.cb_antennaFreqSel.currentText())=='Auto':#if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_antennaFreqGain)
                
                self.cal_txGain=float(self.cal_antennaFreqGain[str(int(bestVal))])
                
                self.e_cal_txGain.setText(str(self.cal_txGain))
                
                
                print "Antenna Calibration frequency set to " + str(int(bestVal)) + "MHz"
                
            else:              
                currentFreq=str(self.cb_antennaFreqSel.currentText())#hold selected frequency
                
                if currentFreq in self.cal_antennaFreqGain:
                    
                    print "Antenna Calibration frequency set to "+ currentFreq+ "MHz"
                    self.cal_txGain=float(self.cal_antennaFreqGain[currentFreq])
                    self.e_cal_txGain.setText(str(self.cal_txGain))
                else:
                    self.cal_txGain=float(self.e_cal_txGain.text())
        else:
            self.cal_txGain=float(self.e_cal_txGain.text())       
               
        self.updateCalFunction()
        
    def on_cal_selectAmp(self):#import Calibrated Amplifier info
        
        currentAmp=self.cb_ampSel.currentText()
        print "Calibrated Antenna Set to " + currentAmp
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_ampFreqSel.clear()
        self.cal_ampFreqGain.clear()
        
        self.cb_ampFreqSel.addItem("")
        
        if self.cb_ampSel.currentText()!='Manual':
            self.e_cal_ampGain.setEnabled(False)
            self.cb_ampFreqSel.setEnabled(True)
            try:
                with open(self.cal_ampFile[str(currentAmp)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    self.cb_ampFreqSel.addItem('Auto')#add auto select frequency
                    
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_ampFreqGain[row[0]]=row[1];
                            
                            self.cb_ampFreqSel.addItem(row[0])
                            
                        skipHeader=False
                csvFile.close()
                
            except:
                print "Exception when attempting to open "+self.cal_antFile[str(currentAmp)]
        else:
            self.e_cal_ampGain.setEnabled(True)
            self.cb_ampFreqSel.setEnabled(False)
        
        self.updateCalFunction()
        
    def on_cal_selectAmpGain(self):  # select calibration Gain for amplifier
        
        if self.cb_ampSel.currentText()!='Manual':
            if str(self.cb_ampFreqSel.currentText())=='Auto':#if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_ampFreqGain)
                
                self.cal_ampGain=float(self.cal_ampFreqGain[str(int(bestVal))])
                
                self.e_cal_ampGain.setText(str(self.cal_ampGain))
                
                
                print "Amplifier Calibration frequency set to " + str(int(bestVal)) + "MHz"
        
            else:
            
                currentFreq=str(self.cb_ampFreqSel.currentText())
                
                if currentFreq in self.cal_ampFreqGain:
                    
                    print "Amplifier Calibration frequency set to "+ currentFreq+ "MHz"
                    self.cal_ampGain=float(self.cal_ampFreqGain[currentFreq])
                    self.e_cal_ampGain.setText(str(self.cal_ampGain))
        else:
            self.cal_ampGain=float(self.e_cal_ampGain.text())
        self.updateCalFunction()
        
    def on_cal_selectCable(self):#import Calibrated cable info
        
        currentCable=self.cb_cableSel.currentText()
        print "Calibrated Cable Set to " + currentCable
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_cableFreqSel.clear()
        self.cal_cableFreqGain.clear()
        
        self.cb_cableFreqSel.addItem("")
        
        if self.cb_cableSel.currentText()!='Manual':
            self.e_cal_cableLoss.setEnabled(False)
            self.cb_cableFreqSel.setEnabled(True)
            try:
                with open(self.cal_cableFile[str(currentCable)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    self.cb_cableFreqSel.addItem('Auto')#add auto select frequency option
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_cableFreqGain[row[0]]=row[1];
                            
                            self.cb_cableFreqSel.addItem(row[0])
                            
                        skipHeader=False
                csvFile.close()
                
            except:
                print "Exception when attempting to open "+self.cal_cableFile[str(currentCable)]
        else:
            self.e_cal_cableLoss.setEnabled(True)
            self.cb_cableFreqSel.setEnabled(False)
        self.updateCalFunction()
    
    def on_cal_selectCableLoss(self):#select calibration Loss for Cable
        
        if self.cb_cableSel.currentText()!='Manual':
            if str(self.cb_cableFreqSel.currentText())=='Auto':#if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_cableFreqGain)
                
                self.cal_cableLoss=float(self.cal_cableFreqGain[str(int(bestVal))])
                
                self.e_cal_cableLoss.setText(str(self.cal_cableLoss))
                
                
                print "Cable Calibration frequency set to " + str(int(bestVal)) + " MHz"
                print '\tCable Loss set to '+str(self.cal_cableFreqGain[str(int(bestVal))]) + " dB"
        
            else:
                currentFreq=str(self.cb_cableFreqSel.currentText())
                
                if currentFreq in self.cal_cableFreqGain:
                    
                    print "Cable Calibration frequency set to "+ currentFreq+ " MHz"
                    print '\tCable Loss set to '+str(self.cal_cableFreqGain[currentFreq]) + " dB"
                    self.cal_cableLoss=float(self.cal_cableFreqGain[currentFreq])
                    self.e_cal_cableLoss.setText(str(self.cal_cableLoss))
        else:
            self.cal_cableLoss=float(self.e_cal_cableLoss.text())
        self.updateCalFunction()
        '''
        
    def on_cal_scale(self):#set detector type for acquisition
        'set acquisition scaling in spectrum alalyzer'
        
        self.cal_aq_scale=self.cb_cal_aqScale.currentText()
        print "Aquisition scale set to " + str(self.cal_aq_scale)
        self.updateCalFunction()
        
    def createStylesheet(self,style):
        'set style for GUI elements'
        if style=='gain':
            retval="""
                    QGroupBox { 
                        background-color: rgb(91, 194, 255);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        if style=='fspl':
            retval="""
                    QGroupBox { 
                        background-color: rgb(74, 162, 214);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='specan':
            retval="""
                    QGroupBox { 
                        background-color: rgb(255, 84, 84);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='source':
            retval="""
                    QGroupBox { 
                        background-color: rgb(255, 146, 84);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='rx/tx':
            retval="""
                    QGroupBox { 
                        background-color: rgb(77, 157, 204);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='setup':
            retval="""
                    QGroupBox { 
                        background-color: rgb(198, 198, 198);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='eq':
            retval="""
                    QGroupBox { 
                        background-color: rgb(31, 150, 18);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='calTab':
            retval="""
                     QTabBar::tab:selected {
                         background: gray;}
                     QTabWidget>QWidget>QWidget{
                         background: rgb(142, 142, 142);}
                    """
        return retval

    
    
