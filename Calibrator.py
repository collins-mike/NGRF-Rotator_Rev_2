'''
project: Rotator Rev2 
copyright 2017 NextGen RF Design
author Mike Collins
mike.collins@nextgenrf.com

the Calibrator class holds all calibration variables and initiates 
dialog boxes that are used to set specific calibration settings.
the calibration dialog boxes are created in the CalDialog.py file.

calibrator object also sets and holds  all settings for the spectrum 
analyzer

'''

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import numpy as np

import math

from CalDialog import CalDialog

#===============================================================================
# Constants
#===============================================================================

#TABSTATE set the available calibration elements

TABSTATE_PATTERN    = 0
TABSTATE_EMC        = 1
TABSTATE_NONE       = 2



class Calibrator(QWidget):
    def __init__(self,parent=None):
        #function and Variable Ddeclaration   
        super(Calibrator,self).__init__(parent)
        
        #=======================================================================
        # Setup calibration tab defaults
        #=======================================================================
        #worker
        self.worker=None
        #setup
        self.setup=None
        
        #mainForm
        self.mainForm=None
        #input
        self.cal_inputPwr=0                     #input to Tx in dB
        
        #Tab State variables
        self.tabState = TABSTATE_PATTERN
        
        #antenna
        self.cal_txGain      = 0                       #tx antenna gain in dB
        self.cal_rxGain      = 0                       #rx antenna gain in dB
        self.cal_antDiameter = 0.2413                   #set rx diameter to measure far field
        
        self.cal_ampGain=0                      #input power to Tx
        #cable
        self.cal_cableLoss=0                    #gain loss due to cable in dB
        self.cal_txCableLoss=0
        self.cal_rxCableLoss=0
        #test config
        self.cal_dist=10                        #testing distance in m
        self.cal_fspl=0
        self.cal_staticCable=False
        self.cal_freq=100e6                     #initial value for test frequency in MHz
        self.cal_span=200e3                     #sweep span in Hz
        self.cal_additionalGain=0               #user can add additional gain
        
        #configueAquisition
        self.cal_aq_detector="min-max"          #data retrieval setting for signal hound
        self.cal_aq_scale="log-scale"           #scaling type for data 
        #configureLevel
        self.cal_level_atten="auto"             #attenuation setting for signal hound
        self.cal_level_ref=0                    #reference setting for signalhound attenuation
        #configure gain
        self.cal_gain='auto'                    #gain setting for signalhound
        #configureSweepCoupling
        self.cal_sc_rbw=10e3                    #resolution bandwidth setting
        self.cal_sc_vbw=10e3                    #video bandwidth setting
        self.cal_sc_sweepTime=0.025             #sweep time setting
        self.cal_sc_rbwType="native"            #resolution bandwidth type, see signal hound api-datasheet for details
        self.cal_sc_rejection="no-spur-reject"  #spurious data rejection setting


        #test informations
        self.cal_tester=''                      #testors name
        self.cal_customer=''                    #customer's name
        self.cal_comments=''                    #comments
        self.cal_dutLabel=''                    #label of DUT
        self.cal_dutSN=''                       #serial number of DUT
        self.cal_orientation=''                  #Orientation of RX antenna
        
        self.CAL_NUM_ARRAY=[]
        #addGainLoss dictionary hold any extra gain elements the user adds
        self.addGainLoss={}
         
    def set_tabState(self):
        #=======================================================================
        #
        #          Name:    set_tabState
        #
        #    Parameters:    None    
        #
        #        Return:    None
        #
        #   Description:    this functions set the current tab state for the 
        #                    calibration tab. the tab state corresponds to the current test type
        #                    and is used to enable/diable functionality depending on the test's use
        #
        #=======================================================================
        
        #=======================================================================
        # No Calibration
        #=======================================================================
        if (self.cb_tabState.currentIndex()==TABSTATE_NONE):  
            
            #set tab state
            self.tabState=TABSTATE_NONE
            
            #Zero out calibration elements
            self.dia_sigGen.e_cal_inputPwr.setText('0')
            self.dia_sigGen.click_ok()
            
            self.dia_preAmp.cb_ampSel.setCurrentIndex(0)
            self.dia_preAmp.e_cal_ampGain.setText('0')
            self.dia_preAmp.click_ok()
            
            self.dia_txCable.cb_cableSel.setCurrentIndex(0)
            self.dia_txCable.e_cal_cableLoss.setText('0')
            self.dia_txCable.click_ok()
            
            self.dia_tx.cb_antennaSel.setCurrentIndex(0)
            self.dia_tx.e_cal_AntGain.setText('0')
            self.dia_tx.click_ok()
            
            self.dia_rx.cb_antennaSel.setCurrentIndex(0)
            self.dia_rx.e_cal_AntGain.setText('0')
            self.dia_rx.click_ok()
            
            self.dia_rxCable.cb_cableSel.setCurrentIndex(0)
            self.dia_rxCable.e_cal_cableLoss.setText('0')
            self.dia_rxCable.click_ok()
            
            self.update_calibration(True)
            
            self.cal_fspl=0;
            self.update_displayValues()
            
            #Enable/Disable setup buttons
            self.b_sigGen.setEnabled(False)
            self.b_preAmp.setEnabled(False)
            self.b_txCable.setEnabled(False)
            self.b_tx.setEnabled(False)
            self.b_FSPL.setEnabled(False)
            self.b_rx.setEnabled(False)
            self.b_rxCable.setEnabled(False)
            self.b_add.setEnabled(False)
            
            #Enable/Disable test config text boxes
            self.e_cal_span.setEnabled(True)
            self.e_cal_span.setText(str(self.cal_span/1e6))
            
            self.e_cal_sc_sweepTime.setEnabled(True)
            self.e_cal_sc_sweepTime.setText(str(self.cal_sc_sweepTime*1e3))
            
            self.e_cal_freq.setEnabled(True)
            self.e_cal_freq.setText(str(self.cal_freq/1e6))
            
            self.gui_fspl.setText(str(self.cal_fspl)+" dB")
            
           
            
            
            
            
            
            
            
        #=======================================================================
        # Radiation Pattern Testing
        #=======================================================================
        if (self.cb_tabState.currentIndex()==TABSTATE_PATTERN): 
            self.tabState=TABSTATE_PATTERN
            
            #Enable/Disable setup buttons
            self.b_sigGen.setEnabled(True)
            self.b_preAmp.setEnabled(True)
            self.b_txCable.setEnabled(True)
            self.b_tx.setEnabled(True)
            self.b_FSPL.setEnabled(True)
            self.b_rx.setEnabled(True)
            self.b_rxCable.setEnabled(True)
            self.b_add.setEnabled(True)
            
            #Enable/Disable test config text boxes
            self.e_cal_span.setEnabled(True)
            self.e_cal_span.setText(str(self.cal_span/1e6))
            
            self.e_cal_sc_sweepTime.setEnabled(True)
            self.e_cal_sc_sweepTime.setText(str(self.cal_sc_sweepTime*1e3))
            
            self.e_cal_freq.setEnabled(True)
            self.e_cal_freq.setText(str(self.cal_freq/1e6))
            
            self.set_fspl()
            self.gui_fspl.setText(str(self.cal_fspl)+" dB")
            self.update_displayValues()
            
            
            
        #=======================================================================
        # EMC Pre-Compliance
        #=======================================================================
        if (self.cb_tabState.currentIndex()==TABSTATE_EMC): 
            self.tabState=TABSTATE_EMC
            self.cal_fspl=0;
            self.update_displayValues()
            
            #Zero out calibration elements
            self.dia_sigGen.e_cal_inputPwr.setText('0')
            self.dia_sigGen.click_ok()
            
            self.dia_preAmp.cb_ampSel.setCurrentIndex(0)
            self.dia_preAmp.e_cal_ampGain.setText('0')
            self.dia_preAmp.click_ok()
            
            self.dia_txCable.cb_cableSel.setCurrentIndex(0)
            self.dia_txCable.e_cal_cableLoss.setText('0')
            self.dia_txCable.click_ok()
            
            self.dia_tx.cb_antennaSel.setCurrentIndex(0)
            self.dia_tx.e_cal_AntGain.setText('0')
            self.dia_tx.click_ok()
            
            self.update_calibration(True)

            self.update_displayValues()
            
            #Enable/Disable setup buttons
            self.b_sigGen.setEnabled(False)
            self.b_preAmp.setEnabled(False)
            self.b_txCable.setEnabled(False)
            self.b_tx.setEnabled(False)
            self.b_FSPL.setEnabled(False)
            self.b_rx.setEnabled(True)
            self.b_rxCable.setEnabled(True)
            self.b_add.setEnabled(True)
            
            #Enable/Disable test config text boxes
            self.e_cal_span.setEnabled(False)
            self.e_cal_span.setText("Auto")
            
            self.e_cal_sc_sweepTime.setEnabled(False)
            self.e_cal_sc_sweepTime.setText("Auto")
            
            self.e_cal_freq.setEnabled(False)
            self.e_cal_freq.setText("Auto")
            
            self.gui_fspl.setText("Auto")
            
        
            
                    
    def create_calibrationTab(self,tab):#create Calibration Tab GUI
        #=======================================================================
        #
        #          Name:    create_calibrationTab
        #
        #    Parameters:    tab (pointer to tab object) 
        #
        #        Return:    None
        #
        #   Description:    creates form and user interface of calibration tab object
        #
        #=======================================================================
        "Create Graphical User Interface that uses nodes for eay readability"
        
        
        tab.setStyleSheet(self.create_styleSheet('calTab'))
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
        # create tab state selection radio buttons
        #=======================================================================
        tabStateLayout=QHBoxLayout()
        
        self.cb_tabState=QComboBox()
        self.cb_tabState.addItem("Radiation Pattern")
        self.cb_tabState.addItem("EMC Pre-Compliance")
        self.cb_tabState.addItem("No Calibration")
        self.cb_tabState.currentIndexChanged.connect(self.set_tabState)
        
        tabStateLayout.addStretch()
        tabStateLayout.addWidget(QLabel('<span style=" color:#000000; font-size:12pt; font-weight:200;">Test Type</span>'))
        tabStateLayout.addWidget(self.cb_tabState)
        tabStateLayout.addStretch()
        
        #=======================================================================
        # Create Signal Generator (InPut)
        #=======================================================================
        self.dia_sigGen=CalDialog(self,self.worker,'sigGen')
        
        inptBox=QGroupBox("Input Generator")
        inptBox.setParent(tab)
        inptBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        
        inptVBoxLayout=QVBoxLayout()
        inptBoxLayout=QFormLayout()
        inptBox.setLayout(inptVBoxLayout)
        #create button 
        self.b_sigGen=QPushButton('')
        self.b_sigGen.clicked.connect(lambda: self.execute_calDialogBox(self.dia_sigGen))
        self.b_sigGen.setToolTip("Adjust settings for Signal Generator") 
        self.b_sigGen.setIcon(img_sigGen)
        self.b_sigGen.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        inptVBoxLayout.addWidget(self.b_sigGen)
        inptVBoxLayout.addLayout(inptBoxLayout)
        
        self.gui_inputPwr=QLabel(str(self.cal_inputPwr)+" dBm")
        inptBoxLayout.addRow(QLabel("Power: "),self.gui_inputPwr)
        
        
        #=======================================================================
        # Create PreAmp layout
        #=======================================================================
        
        self.dia_preAmp=CalDialog(self,self.worker,'amp')
        preampBox=QGroupBox("PreAmp")
        preampBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        preampVBoxLayout=QVBoxLayout()
        preampBoxLayout=QFormLayout()
        preampBox.setLayout(preampVBoxLayout)
        #create button 
        self.b_preAmp=QPushButton('')
        self.b_preAmp.clicked.connect(lambda: self.execute_calDialogBox(self.dia_preAmp))
        self.b_preAmp.setToolTip("Adjust settings for Preamplifier") 
        self.b_preAmp.setIcon(img_preAmp)
        self.b_preAmp.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        preampVBoxLayout.addWidget(self.b_preAmp)
        preampVBoxLayout.addLayout(preampBoxLayout)
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
        txCableBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        txCableVBoxLayout=QVBoxLayout()
        txCableBoxLayout=QFormLayout()
        txCableBox.setLayout(txCableVBoxLayout)
        #create buttons
        self.b_txCable=QPushButton('')
        self.b_txCable.clicked.connect(lambda: self.execute_calDialogBox(self.dia_txCable))
        self.b_txCable.setToolTip("Adjust settings for Tx Cable") 
        self.b_txCable.setIcon(img_omega)
        self.b_txCable.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        txCableVBoxLayout.addWidget(self.b_txCable)
        txCableVBoxLayout.addLayout(txCableBoxLayout)
        
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
        txBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        txVBoxLayout=QVBoxLayout()
        txBoxLayout=QFormLayout()
        txBox.setLayout(txVBoxLayout)
        #create buttons
        self.b_tx=QPushButton('')
        self.b_tx.clicked.connect(lambda: self.execute_calDialogBox(self.dia_tx))
        self.b_tx.setToolTip("Adjust settings for Device Under Test") 
        self.b_tx.setIcon(img_antenna)
        self.b_tx.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        txVBoxLayout.addWidget(self.b_tx)
        txVBoxLayout.addLayout(txBoxLayout)
        
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
        fsplpBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        fsplpVBoxLayout=QVBoxLayout()
        fsplpBoxLayout=QFormLayout()
        fsplpBox.setLayout(fsplpVBoxLayout)
        #create buttons
        self.b_FSPL=QPushButton('FSPL')
        self.b_FSPL.clicked.connect(lambda: self.execute_calDialogBox(self.dia_fspl))
        self.b_FSPL.setToolTip("Adjust settings for FSPL") 
        fsplpVBoxLayout.addWidget(self.b_FSPL)
        fsplpVBoxLayout.addLayout(fsplpBoxLayout)
        
        self.gui_fsplMode=QLabel(str(self.dia_fspl.cb_cal_fspl.currentText()))
        fsplpBoxLayout.addRow(QLabel("Mode: "),self.gui_fsplMode)
        
        self.gui_fspl=QLabel(str(self.cal_fspl)+" dB")
        fsplpBoxLayout.addRow(QLabel("FSPL: "),self.gui_fspl)
        
        #=======================================================================
        # create Calibrated Antenna layout
        #=======================================================================
        
        self.dia_rx=CalDialog(self,self.worker,'antenna','rx')
        rxBox=QGroupBox("Calibrated Antenna")
        rxBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        rxVBoxLayout=QVBoxLayout()
        rxBoxLayout=QFormLayout()
        rxBox.setLayout(rxVBoxLayout)
        #create buttons
        self.b_rx=QPushButton('')
        self.b_rx.clicked.connect(lambda: self.execute_calDialogBox(self.dia_rx))
        self.b_rx.setToolTip("Adjust settings for Calibrated Antenna") 
        self.b_rx.setIcon(img_antenna)
        self.b_rx.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        rxVBoxLayout.addWidget(self.b_rx)
        rxVBoxLayout.addLayout(rxBoxLayout)
        
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
        rxCableBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        rxCableVBoxLayout=QVBoxLayout()
        rxCableBoxLayout=QFormLayout()
        rxCableBox.setLayout(rxCableVBoxLayout)
        #create buttons
        self.b_rxCable=QPushButton('')
        self.b_rxCable.clicked.connect(lambda: self.execute_calDialogBox(self.dia_rxCable))
        self.b_rxCable.setToolTip("Adjust settings for Rx Cable") 
        self.b_rxCable.setIcon(img_omega)
        self.b_rxCable.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        rxCableVBoxLayout.addWidget(self.b_rxCable)
        rxCableVBoxLayout.addLayout(rxCableBoxLayout)
        
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
        additionalBox.setStyleSheet(self.create_styleSheet('gain'))#apply styling
        additionalVBoxLayout=QVBoxLayout()
        additionalBoxLayout=QFormLayout()
        additionalBox.setLayout(additionalVBoxLayout)
        #create buttons
        self.b_add=QPushButton('')
        self.b_add.clicked.connect(lambda: self.execute_calDialogBox(self.dia_additional))
        self.b_add.setToolTip("Add/Remove additional Gain/Loss elements") 
        self.b_add.setIcon(img_add)
        self.b_add.setIconSize(QSize(BUTTON_LENGTH,BUTTON_HEIGHT))
        additionalVBoxLayout.addWidget(self.b_add)
        additionalVBoxLayout.addLayout(additionalBoxLayout)
        
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
        specanBox.setStyleSheet(self.create_styleSheet('specan'))#apply styling
        specanVBoxLayout=QVBoxLayout()
        specanBoxLayout=QFormLayout()
        specanBox.setLayout(specanVBoxLayout)
        
        #create button NOTE: b_specan.setEnable() is called from parent
        self.b_specan=QPushButton('Spectrum Analyzer')
        self.b_specan.clicked.connect(lambda: self.execute_calDialogBox(self.dia_specAn))
        self.b_specan.setToolTip("Adjust settings for Spectrum Analyzer")
        self.b_specan.setEnabled(True) 
        specanVBoxLayout.addWidget(self.b_specan)
        specanVBoxLayout.addLayout(specanBoxLayout)
        
        #create Qlabels
        self.gui_specan=QLabel(str(self.cal_rxGain))
        specanBoxLayout.addRow(QLabel("model: "),self.gui_specan)
        
        #=======================================================================
        # Create inner calibration form
        #=======================================================================
        innerCalBox=QGroupBox("Configuration")
        innerCalBox.setStyleSheet(self.create_styleSheet('setup'))#apply styling
        innerCalVBox= QVBoxLayout()
        innerCalVBox.addLayout(tabStateLayout)
        innerCalBoxLayout=QGridLayout()
        
        innerCalVBox.addLayout(innerCalBoxLayout)
        innerCalBox.setLayout(innerCalVBox)
        #=======================================================================
        # create test info Layout
        #=======================================================================
        infoBox=QGroupBox('Test Information')
        infoBoxLayout=QFormLayout()
        #create customer namer line edit
        self.e_cal_customer = QLineEdit('')
        self.e_cal_customer.connect(self.e_cal_customer,SIGNAL('returnPressed()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("Customer's Name"),self.e_cal_customer)
        
        #create orientation line edit
        self.cb_cal_orientation = QComboBox()
        self.cb_cal_orientation.addItem("Vertical")
        self.cb_cal_orientation.addItem("Horizontal")
        self.cb_cal_orientation.connect(self.cb_cal_orientation,SIGNAL('currentIndexChanged()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("RX Polarity"),self.cb_cal_orientation)
        
        #create DUT label line edit
        self.e_cal_dutLabel = QLineEdit('')
        self.e_cal_dutLabel.connect(self.e_cal_dutLabel,SIGNAL('returnPressed()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("DUT Label"),self.e_cal_dutLabel)
        
        #create DUT SN line edit
        self.e_cal_dutSN = QLineEdit('')
        self.e_cal_dutSN.connect(self.e_cal_dutSN,SIGNAL('returnPressed()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("DUT Serial Number"),self.e_cal_dutSN)
        
        #create tester namer line edit
        self.e_cal_tester = QLineEdit('')
        self.e_cal_tester.connect(self.e_cal_tester,SIGNAL('returnPressed()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("Tester's Name"),self.e_cal_tester)
        
        #create coments line edit
        self.e_cal_comments = QLineEdit('')
        self.e_cal_comments.connect(self.e_cal_comments,SIGNAL('returnPressed()'),self.apply_testInfo)
        infoBoxLayout.addRow(QLabel("Comments"),self.e_cal_comments)
        
        
        
        #create apply button
        b_applyInfo=QPushButton('Apply')
        b_applyInfo.clicked.connect(self.apply_testInfo)
        b_applyInfo.setToolTip("Apply test info")
        infoBoxLayout.addWidget(b_applyInfo)
        
        infoBox.setLayout(infoBoxLayout)
        
        
        
        #=======================================================================
        # create Test Configuration Layout
        #=======================================================================
        configBox=QGroupBox('Test Configuration')
        configBoxLayout=QFormLayout()
        
        self.e_cal_freq = QLineEdit(str(self.cal_freq/1e6))
        self.e_cal_freq.returnPressed.connect(self.apply_testConfig)
        
        
        #self.e_cal_freq.connect(self.e_cal_freq,SIGNAL('returnPressed()'),self.update_calibration)
        configBoxLayout.addRow(QLabel("Testing Frequency (MHz)"),self.e_cal_freq)
        
        #TODO add center/span functionality when starting test
        self.e_cal_span= QLineEdit(str(self.cal_span/1e6))
        self.e_cal_span.returnPressed.connect(self.apply_testConfig)
        configBoxLayout.addRow(QLabel("Testing Frequency Span (MHz)"),self.e_cal_span)
        
        self.e_cal_sc_sweepTime= QLineEdit(str(self.cal_sc_sweepTime*1000))
        self.e_cal_sc_sweepTime.returnPressed.connect(self.apply_testConfig)
        configBoxLayout.addRow(QLabel("sweep Time (ms)"),self.e_cal_sc_sweepTime)
        
        self.e_cal_dist = QLineEdit('3')
        self.e_cal_dist.connect(self.e_cal_dist,SIGNAL('returnPressed()'),self.apply_testConfig)
        configBoxLayout.addRow(QLabel("Testing Distance (m)"),self.e_cal_dist)
        
        
        self.e_cal_res=QLineEdit(str(100))
        self.e_cal_res.connect(self.e_cal_res,SIGNAL('returnPressed()'),self.apply_testConfig)
        configBoxLayout.addRow('Resolution (# of Data Points)',self.e_cal_res)
        
        
        #create static cable check box
        self.cb_cal_staticCable = QCheckBox()
        self.cb_cal_staticCable.connect(self.cb_cal_staticCable,SIGNAL('clicked()'),self.apply_testConfig)
        configBoxLayout.addRow(QLabel("Static Cable"),self.cb_cal_staticCable)
        self.cb_cal_staticCable.setToolTip("check this box if a static cable is connected to the rotating table.\n\nthis will cause the table to rotate backward to home after each test to unwind cable")


        #create apply button
        self.b_applytestConfig=QPushButton('Apply')
        self.b_applytestConfig.clicked.connect(self.apply_testConfig)
        self.b_applytestConfig.setToolTip("Apply test configuration")
        configBoxLayout.addWidget(self.b_applytestConfig)
        
        configBox.setLayout(configBoxLayout)
    
        #=======================================================================
        # create calibration equation layout
        #=======================================================================
        calEqBox=QGroupBox('Calibration Equation')
        calEqBox.setMinimumWidth(600)#set min width so equiation doesnt get screwed up
        calEqBoxLayout=QHBoxLayout()
        calEqBox.setStyleSheet(self.create_styleSheet('EMC2'))#apply styling
        self.calFunctionTotalDisplay=QLabel()
        
        self.calFunctionTotalDisplay.setAlignment(Qt.AlignCenter)
        self.calFunctionTotalDisplay.setMargin(4)   
        
        self.calFunctionDisplay=QLabel()
        self.calFunctionDisplay.setAlignment(Qt.AlignLeft)
        self.calFunctionDisplay.setMargin(4) 
        self.calFunctionDisplay.setWordWrap(True)
        
        calEqBoxLayout.addWidget(self.calFunctionDisplay)
        calEqBoxLayout.addWidget(self.calFunctionTotalDisplay)
        
        calEqBox.setLayout(calEqBoxLayout)
        
        self.update_displayValues()
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
        #Additional
        grid.addWidget(QLabel(pixmap=img_dnArrow.scaledToHeight(24),alignment=Qt.AlignCenter),3,4)
        grid.addWidget(additionalBox,4,4)
        #specan
        grid.addWidget(QLabel(pixmap=img_dnArrow.scaledToHeight(24),alignment=Qt.AlignCenter),5,4)
        grid.addWidget(specanBox,6,4)
        
        
        
        #=======================================================================
        # set up GUI Grid inner layout
        #=======================================================================
        grid.addWidget(innerCalBox,1,1,6,3)
        
        innerCalBoxLayout.addWidget(infoBox,0,0)
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
        
        #set defaulttab state
        self.cb_tabState.setCurrentIndex(0)
        
        #apply layout to calibration tab
        vbox=QVBoxLayout()
#         vbox.addLayout(tabStateLayout)
        vbox.addLayout(grid)
        
        tab.setLayout(vbox)
        
        #set initial conditions
        self.update_calibration()
    
    def calibrate_data(self,data):#calibrate collected data
        #=======================================================================
        #
        #          Name:    calibrate_data
        #
        #    Parameters:    float(data) (uncalibrated data from data collection array)
        #
        #        Return:    (float)temp (calibrated data)
        #
        #   Description:    calibrates the input value according to the calibration inputs from user
        #
        #=======================================================================
        'Calibrate Collected Data'
        
        temp=(data-self.cal_inputPwr)       #subtract input power in dBm
        
        temp=temp-self.cal_ampGain          #subtract preamp gain
        
        temp=temp-self.cal_txCableLoss      #subtract cable loss
        
        temp=temp-self.cal_txGain           #Subtract DUT(Tx) antenna gain
        
        temp=temp-self.cal_fspl             #subtract free space  loss
        
        temp=temp-self.cal_rxGain           #Subtract Calibrated (Rx) antenna gain
                
        temp=temp-self.cal_rxCableLoss      #subtract cable loss
        
        temp=temp-self.cal_additionalGain   #subtract any additional gain/loss

        return temp    
    
    def get_calNum(self,freq):#calibrate collected data
        #=======================================================================
        #
        #          Name:    calibrate_data
        #
        #    Parameters:    float(data) (uncalibrated data from data collection array)
        #
        #        Return:    (float)temp (calibrated data)
        #
        #   Description:    calibrates the input value according to the calibration inputs from user
        #
        #=======================================================================
        'Calibrate Collected Data'
        
        temp=-(self.cal_inputPwr)                       #subtract input power in dBm
        
        temp=temp-self.dia_preAmp.get_ampGain(freq)         #subtract preamp gain
        
        temp=temp-self.dia_txCable.get_cableLoss(freq)      #subtract cable loss
        
        temp=temp-self.dia_tx.get_antennaGain(freq)         #Subtract DUT(Tx) antenna gain
        
        temp=temp-self.get_fspl(freq)                             #subtract free space  loss
        
        temp=temp-self.dia_rx.get_antennaGain(freq)         #Subtract Calibrated (Rx) antenna gain
                
        temp=temp-self.dia_rxCable.get_cableLoss(freq)      #subtract cable loss
        
        temp=temp-self.cal_additionalGain                   #subtract any additional gain/loss

        return temp   
            
    
    def execute_calDialogBox(self,dialog):#Execute one of the calibration dialog boxes
        #=======================================================================
        #
        #          Name:    execute_calDialogBox
        #
        #    Parameters:    (QDialogBox) dialog
        #
        #        Return:    None
        #
        #   Description:    executes the dialog box from the input parameter
        #
        #=======================================================================
        "Run execute item specific dialog box"
        if dialog==self.dia_additional:
            dialog.tempDict=self.addGainLoss.copy()
            dialog.tempCalValue=self.cal_additionalGain
            
        dialog.exec_()
        
    def update_displayValues(self):#update displayed calibration function
        #=======================================================================
        #
        #          Name:    update_displayValues
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this functions updates all of the displayed values on the calibration tab
        #
        #=======================================================================
        "Update the Calibration equation shown in the calibration tab"
        
        #=======================================================================
        # set text that displays the calibration equation
        #=======================================================================
        self.calFunctionDisplay.setText('''<span style=" color:#00FF00; font-size:9pt; font-weight:300;">
                                            (Data)<br/> - ('''+str(self.cal_inputPwr)+ ''' dBm): Input Power<t/><br/>
                                            - ('''+str(self.cal_ampGain)+''' dB): PreAmpGain<br/>
                                            - ('''+str(self.cal_txCableLoss)+''' dB): Tx Cable Loss<br/>
                                            - ('''+str(self.cal_txGain)+''' dBi): DUT Gain<br/>
                                            - (''' +str(self.cal_fspl)+''' dB): FSPL<br/>
                                            - ('''+str(self.cal_rxGain)+''' dBi): Calibrated Antenna Gain<br/>
                                            - ('''+str(self.cal_rxCableLoss)+''' dB): Rx Cable_Loss<br/>
                                            - ('''+str(self.cal_additionalGain)+''' dB): Addidtional_Gain</span>''')
        
        
        
        
        #=======================================================================
        # add "+" or "-" to front of total calibration display
        #=======================================================================
        if self.calibrate_data(0)>=0:
            self.calFunctionTotalDisplay.setText('''<span style=" color:#00FF00; font-size:20pt; font-weight:400;">
                                                        Total Calibration:<br/>   +'''+str(self.calibrate_data(0))+''' (dB)</span>''')
        else:       
            self.calFunctionTotalDisplay.setText('''<span style=" color:#00FF00; font-size:20pt; font-weight:400;">
                                                        Total Calibration:<br/>   '''+str(self.calibrate_data(0))+''' (dB)</span>''')
            
        #=======================================================================
        # update displayed values of gain elements 
        #=======================================================================
        self.gui_inputPwr.setText(str(self.cal_inputPwr)+" dBm")
        self.gui_ampGain.setText(str(self.cal_ampGain)+" dB")
        self.gui_txCableLoss.setText(str(self.cal_txCableLoss)+" dB")
        self.gui_txGain.setText(str(self.cal_txGain)+" dBi")
        self.gui_fspl.setText(str(self.cal_fspl)+" dB")
        self.gui_rxGain.setText(str(self.cal_rxGain)+" dBi")
        self.gui_rxCableLoss.setText(str(self.cal_rxCableLoss)+" dB")
        self.gui_additional.setText(str(self.cal_additionalGain)+" dB")
        
        self.e_cal_span.setText(str(self.cal_span/1e6))
        self.e_cal_freq.setText(str(self.cal_freq/1e6))
        self.e_cal_sc_sweepTime.setText(str(self.cal_sc_sweepTime*1e3))
        
        #=======================================================================
        # update gain/losses in GUI labels
        #=======================================================================
        self.gui_ampCalFreq.setText(str(self.dia_preAmp.calFreq))
        self.gui_txCableCalFreq.setText(str(self.dia_txCable.calFreq))
        self.gui_txCalFreq.setText(str(self.dia_tx.calFreq))
        self.gui_rxCalFreq.setText(str(self.dia_rx.calFreq))
        self.gui_rxCableCalFreq.setText(str(self.dia_rxCable.calFreq))
        
        #=======================================================================
        # update frequency in EMC testing tab
        #=======================================================================
        self.mainForm.emc_gui_dist.setText(str(self.cal_dist))    
        #self.gui_specan.setText("--Spectrum analyzer not detected--")
     
    def get_fspl(self,freq):
        #=======================================================================
        #
        #          Name:    get_fspl
        #
        #    Parameters:    (float)freq
        #
        #        Return:    (float) value of FSPL either calculated or user input
        #
        #   Description:    function returns the value of FSPL based on frequency and testing distance
        #
        #=======================================================================
        if(self.dia_fspl.cb_cal_fspl.currentText()=='Derived'):
            
            #calculate FSPL
            fspl = -(20*math.log10(freq)+(20*math.log10(float(self.e_cal_dist.text())))+20*math.log10((4*np.pi)/299792458))   
            return fspl 
        else:
            return float(self.dia_fspl.e_cal_fspl.text())
        
    
    def set_fspl(self):#calculate or manually setFSPL 
        #=======================================================================
        #
        #          Name:    set_fspl
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this functional calculates the FSPL and updates the displayed values
        #
        #=======================================================================
        "Calculate FSPL and update frequency for automatic frequency selection"
        #=======================================================================
        # set manual FSPL
        #=======================================================================
        if str(self.dia_fspl.cb_cal_fspl.currentText())=='Manual':
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_fspl=float(self.dia_fspl.e_cal_fspl.text())
            self.cal_freq=float(self.e_cal_freq.text())*1e6
        else:
        #=======================================================================
        # set derived 
        #=======================================================================
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_freq=float(self.e_cal_freq.text())*1e6
            self.cal_fspl= -(20*math.log10(self.cal_freq)+(20*math.log10(float(self.e_cal_dist.text())))+20*math.log10((4*np.pi)/299792458))       
            self.dia_fspl.e_cal_fspl.setText(str(self.cal_fspl))
        self.gui_fsplMode.setText(self.dia_fspl.cb_cal_fspl.currentText())
    
    def update_autoGains(self):#update gain for calibration elements that are set to "auto"
        #=======================================================================
        #
        #          Name:    update_autoGains
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function updates the gain on any elements set to "auto" whenever the user
        #                    changes the test frequency
        #
        #=======================================================================
        'Update the values of calibrated elements to correct gain at currently selected test frequency'
        
        #=======================================================================
        # update automatically set gains/losses based on new frequency 
        #=======================================================================
        self.dia_preAmp.set_ampGain()
        self.dia_tx.set_antennaGain()
        self.dia_txCable.set_cableLoss()
        self.dia_rxCable.set_cableLoss()
        self.dia_rx.set_antennaGain()
        
    def update_calibration(self,draw=True):#update calibration values
        #=======================================================================
        #
        #          Name:    update_calibration
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function updates all of the calibration parameters 
        #                    as well as the displayed values
        #
        #=======================================================================
        self.update_autoGains()
        self.set_fspl()
        if draw:
            self.update_displayValues()
            self.mainForm.set_emcRegulations()
        
    def set_fsplMode(self):#set manual or derived mode for FSPL Loss
        #=======================================================================
        #
        #          Name:    set_fsplMode
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function switches the fspl mode from "manual" to "derived"
        #
        #=======================================================================
        'set FSPL mode to either manual or derived'
        if str(self.cb_cal_fspl.currentText())=='Manual':
            self.e_cal_fspl.setEnabled(True)
        else:
            self.e_cal_fspl.setEnabled(False)
        
        self.update_calibration()
             
    def apply_specanSettings(self):# apply calibration settings
        #=======================================================================
        #
        #          Name:    apply_specanSettings
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function applies all of the specan settings based on user inputs
        #
        #                    NOTE: this only applies to SIGNAL HOUND BB60c
        #
        #=======================================================================
        'apply calibration settings to specturm alalyzer'
        
        #TODO: add automatic parameter correction in case of user error
        try:
            #===================================================================
            # signalhound specan
            #===================================================================
            if(self.worker.specan.get_SpectrumAnalyzerType()=="SH"):
                
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
                
                # set attenuation
                if self.dia_specAn.cb_autoAtten.isChecked():
                    self.cal_level_atten="auto"
                else:
                    self.cal_level_atten=float(self.dia_specAn.e_cal_atten.text())
                    
                self.worker.specan.sh.configureLevel(int(self.dia_specAn.cb_cal_attenRef.currentText()) , self.cal_level_atten)#set attenuation in specan
                
                #log or linear units
                self.worker.specan.sh.configureProcUnits("log")
                
                #data units
                self.worker.specan.sh.configureAcquisition(str(self.cal_aq_detector),str(self.cal_aq_scale))
                
                #rbw
                self.cal_sc_rbw=float(self.dia_specAn.e_cal_sc_rbw.text())*1000
                self.cal_sc_vbw=float(self.dia_specAn.e_cal_sc_vbw.text())*1000
                
                #sweeptime, RBW, VBW
                self.worker.specan.set_sweeptime(self.cal_sc_sweepTime)
                
                #setup center frequency and span of test sweep
                self.worker.specan.set_frequency(self.cal_freq,self.cal_span)
                
            #===================================================================
            # HP specan
            #===================================================================
            if(self.worker.specan.get_SpectrumAnalyzerType()=="HP"):    
                pass  
            #===================================================================
            # TODO: NEW SPECAN
            #===================================================================
            if(self.worker.specan.get_SpectrumAnalyzerType()=="New_Specan_ID"):    
                pass

        except:
            print "could not find Specan"
        
    def set_specan_AutoGain(self):#toggle auto-gain settings
        #=======================================================================
        #
        #          Name:    set_specan_AutoGain
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the specan Gain from Auto to manual
        #                    
        #                    NOTE: this only changes Calibrator values NOT specan Values
        #
        #=======================================================================
        'toggle auto attenuation setting'
        
        if self.dia_specAn.cb_autoGain.isChecked():
            print "Gain set to AUTO"
            self.cal_gain='auto'
            self.dia_specAn.e_cal_gain.setEnabled(False)
        else:
            print "Gain set to ManuaL"
            self.dia_specAn.e_cal_gain.setEnabled(True)
        
    def set_specan_autoAttenuation(self):#toggle auto-gain settings
        #=======================================================================
        #
        #          Name:    set_specan_autoAttenuation
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    sets specan attenuation to auto or manual
        #
        #                    NOTE: this only changes Calibrator values NOT specan Values
        #                    
        #=======================================================================
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
            
    def set_specan_autoAttenReference(self):#set reference for auto attenuation
        #=======================================================================
        #
        #          Name:    set_specan_autoAttenReference
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this functions sets the auto attenuation reference value
        #
        #                    NOTE: this only set the Calibrator values not the specan values
        #
        #=======================================================================
        'set reference value for auto attenuation'
        
        self.cal_level_ref=int(self.dia_specAn.cb_cal_attenRef.currentText())
        print "Attenuation reference set to " + str(self.cal_level_ref)

    def set_specan_detectorType(self):#set detector type for acquisition
        #=======================================================================
        #
        #          Name:    set_specan_detectorType
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the specan detector type
        #
        #                    NOTE: this only sets the Calibrator values not the Specan values
        #
        #=======================================================================
        'set spectrum analyzer detector type'
        self.cal_aq_detector=self.dia_specAn.cb_cal_aqDet.currentText()
        print "Aquisition detector type set to " + str(self.cal_aq_detector)
  
    def set_specan_detectorScale(self):#set detector type for acquisition
        #=======================================================================
        #
        #          Name:    set_specan_detectorScale
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the detector scaling
        #
        #                    NOTE this Only set the Calibrator Values Not the Specan Values
        #
        #=======================================================================
        'set acquisition scaling in spectrum analyzer'
        
        self.cal_aq_scale=self.dia_specAn.cb_cal_aqScale.currentText()
        print "Aquisition scale set to " + str(self.cal_aq_scale)
    
    def set_inputPwr(self):#set input power for calibration
        #=======================================================================
        #
        #          Name:    set_inputPwr
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the input power from user input
        #
        #=======================================================================
        'Set input power for calibration'
        self.cal_inputPwr=float(self.dia_sigGen.e_cal_inputPwr.text())
        
        self.update_calibration()
          
#     def get_bestValue2(self,gainDict,testfreq):#get closest value to selected test frequency
#         #=======================================================================
#         #
#         #          Name:    get_bestValue2
#         #
#         #    Parameters:    (disctionary) gainDict
#         #
#         #        Return:    (int)
#         #
#         #   Description:    this function finds the closest frequency to a
#         #                    newly selected frequency for elements that are set to auto
#         #                    
#         #                    if the closest value is between 2 calibrated frequencies
#         #                    the frequency with the highest gain will be selected
#         #
#         #=======================================================================
#         'get closest value to selected test frequency, if value is between to frequencies the frequency with the highest gain will be chosen'
#         
#         bestVal=9999999#set very high initial value to be replaced on first iteration
#         
#         #iterate through all values in gain dictionary and test against current best value
#         for freq in sorted(gainDict):
#             if abs(int(freq)-testfreq/1e6)<abs((int(bestVal)-testfreq/1e6)):#if (current frequency)-(test frequency)<(best value)-(test frequency)
#                 bestVal=freq
#             elif abs(int(freq)-testfreq/1e6)==abs((int(bestVal)-testfreq/1e6)):#if (current frequency)-(test frequency)==(best value)-(test frequency): get frequency with higher gain
#                 
#                 if gainDict[str(freq)]>=gainDict[str(int(bestVal))]:
#                     bestVal=freq
#         return int(bestVal)
    
    def create_styleSheet(self,style):#set styling for GUI elements
        #=======================================================================
        #
        #          Name:    create_styleSheet
        #
        #    Parameters:    (string)style
        #
        #        Return:    None
        #
        #   Description:    this function sets the styling for QGroupBoxes used mainly in the calibration tab
        #
        #=======================================================================
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
        if style=='EMC1':
            retval="""
                    QGroupBox { 
                        background-color: rgb(110, 173, 112);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 12px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        if style=='EMC2':
            retval="""
                    QGroupBox { 
                        background-color: rgb(50, 50, 50);
                        margin-top: 0.5em;
                        border: 1px solid #FFFFFF;
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 12px;}
                            
                    QGroupBox::title {
                        top: -3px;
                        left: 10px;
                        color: #FFFFFF;}
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
                        font-size: 12px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
        elif style=='eq':
            retval="""
                    QGroupBox { 
                        background-color: rgb(110, 173, 112);
                        margin-top: 0.5em;
                        border: 1px solid rgb(25, 25, 25);
                        border-radius: 3px;
                        padding: 3 3px; 
                        font-size: 16px;}
                            
                    QGroupBox::title {
                        top: -6px;
                        left: 10px;}
                    """
                    #background-color: rgb(31, 150, 18);
                    
        elif style=='calTab':
            retval="""
                     QTabBar::tab:selected {
                         background: gray;}
                     QTabWidget>QWidget>QWidget{
                         background: rgb(142, 142, 142);}
                    """
                    
        elif style=='dataTab':
            retval="""
                     QTabBar::tab:selected {
                         background: gray;}
                     QTabWidget>QWidget>QWidget{
                         background: rgb(142, 142, 142);}
                    """
        return retval

    def get_setupDialogValues(self):#grab settings from setup dialog box
        #=======================================================================
        #
        #          Name:    get_setupDialogValues
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function gets the test setup values from the
        #                    "Setup" Object
        #
        #=======================================================================
        'grab settings from setup dialog box'
        #=======================================================================
        #call function with one of the following numbers
        #
        #setup.num_st         = 0
        #setup.num_cfreq      = 1
        #setup.num_span       = 2
        #setup.num_offset     = 3
        #setup.maxhold        = 4
        #setup.usesig         = 5
        #setup.num_res        = 6
        #=======================================================================
        
        settingList=self.setup.get_values()
        self.set_frequency(settingList[1])
        self.set_span(settingList[2])
        self.set_sweepTime(settingList[0])
        self.update_calibration()

    def set_frequency(self,freq):#set frequency for test and calibration
        #=======================================================================
        #
        #          Name:    set_frequency
        #
        #    Parameters:    (float)freq
        #
        #        Return:    None
        #
        #   Description:    this function sets the testing frequency
        #
        #=======================================================================
        'set testing frequency'
        print "e text",self.e_cal_freq.text()
        if freq==0:#when xero this is being called from the gui, else is called from setup dialog box
            if self.e_cal_freq.text()!="Auto":
                self.cal_freq=float(self.e_cal_freq.text())*1e6
        else:
            self.cal_freq=float(freq)
            
        self.setup.set_frequency(self.cal_freq)
        
        self.mainForm.currentTest.setFreqCenter(self.cal_freq)
        
        print "Test Frequency set to ", self.cal_freq, " Hz\n"

    def set_span(self,span):#set frequency span for test
        #=======================================================================
        #
        #          Name:    set_span
        #
        #    Parameters:    (float)span
        #
        #        Return:    None
        #
        #   Description:    this function sets the testing frequency span
        #
        #=======================================================================
        'set testing span'
        
        if span==0:#when xero this is being called from the gui, else is called from setup dialog box
            if self.e_cal_span.text()!="Auto":
                self.cal_span=float(self.e_cal_span.text())*1e6 
        else:
            self.cal_span=float(span)
        
        self.setup.set_span(self.cal_span)
        
        self.mainForm.currentTest.setFreqSpan(self.cal_span)
        
        print "Test frequency span set to ", self.cal_span, " Hz\n"
        
    def set_sweepTime(self,st):#set frequency span for test
        #=======================================================================
        #
        #          Name:    set_sweepTime
        #
        #    Parameters:    (float)st
        #
        #        Return:    None
        #
        #   Description:    this function sets the testing sweep time
        #
        #=======================================================================
        'set testing span'
        
        if st==0:#when zero this is being called from the gui, else is called from setup dialog box
            if self.e_cal_sc_sweepTime.text()!="Auto":
                self.cal_sc_sweepTime=float(self.e_cal_sc_sweepTime.text())/1e3
        else:
            self.cal_sc_sweepTime=float(st)
        self.setup.set_sweepTime(self.cal_sc_sweepTime)
        
        self.mainForm.currentTest.setSweepTime(self.cal_sc_sweepTime)
        
        print "Sweep time set to ", self.cal_sc_sweepTime, " seconds\n"

    def set_distance(self):
        #=======================================================================
        #
        #          Name:    set_distance
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the testing distance in meters
        #
        #=======================================================================
        'set testing distance'
        self.cal_dist=float(self.e_cal_dist.text())
        
        self.mainForm.currentTest.setDistance(self.cal_dist)
        
        #self.update_calibration()
        print "testing distance set to ", self.cal_dist, " m\n"
      
    def apply_testConfig(self):#apply test configuration settings when "apply" is clicked
        #=======================================================================
        #
        #          Name:    apply_testConfig
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this functions ets the test configuration when the user
        #                    clicks the apply pushbutton in the test configuration groupbox
        #
        #=======================================================================
        'apply test configuration settings when "apply" is clicked'
        
#         self.set_resolution()
        self.set_frequency(0)
        self.mainForm.currentTest.setFreqCenter(self.cal_freq)
        
        self.set_span(0)
        self.mainForm.currentTest.setFreqSpan(self.cal_span)
        
        self.set_sweepTime(0)
        self.mainForm.currentTest.setSweepTime(self.cal_sc_sweepTime)
        
        self.set_distance()
        self.mainForm.currentTest.setDistance(self.cal_dist)
        
        if(self.tabState!=TABSTATE_EMC):
            self.update_calibration()
            
        self.cal_staticCable=self.cb_cal_staticCable.isChecked();
        
        if self.cb_cal_staticCable.isChecked():
            self.setup.cb_cal_staticCable.setCheckState(Qt.Checked)
        else:
            self.setup.cb_cal_staticCable.setCheckState(Qt.Unchecked)
            
        self.cal_res=float(self.e_cal_res.text())
        self.setup.set_resolution(self.cal_res)
        
        print self.cal_staticCable
        self.apply_testInfo()
                   
    def apply_testInfo(self):#apply test information settings when apply is clicked
        #=======================================================================
        #
        #          Name:    apply_testInfo
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the test info when the user clicks the apply button 
        #                    in the test information groupbox
        #
        #=======================================================================
        'apply test info for test report'
        
        
        self.cal_dutLabel=str(self.e_cal_dutLabel.text())
        self.mainForm.currentTest.setLabel(self.cal_dutLabel)
        print "DUT Labet set to: ", self.cal_dutLabel
        
        self.cal_dutSN=str(self.e_cal_dutSN.text())
        self.mainForm.currentTest.setSN(self.cal_dutSN)
        print "DUT serial Number set to: ", self.cal_dutSN
        
        self.cal_comments=str(self.e_cal_comments.text())
        print "Comments added: ", self.cal_comments
        
        self.cal_customer=str(self.e_cal_customer.text())
        print "Customer Name set to ", self.cal_customer 
        
        self.cal_tester=str(self.e_cal_tester.text())
        print "tester Name set to ", self.cal_tester
        
        self.cal_orientation=str(self.cb_cal_orientation.currentText())
        self.mainForm.currentTest.setRxPolarity(self.cal_orientation)
        print "RX Orienation set to ", self.cal_orientation
        
        self.mainForm.update_figureInfo()
        
    def testConfigEnable(self,true):
        if true:
            self.b_applytestConfig.setEnabled(True)
            self.e_cal_freq.setEnabled(True)
            self.e_cal_sc_sweepTime.setEnabled(True)
            self.cb_cal_staticCable.setEnabled(True)
            self.e_cal_dist.setEnabled(True)
            self.e_cal_span.setEnabled(True)
        else:
            self.b_applytestConfig.setEnabled(False)
            self.e_cal_freq.setEnabled(False)
            self.e_cal_sc_sweepTime.setEnabled(False)
            self.cb_cal_staticCable.setEnabled(False)
            self.e_cal_dist.setEnabled(False)
            self.e_cal_span.setEnabled(False)
            
            
    def set_setup(self,setup):#set pointer to setup dialog box
        #=======================================================================
        #
        #          Name:    set_setup
        #
        #    Parameters:    (Setup Object)setup
        #
        #        Return:    None
        #
        #   Description:    this function creates a pointer to the Setup object
        #
        #=======================================================================
        'holds setup dialog box'
        self.setup=setup
    
    def set_worker(self,worker):#set pointer to worker object
        #=======================================================================
        #
        #          Name:    set_worker
        #
        #    Parameters:    (Worker object)worker
        #
        #        Return:    None
        #
        #   Description:    thsi function creates a pointer to the Worker Object
        #
        #=======================================================================
        'holds access to worker'
        self.worker=worker
    
    def set_mainForm(self,mainForm):#set pointer to main Form object
        #=======================================================================
        #
        #          Name:    set_mainForm
        #
        #    Parameters:    (AppForm object)mainForm
        #
        #        Return:    None
        #
        #   Description:    this function creates a pointer to the main "AppForm" object
        #
        #=======================================================================
        'holds access to worker'
        self.mainForm=mainForm
    
    def get_tabState(self):
        #=======================================================================
        #
        #          Name:    get_tabState
        #
        #    Parameters:    None
        #
        #        Return:    returns the current tabstate(testing type)
        #
        #   Description:    this function returns the current tab state which corresponds
        #                   to the current testing type(EMC/Radiation pattern)
        #
        #=======================================================================
        return self.tabState
      
    def get_RBW(self):
        #=======================================================================
        #
        #          Name:    get_RBW
        #
        #    Parameters:    None
        #
        #        Return:    (float)
        #
        #   Description:    this functions returns the cal_sc_rbw (user defined resolustion bandwidth) value
        #
        #=======================================================================
        'returns resolution bandwidth setting'
        
        return self.cal_sc_rbw
    
    def get_VBW(self):
        #=======================================================================
        #
        #          Name:    get_VBW
        #
        #    Parameters:    None
        #
        #        Return:    (float)
        #
        #   Description:    this functions returns the cal_sc_vbw (user defined video bandwidth) value
        #
        #=======================================================================
        'returns video bandwidth setting'
        
        return self.cal_sc_vbw
    
    
    
    
    
#end of file