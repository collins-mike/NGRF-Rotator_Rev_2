'''
project: Rotator Rev2 
copyright 2017 NextGen RF Design
author Mike Collins
mike.collins@nextgenrf.com

The CalDialog class set functionality for the calibration
dialog boxes that appear in the calibration tab. when executed
the dialog boxes will change the settings for the calibration
parameters that are held in the "Calibrator" class. 

'''
#
import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class CalDialog(QDialog):       #create setup dialog that finds specan and turntable, and sets basic specan parameters
    def __init__(self,parent=None,worker=None,fType=None,rxtx=None):
#==================================================
#initialize all variables and functions for setup dialog
#==================================================
        super(CalDialog,self).__init__(parent)
        
        
        self.worker=worker      #get worker form cal
        self.parent=parent      #get parent instance
        
        self.cal=parent
        
        self.fType=fType        #get form type
        self.rxtx=rxtx          #get whether rx or tx
        
        #setup base layout for dialog box
        self.vert = QVBoxLayout()
        
        #create "OK" and "Cancel" push buttons in dialog window
        self.b_box = QDialogButtonBox(QDialogButtonBox.Ok  | QDialogButtonBox.Cancel)
            
        #setup item specific Gui layout of Dialog box
        self.form=QFormLayout()   
            
            
        if self.fType=='antenna':
            self._init_antenna()
            self.calFreq=''                 #create a string to hold calibration frequency for GUI display
        elif self.fType=='cable':
            self._init_cable()
            self.calFreq=''                 #create a string to hold calibration frequency for GUI display
        elif self.fType=='amp':
            self._init_amplifier()
            self.calFreq=''                 #create a string to hold calibration frequency for GUI display
        elif self.fType=='fspl':
            self._init_fspl()
        elif self.fType=='input':
            self._init_sigGen()
        elif self.fType=='specAn':
            self._init_specAn()
        elif self.fType=='sigGen':
            self._init_sigGen() 
        elif self.fType=='add':
            self._init_additional()
               
        #set up layouts    
        self.vert.addLayout(self.form)
        self.vert.addWidget(self.b_box)
        self.setLayout(self.vert)

        
            
        #set button behavior
        self.connect(self.b_box, SIGNAL('rejected()'),self.click_cancel)    #behavior when "cancel" is clicked
        self.connect(self.b_box, SIGNAL('accepted()'),self.click_ok)        #behavior when "ok" is clicked
        
         
        self.dev_connected=False
        #self.worker.dev_found.connect(self.device_found)
                   
    def _init_antenna(self):                #sets up antenna setting dialog box
        #=======================================================================
        #
        #          Name:    _init_antenna
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function initializes antenna selection dialog boxes
        #                    and sets their form and user interface
        #
        #=======================================================================

        'initialize antenna dialog box'
        fbox = QFormLayout()
        "Initialze antenna setting dialog box"
        self.setWindowTitle("Antenna Setup")
        
        #create dictionaries to hold cal data
        self.cal_antFile={}                                                         #dictionary thats holds list of file names of calibrated antennas
        self.cal_antennaFreqGain={}                                                 #dictionary holds frequency and gain relationships of antenna
        
        #=================================
        # calibrated Antenna selection buttons
        #=================================
        
        #create dictionaries to hold cal data
        self.cal_antFile={}                                                         #dictionary thats holds list of file names of calibrated antennas
        self.cal_antennaFreqGain={}                                                 #dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_antennaSel=QComboBox()                                              #create combo box to select antenna
        self.cb_antennaSel.addItem('Manual')
        self.cb_antennaSel.setToolTip("Select Calibrated Antenna")
        self.cb_antennaSel.currentIndexChanged.connect(self.set_antenna)
        
        self.cb_antennaFreqSel=QComboBox()                                          #create combo box to select antenna calibration frequency
        self.cb_antennaFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_antennaFreqSel.currentIndexChanged.connect(self.set_antennaGain)
        self.cb_antennaFreqSel.setEnabled(False)
        
        #==========================================
        # import list of antennas from antennas.csv
        #=========================================
        
        try:                                                #import list of calibrated antennas from antennas.csv
            with open('calibration/antennaList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:                   #stop app from importing csv header
                        print(row[0]+" Antenna found")
                        self.cb_antennaSel.addItem(row[0])
                        self.cal_antFile[row[0]]='calibration/antennas/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox.addRow('Antenna Type', self.cb_antennaSel)
        fbox.addRow('Antenna calibration frequency (MHz)',self.cb_antennaFreqSel)
        
        #====================================
        # Manual gain line edit box
        #====================================
        self.e_cal_AntGain = QLineEdit('0')
        self.e_cal_AntGain.connect(self.e_cal_AntGain,SIGNAL('returnPressed()'),self.set_antennaGain)
        fbox.addRow(QLabel("Rx-Antenna Gain (dBi)"),self.e_cal_AntGain)
        
        self.vert.addLayout(fbox)
        
    def _init_amplifier(self):	            #sets up amplifier settings dialog box
        #=======================================================================
        #
        #          Name:    _init_amplifier
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the ampliier calibration dialog box
        #
        #=======================================================================
        "Initialze amplifer setting dialog box"
        self.setWindowTitle("Amplifier Setup")
        fbox = QFormLayout()
        #=================================
        # calibrated PreAmp selection buttons
        #=================================
        fbox.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Amplifier</span>'))
        
        #create dictionaries to hold cal data
        self.cal_ampFile={}                                 #dictionary thats holds list of file names of calibrated antennas
        self.cal_ampFreqGain={}                             #dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_ampSel=QComboBox()                          #create combo box to select antenna
        self.cb_ampSel.addItem('Manual')
        self.cb_ampSel.setToolTip("Select Calibrated Antenna")
        self.cb_ampSel.currentIndexChanged.connect(self.set_amp)
        
        self.cb_ampFreqSel=QComboBox()                      #create combo box to select antenna calibration frequency
        self.cb_ampFreqSel.setToolTip("Select Antenna Calibration Frequency")
        self.cb_ampFreqSel.currentIndexChanged.connect(self.set_ampGain)
        self.cb_ampFreqSel.setEnabled(False)
        
        #==========================================
        # import list of Preamps from antennas.csv
        #=========================================
        
        try:                                                #import list of calibrated antennas from antennas.csv
            with open('calibration/preampList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:                   #stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_ampSel.addItem(row[0])
                        self.cal_ampFile[row[0]]='calibration/preamps/'+row[1]
                        
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
        self.e_cal_ampGain.connect(self.e_cal_ampGain,SIGNAL('returnPressed()'),self.set_ampGain)
        fbox.addRow(QLabel("Amplifier Gain (dB)"),self.e_cal_ampGain)
        self.vert.addLayout(fbox)
           
    def _init_cable(self):	                #sets up amplifier settings dialog box
        #=======================================================================
        #
        #          Name:    _init_cable
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the cable calibration dialog box
        #
        #=======================================================================
        "Initialze cable setting dialog box"
        self.setWindowTitle("Cable Setup")
        fbox = QFormLayout()
        #=================================
        # calibrated Cable selection buttons
        #=================================
        fbox.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">Cable Loss</span>'))
        
        #create dictionaries to hold cal data
        self.cal_cableFile={}                                           #dictionary thats holds list of file names of calibrated antennas
        self.cal_cableFreqGain={}                                       #dictionary holds frequency and gain relationships of antenna
        
        #create combo boxes to hold calibrated values
        self.cb_cableSel=QComboBox()                                    #create combo box to select antenna
        self.cb_cableSel.addItem('Manual')
        self.cb_cableSel.setToolTip("Select Calibrated Cable")
        self.cb_cableSel.currentIndexChanged.connect(self.set_cable)
        
        self.cb_cableFreqSel=QComboBox()                                #create combo box to select antenna calibration frequency
        self.cb_cableFreqSel.setToolTip("Select Cable Calibration Frequency")
        self.cb_cableFreqSel.currentIndexChanged.connect(self.set_cableLoss)
        self.cb_cableFreqSel.setEnabled(False)
        
        #==========================================
        # import list of cables from cables.csv
        #=========================================
        
        try:                                                        #import list of calibrated antennas from antennas.csv
            with open('calibration/cableList.csv','r') as csvfile:
                reader=csv.reader(csvfile)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:                           #stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_cableSel.addItem(row[0])
                        self.cal_cableFile[row[0]]='calibration/cables/'+row[1]
                        
                    skipHeader=False
            csvfile.close()
        except:
            print 'Exception while attempting to open .csv file'
            
        fbox.addRow('Cable Type', self.cb_cableSel)
        fbox.addRow('Cable calibration frequency (MHz)',self.cb_cableFreqSel)
        
        #====================================
        # Manual cable line edit boxes
        #====================================
          
        self.e_cal_cableLoss = QLineEdit('0')
        self.e_cal_cableLoss.connect(self.e_cal_cableLoss,SIGNAL('returnPressed()'),self.set_cableLoss)
        fbox.addRow(QLabel("Cable Loss (dB)"),self.e_cal_cableLoss)

        self.vert.addLayout(fbox)
    
    def _init_sigGen(self):	                #sets up signal Generator settings dialog box
        #=======================================================================
        #
        #          Name:    _init_sigGen
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the Input generator calibration dialog box
        #
        #=======================================================================
        "Initialze signal generator setting dialog box"
        self.setWindowTitle(" Signal Generator Setup")
        fbox = QFormLayout()
        
        self.e_cal_inputPwr = QLineEdit('0')
        self.e_cal_inputPwr.connect(self.e_cal_inputPwr,SIGNAL('returnPressed()'),self.cal.set_inputPwr)
        fbox.addRow(QLabel("Tx Input Power (dBm)"),self.e_cal_inputPwr)
        
        self.vert.addLayout(fbox)
    
    def _init_specAn(self):                 #sets up the spectrum analyzer dialog box
        #=======================================================================
        #
        #          Name:    _init_specAn
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the spectrum analyzer settings dialog box
        #
        #=======================================================================
        "Initialze spectrum analyzer setting dialog box"
        self.setWindowTitle("Spectrum Analyzer Setup")
        fbox = QFormLayout()

        fbox.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">SignalHound BB60C\nSpectrum Analyzer</span>'))#add heading
        #RBW
        self.e_cal_sc_rbw  =QLineEdit('10')
        fbox.addRow(QLabel("RBW (kHz)"),self.e_cal_sc_rbw)
        #VBW
        self.e_cal_sc_vbw  =QLineEdit('10')
        fbox.addRow(QLabel("VBW (kHz)"),self.e_cal_sc_vbw)
        
        #Gain MAX=3 TODO: add automatic value correction
        hbox=QHBoxLayout()#create child hbox
        self.cb_autoGain = QCheckBox("Auto",checked=True)
        self.connect(self.cb_autoGain, SIGNAL('stateChanged(int)'), self.cal.set_specan_AutoGain)
        self.cb_autoGain.setToolTip("Set Automatic Gain Control")
        
        self.e_cal_gain=QLineEdit("0")
        self.e_cal_gain.setEnabled(False)
        
        hbox.addWidget(QLabel('Gain: Auto or 0-3'))
        hbox.addWidget(self.cb_autoGain)
        hbox.addWidget(self.e_cal_gain)
        fbox.addRow(hbox)
        
        #Attenuation MAX=30 TODO: add automatic value correction
        hbox=QHBoxLayout()#create child hbox
        self.cb_autoAtten = QCheckBox("Auto",checked=True)
        self.connect(self.cb_autoAtten, SIGNAL('stateChanged(int)'), self.cal.set_specan_autoAttenuation)
        self.cb_autoAtten.setToolTip("Set Automatic Attenuation Control")
        
        self.cb_cal_attenRef=QComboBox()
        self.cb_cal_attenRef.addItem('-50')
        self.cb_cal_attenRef.addItem('-40')
        self.cb_cal_attenRef.addItem('-30')
        self.cb_cal_attenRef.addItem('-20')
        self.cb_cal_attenRef.addItem('-10')
        self.cb_cal_attenRef.addItem('0')
        self.cb_cal_attenRef.addItem('10')
        self.cb_cal_attenRef.addItem('20')
        self.cb_cal_attenRef.addItem('30')
        self.cb_cal_attenRef.setCurrentIndex(5)
#         self.cb_cal_attenRef.currentIndexChanged.connect(self.cal.set_specan_autoAttenReference)
        
        self.cb_cal_attenRef.setEnabled(True)
        
        self.e_cal_atten=QLineEdit("30")
        self.e_cal_atten.setEnabled(False)
        
        hbox.addWidget(QLabel('Attenuation:'))
        hbox.addWidget(self.cb_autoAtten)
        hbox.addWidget(QLabel('Reference (dB)'))
        hbox.addWidget(self.cb_cal_attenRef)
        hbox.addWidget(QLabel('Manual (dB)'))
        hbox.addWidget(self.e_cal_atten)
        fbox.addRow(hbox)
        
        #Aquisition Detector type and scale
        hbox=QHBoxLayout()#create child hbox

        self.cb_cal_aqDet=QComboBox()
        self.cb_cal_aqDet.addItem('average')
        self.cb_cal_aqDet.addItem('min-max')
        self.cb_cal_aqDet.currentIndexChanged.connect(self.cal.set_specan_detectorType)
        
        self.cb_cal_aqScale=QComboBox()
        self.cb_cal_aqScale.addItem('log-scale')
        self.cb_cal_aqScale.addItem('log-full-scale')
        self.cb_cal_aqScale.addItem('lin-scale')
        self.cb_cal_aqScale.addItem('lin-full-scale')
        self.cb_cal_aqScale.currentIndexChanged.connect(self.cal.set_specan_detectorScale)
        
        
        hbox.addWidget(QLabel('Acquisition:'))
        hbox.addWidget(QLabel('Detector Type'))
        hbox.addWidget(self.cb_cal_aqDet)
        hbox.addWidget(QLabel('Scale'))
        hbox.addWidget(self.cb_cal_aqScale)
        fbox.addRow(hbox)
        
        self.vert.addLayout(fbox)
    
    def _init_fspl(self):	                #sets up FSPL settings dialog box
        #=======================================================================
        #
        #          Name:    _init_fspl
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the FSPL setup dialog box
        #
        #=======================================================================
        "Initialize fspl setting dialog box"
        
        self.setWindowTitle("Free Space Path Loss (FSPL) Setup")
        
        fbox = QFormLayout()
                
        fbox.addRow(QLabel('<span style=" font-size:10pt; font-weight:600;">FSPL setup</span>'))#add heading
        
        self.e_cal_fspl = QLineEdit(str(self.cal.cal_fspl))
        self.e_cal_fspl.connect(self.e_cal_fspl,SIGNAL('returnPressed()'),self.cal.set_fspl)
        self.e_cal_fspl.setEnabled(False)
        
        hbox=QHBoxLayout()
        hbox.addWidget(QLabel("FSPL (dB)"))
        
        self.cb_cal_fspl=QComboBox()
        self.cb_cal_fspl.addItem('Derived')
        self.cb_cal_fspl.addItem('Manual')
        self.cb_cal_fspl.currentIndexChanged.connect(self.set_fsplMode)
        
        hbox.addWidget(self.cb_cal_fspl)
        hbox.addWidget(self.e_cal_fspl)
        fbox.addRow(hbox)
        
        self.vert.addLayout(fbox)

    def _init_additional(self):	            #sets up signal Generator settings dialog box
        #=======================================================================
        #
        #          Name:    _init_additional
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    initializes the layout of the Additional Gain/Loss calibration dialog box
        #
        #=======================================================================
        "Initialze additional gain/loss dialog box"
    
        self.setWindowTitle("Aditional Gain/Loss")
        
        self.fbox = QGridLayout()
        
        self.fbox.addWidget(QLabel("Name: "),0,0)
        self.fbox.addWidget(QLabel("Gain/Loss "),0,1)
        
        self.e_cal_addName=QLineEdit('')
        self.e_cal_addGain=QLineEdit('0')
        
        #create add new element button
        b_add=QPushButton('Add')
        b_add.clicked.connect(self.add_additionalElement)
        b_add.setToolTip("Add new gain element") 
        
        
        self.fbox.addWidget(self.e_cal_addName,1,0)
        self.fbox.addWidget(self.e_cal_addGain,1,1)
        self.fbox.addWidget(b_add,1,3)
        
        #hold temporary values for keeping all additional elements 
        self.tempDict={}
        self.tempCalValue=0
        
        self.names=[]
        self.gains=[]   
        self.removeButtons=[]
        self.removeButtDict={}
        
        self.vert.addLayout(self.fbox)
        tbox=QLabel()
        tbox.wordWrap=True
        tbox.setText("When adding additional Gain Elements,\n Ensure all gains are Positive Numbers\n and all Losses are Negative Numbers")
        self.vert.addWidget(tbox)
        self.vert.addStretch()
        
    def click_cancel(self):	                #execute this code when user clicks cancel
        #=======================================================================
        #
        #          Name:    click_cancel
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function sets the behavior of the dialog box
        #                    when the user clicks the cancel button
        #
        #=======================================================================
        "cancel settings"

        #=======================================================================
        # antenna cancel settings
        #=======================================================================
        if self.fType=='antenna':
            pass
        #=======================================================================
        # cable cancel settings
        #=======================================================================
        elif self.fType=='cable':
            pass
        #=======================================================================
        # amplifier cancel settings
        #=======================================================================
        elif self.fType=='amp':
            pass
        #=======================================================================
        # FSPL cancel settings
        #=======================================================================
        elif self.fType=='fspl':
            pass
        #=======================================================================
        # Input power cancel settings
        #=======================================================================
        elif self.fType=='input':
            pass
        #=======================================================================
        # Spectrum analyzer cancel settings
        #=======================================================================
        elif self.fType=='specAn':
            pass
        #=======================================================================
        # signal generator cancel settings
        #=======================================================================
        elif self.fType=='sigGen':
            pass 
        #=======================================================================
        # Additional Gain/Loss Cancel settings
        #=======================================================================
        elif self.fType=='add':
            self.tempDict=self.cal.addGainLoss.copy()        #set temporay dicitonary back to cal's values
            self.tempCalValue=self.cal.cal_additionalGain    #set temporary calibration value back to cal's value
            self.refresh_additionalElements()                #refresh dialog boxes elements
        
        #exit setup dialog without saving values
        self.close()
        
    def click_ok(self):	                	#execute this code when user clicks OK
        #=======================================================================
        #
        #          Name:    click_ok
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    This function sets the behavior of the dialog box
        #                    when the user presses the OK button
        #
        #=======================================================================
        'set Functionality for when user clicks the ok button in a calibration dialog box'
        #=======================================================================
        # set functionality for antennas when clicking OK
        #=======================================================================
        if self.fType=='antenna':
            if self.rxtx=='tx':                                         #set up Tx antenna gain
                self.cal.cal_txGain=float(self.e_cal_AntGain.text())
                self.cal.gui_txGain.setText(str(self.cal.cal_txGain) + ' dBi')
                self.cal.gui_txType.setText(self.cb_antennaSel.currentText())
                self.cal.gui_txCalFreq.setText(self.calFreq)
            else:                                                       #setup Rx antenna gain  
                self.cal.cal_rxGain=float(self.e_cal_AntGain.text())
                self.cal.gui_rxGain.setText(str(self.cal.cal_rxGain)+ ' dBi')
                self.cal.gui_rxType.setText(self.cb_antennaSel.currentText())
                self.cal.gui_rxCalFreq.setText(self.calFreq)
                
        #=======================================================================
        # set functionality for cables when clicking OK
        #=======================================================================    
        elif self.fType=='cable':
            
            if self.rxtx=='tx':                                                     #set up Tx antenna gain
                self.cal.cal_txCableLoss=float(self.e_cal_cableLoss.text())
                self.cal.gui_txCableLoss.setText(str(self.cal.cal_txCableLoss) + ' dB')
                self.cal.gui_txCableType.setText(self.cb_cableSel.currentText())
                self.cal.gui_txCableCalFreq.setText(self.calFreq)
            else:                                                                   #setup Rx antenna gain  
                self.cal.cal_rxCableLoss=float(self.e_cal_cableLoss.text())
                self.cal.gui_rxCableLoss.setText(str(self.cal.cal_rxCableLoss)+ ' dB')  
                self.cal.gui_rxCableType.setText(self.cb_cableSel.currentText())  
                self.cal.gui_rxCableCalFreq.setText(self.calFreq)
                
        #=======================================================================
        # set functionality for amplifier when clicking OK
        #=======================================================================
        elif self.fType=='amp':
            self.cal.cal_ampGain=float(self.e_cal_ampGain.text())
            self.cal.gui_ampGain.setText(str(self.cal.cal_ampGain) + ' dB')
            self.cal.gui_ampType.setText(self.cb_ampSel.currentText())
            self.cal.gui_ampCalFreq.setText(self.calFreq)
            
        #=======================================================================
        # set functionality for FSPL when clicking OK
        #=======================================================================
        elif self.fType=='fspl':
            self.cal.set_fspl()
            self.cal.update_calibration()
        #=======================================================================
        # set functionality for spectrum analyser when clicking OK
        #=======================================================================
        elif self.fType=='specAn':
            self.cal.apply_specanSettings()
        
        #=======================================================================
        # set Additional Gains/Losses  when clicking OK
        #=======================================================================
        elif self.fType=='add':
            self.refresh_additionalElements()                #refresh elements in dialog box
            self.cal.addGainLoss=self.tempDict.copy()        #set cal dictionary to temporary value
            self.cal.cal_additionalGain=self.tempCalValue    #set cal Additional Gain/Loss value to temporary value
            self.cal.update_calibration()
            
            self.cal.gui_additionalCnt.setText(str(len(self.cal.addGainLoss)))
            
            #create string to hold the values of the additional gain elements
            namesString=""
            for i in self.cal.addGainLoss:
                namesString=namesString+str(i)+"<br/>" 
            #create list of Additional Gain/Loss elements in GUI
            self.cal.gui_addNames.setText(namesString)
            
            namesString=""
            for i in self.cal.addGainLoss:
                namesString=namesString+str(self.cal.addGainLoss[i]) +" dB<br/>" 
            #create list of Additional Gain/Loss element's gains in GUI
            self.cal.gui_addGains.setText(namesString)
        #=======================================================================
        # set functionality for Signal generator when clicking OK
        #=======================================================================
        elif self.fType=='sigGen':
            
            #set input power to seleced value
            self.cal.cal_inputPwr=float(self.e_cal_inputPwr.text())
            self.cal.gui_inputPwr.setText(str(self.cal.cal_inputPwr)+" dBm")
        
            self.cal.update_calibration()
            
#==================================================
#on clicking "OK" in setup dialog box execute this code
# this accepts the test parameters
#==================================================
        """convert values to float, complain if get an exception
        """
        self.close()

    def set_antenna(self):	        	    #import Calibrated antenna info
        #=======================================================================
        #
        #          Name:    set_antenna
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function controls the behavior when the player chooses
        #                    an antenna from the drop down menu
        #
        #=======================================================================
        
        currentAnt=self.cb_antennaSel.currentText()
        print "Calibrated Antenna Set to " + currentAnt
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_antennaFreqSel.clear()
        self.cal_antennaFreqGain.clear()
        
        #insert a blank space as default value
        self.cb_antennaFreqSel.addItem("")
        
        
        #populate 
        if self.cb_antennaSel.currentText()!='Manual':
            self.e_cal_AntGain.setEnabled(False)
            self.cb_antennaFreqSel.setEnabled(True)
            try:
                with open(self.cal_antFile[str(currentAnt)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    
                    skipHeader=True
                    self.cb_antennaFreqSel.addItem('Auto')      #create "auto" setting for antenna gain selection
                    
                    for row in reader:
                        if skipHeader==False:                   #stop app from importing csv header
                            self.cal_antennaFreqGain[row[0]]=row[1];
                            
                            self.cb_antennaFreqSel.addItem(row[0])
                            
                            if(self.rxtx=='rx'):
                                if(row[3]!=""):
                                    self.cal.cal_antDiameter=row[3]   
                                
                        skipHeader=False
                csvFile.close()
                self.cb_antennaFreqSel.setCurrentIndex(1)
                
            except:
                print "Exception when attempting to open "+self.cal_antFile[str(currentAnt)]
        else:
            self.e_cal_AntGain.setEnabled(True)
            self.cb_antennaFreqSel.setEnabled(False)
            
    def get_antennaGain(self,freq):                #select calibration Gain for antenna
        #=======================================================================
        #
        #          Name:    get_antennaGain
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the gain for an antenna when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================

        if str(self.cb_antennaFreqSel.currentText())=='Auto':                       #if frequency set to auto select the closest frequency with the highest gain
            
            bestVal=self.get_bestValue2(self.cal_antennaFreqGain,testfreq=freq)                #fetch closest frequency to the test frequency, if inbetween to frequencies select freq w/ largest gain

            return float(self.cal_antennaFreqGain[str(int(bestVal))])
        else:
            return float(self.e_cal_AntGain.text())
        
    def get_ampGain(self,freq):                #select calibration Gain for antenna
        #=======================================================================
        #
        #          Name:    get_ampGain
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the gain for an amplifier when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================

        if str(self.cb_ampFreqSel.currentText())=='Auto':                       #if frequency set to auto select the closest frequency with the highest gain
            
            bestVal=self.get_bestValue2(self.cal_ampFreqGain,testfreq=freq)                #fetch closest frequency to the test frequency, if inbetween to frequencies select freq w/ largest gain

            return float(self.cal_ampFreqGain[str(int(bestVal))])
        else:
            return float(self.e_cal_ampGain.text())
        
    def get_cableLoss(self,freq):                #select calibration Gain for antenna
        #=======================================================================
        #
        #          Name:    get_cableLoss
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the loss for a cable when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================

        if str(self.cb_cableFreqSel.currentText())=='Auto':                       #if frequency set to auto select the closest frequency with the highest gain
            
            bestVal=self.get_bestValue2(self.cal_cableFreqGain,testfreq=freq)                #fetch closest frequency to the test frequency, if inbetween to frequencies select freq w/ largest gain

            return float(self.cal_cableFreqGain[str(int(bestVal))])
        else:
            return float(self.e_cal_cableLoss.text())
        
                    
    def set_antennaGain(self):	    	    #select calibration Gain for antenna
        #=======================================================================
        #
        #          Name:    set_antennaGain
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the gain for an antenna when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================
        gainTypeMsg=""
        if self.cb_antennaSel.currentText()!='Manual':
            #===================================================================
            # Auto
            #===================================================================
            if str(self.cb_antennaFreqSel.currentText())=='Auto':                       #if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_antennaFreqGain,self.cal.cal_freq)                #fetch closest frequency to the test frequency, if inbetween to frequencies select freq w/ largest gain
                print "bestval: ", bestVal
                
                gain=0
                
                
                if bestVal["low"]==0:
                    #if test frequency is an exact match to a calibrated frequency set to that gain
                    gain=self.cal_antennaFreqGain[str(bestVal["high"])]
                    gainTypeMsg="(Auto)"
                else:
                    #interpolate gain from surrounding values
                    gain = self.interp(self.cal.cal_freq/1e6, bestVal["low"], float(self.cal_antennaFreqGain[str(bestVal["low"])]), bestVal["high"], float(self.cal_antennaFreqGain[str(bestVal["high"])]))
                    gainTypeMsg="(Auto)(Interpolated)"
                    
                print "gain: ", gain
                if self.rxtx=='tx':  
                    self.cal.cal_txGain=float(gain)  #set gain
                    
                    self.e_cal_AntGain.setText(str(self.cal.cal_txGain))                 #set text in tab

                else:   
                    self.cal.cal_rxGain=float(gain)
                    self.e_cal_AntGain.setText(str(self.cal.cal_rxGain))

                    
                self.calFreq = str(self.cal.cal_freq/1e6)+" MHz "+gainTypeMsg           #set gui display Frequency value in MHz
            #===================================================================
            # select Gain selected from list
            #===================================================================
            else:              
                currentFreq=str(self.cb_antennaFreqSel.currentText())                   #hold selected frequency
                
                if currentFreq in self.cal_antennaFreqGain:
                    
                    if self.rxtx=='tx':
                        self.cal.cal_txGain=float(self.cal_antennaFreqGain[currentFreq])
                        self.e_cal_AntGain.setText(str(self.cal.cal_txGain))
                    else:
                        self.cal.cal_rxGain=float(self.cal_antennaFreqGain[currentFreq])
                        self.e_cal_AntGain.setText(str(self.cal.cal_rxGain))
                else:
                    if self.rxtx=='tx':
                        self.cal.cal_txGain=float(self.e_cal_AntGain.text())
                    else:
                        self.cal.cal_rxGain=float(self.e_cal_AntGain.text())
                        
                self.calFreq = self.cb_antennaFreqSel.currentText()+ " MHz (Manual)"    #set gui display Frequency value in MHz
        #=======================================================================
        # Manually enetered gain
        #=======================================================================
        else:                  
            if self.rxtx=='tx':
                self.cal.cal_txGain=float(self.e_cal_AntGain.text())
            else:
                self.cal.cal_rxGain=float(self.e_cal_AntGain.text())
                
            self.calFreq = 'Manually Entered Gain'                                      #set gui display Frequency value

        self.cal.update_displayValues() 
        
    def set_cable(self):	        	    #import Calibrated cable info
        #=======================================================================
        #
        #          Name:    set_cable
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function controls the behavior when the player chooses
        #                    an cable from the drop down menu
        #
        #=======================================================================
        
        currentCable=self.cb_cableSel.currentText()
        print "Calibrated Cable Set to " + currentCable
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_cableFreqSel.clear()
        self.cal_cableFreqGain.clear()
        
        self.cb_cableFreqSel.addItem("")
        
        #=======================================================================
        # get calibrated gain values from csv file
        #=======================================================================
        if self.cb_cableSel.currentText()!='Manual':
            self.e_cal_cableLoss.setEnabled(False)
            self.cb_cableFreqSel.setEnabled(True)
            try:
                with open(self.cal_cableFile[str(currentCable)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    self.cb_cableFreqSel.addItem('Auto')                        #add auto select frequency option
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:                                   #stop app from importing csv header
                            self.cal_cableFreqGain[row[0]]=row[1];
                            
                            self.cb_cableFreqSel.addItem(row[0])
                            
                        skipHeader=False
                csvFile.close()
                self.cb_cableFreqSel.setCurrentIndex(1)
            except:
                print "Exception when attempting to open "+self.cal_cableFile[str(currentCable)]
        else:
            self.e_cal_cableLoss.setEnabled(True)
            self.cb_cableFreqSel.setEnabled(False)
    
    def set_cableLoss(self):	    	    #select calibration Loss for Cable
        #=======================================================================
        #
        #          Name:    set_cableLoss
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the loss for a cable when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================
        
        if self.cb_cableSel.currentText()!='Manual':
            #===================================================================
            # Auto
            #===================================================================
            if str(self.cb_cableFreqSel.currentText())=='Auto':                                             #if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_cableFreqGain,self.cal.cal_freq)
                gain=0
                
                if bestVal["low"]==0:
                    gain=self.cal_cableFreqGain[str(bestVal["high"])]
                    gainTypeMsg="(Auto)"
                else:
                    #interpolate gain from surrounding values
                    gain = self.interp(self.cal.cal_freq/1e6, bestVal["low"], float(self.cal_cableFreqGain[str(bestVal["low"])]), bestVal["high"], float(self.cal_cableFreqGain[str(bestVal["high"])]))
                    gainTypeMsg="(Auto)(Interpolated)"
                
                print "Cable Calibration frequency set to " + str(gain) + " MHz"
                
                if self.rxtx=='tx':
                    self.cal.cal_txCableLoss=float(gain)
                    self.e_cal_cableLoss.setText(str(self.cal.cal_txCableLoss))
                    print '\tTx Cable Loss set to '+str(gain) + " dB\n"
                else:
                    self.cal.cal_rxCableLoss=float(gain)
                    self.e_cal_cableLoss.setText(str(self.cal.cal_rxCableLoss))
                    print '\tRx Cable Loss set to '+str(gain) + " dB\n"
                self.calFreq = str(self.cal.cal_freq/1e6)+" MHz "+gainTypeMsg 
                                                        #set gui display Frequency value in MHz
            #===================================================================
            # Gain Selected from menu
            #===================================================================
            else:
                currentFreq=str(self.cb_cableFreqSel.currentText())
                
                if currentFreq in self.cal_cableFreqGain:
                    print "Cable Calibration frequency set to "+ currentFreq+ " MHz"
                    if self.rxtx=='tx':
                        print '\tTx Cable Loss set to '+str(self.cal_cableFreqGain[currentFreq]) + " dB\n"
                        self.cal.cal_txCableLoss=float(self.cal_cableFreqGain[currentFreq])
                        self.e_cal_cableLoss.setText(str(self.cal.cal_txCableLoss))
                    else:
                        print '\tRx Cable Loss set to '+str(self.cal_cableFreqGain[currentFreq]) + " dB\n"
                        self.cal.cal_rxCableLoss=float(self.cal_cableFreqGain[currentFreq])
                        self.e_cal_cableLoss.setText(str(self.cal.cal_rxCableLoss))
                    self.calFreq = self.cb_cableFreqSel.currentText()+" MHz (Manual)"                       #set gui display Frequency value in MHz
        else:
            
            self.cal_cableLoss=float(self.e_cal_cableLoss.text())
            self.calFreq = "Manually Entered Cable Loss"                                                    #set gui display Frequency value in MHz
        self.cal.update_displayValues() 
           
    def set_amp(self):	            	                                         #import Calibrated Amplifier info
        #=======================================================================
        #
        #          Name:    set_amp
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function controls the behavior when the player chooses
        #                    an amplifier from the drop down menu
        #
        #=======================================================================
        
        currentAmp=self.cb_ampSel.currentText()
        print "\nCalibrated Amplifier Set to " + currentAmp
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_ampFreqSel.clear()
        self.cal_ampFreqGain.clear()
        
        self.cb_ampFreqSel.addItem("")                                          #add blank item as default to amplifier combo box
        
        #=======================================================================
        # get calibrated gain values from csv file
        #=======================================================================
        if self.cb_ampSel.currentText()!='Manual':
            self.e_cal_ampGain.setEnabled(False)
            self.cb_ampFreqSel.setEnabled(True)
            try:
                with open(self.cal_ampFile[str(currentAmp)],'r') as csvFile:
                    reader=csv.reader(csvFile)
                    self.cb_ampFreqSel.addItem('Auto')                          #add auto select frequency
                    
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:                                   #stop app from importing csv header
                            self.cal_ampFreqGain[row[0]]=row[1];
                            
                            self.cb_ampFreqSel.addItem(row[0])
                            
                        skipHeader=False
                csvFile.close()
                self.cb_ampFreqSel.setCurrentIndex(1)
            except:
                print "Exception when attempting to open "+self.cal_ampFile[str(currentAmp)]
        else:
            self.e_cal_ampGain.setEnabled(True)
            self.cb_ampFreqSel.setEnabled(False)
 
    def set_ampGain(self):  	    	                                          #select calibration Gain for amplifier
        #=======================================================================
        #
        #          Name:    set_ampGain
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the gain for a amplifier when the user
        #                    selects a calibraiton frequency
        #
        #=======================================================================
        'apply correct gain to preamp for selected frequency'
        
        if self.cb_ampSel.currentText()!='Manual':                                      #apply gain from automatically selected frequency
            #===================================================================
            # Auto
            #===================================================================
            if str(self.cb_ampFreqSel.currentText())=='Auto':                           #if frequency set to auto select the closest frequency with the highest gain
                
                bestVal=self.get_bestValue(self.cal_ampFreqGain,self.cal.cal_freq)                    #get closest frequency form list of calibrated frequencies
                
                gain=0
                
                if bestVal["low"]==0:
                    gain=self.cal_ampFreqGain[str(bestVal["high"])]
                    gainTypeMsg="(Auto)"
                else:
                    #interpolate gain from surrounding values
                    gain = self.interp(self.cal.cal_freq/1e6, bestVal["low"], float(self.cal_ampFreqGain[str(bestVal["low"])]), bestVal["high"], float(self.cal_ampFreqGain[str(bestVal["high"])]))
                    gainTypeMsg="(Auto)(Interpolated)"
                
                self.cal.cal_ampGain=float(gain)     #set amplifier gain in cal Calibrator object
                
                self.e_cal_ampGain.setText(str(self.cal.cal_ampGain))                   #change text in line edit box

                #print info to console
                print "\nAmplifier Calibration frequency set to " + str(self.cal.cal_freq/1e6) + "MHz\n"
                print "\tAmplifer Gain set to "+ str(self.cal.cal_ampGain)
                self.calFreq = str(self.cal.cal_freq/1e6)+" MHz "  +     gainTypeMsg                #set gui display Frequency value in MHz
            #===================================================================
            # gain selected from list
            #===================================================================
            else:                                                                       #apply gain from manually selected frequency
            
                currentFreq=str(self.cb_ampFreqSel.currentText())                       #hold the selected frequency in convinient variable
                
                if currentFreq in self.cal_ampFreqGain:                                 #check if selected frequency exists in cal_ampFreqGain dictionary
                    
                    print "\nAmplifier Calibration frequency set to "+ currentFreq+ "MHz\n"
                    self.cal.cal_ampGain=float(self.cal_ampFreqGain[currentFreq])       #apply gain to cal Calibrator object
                    self.e_cal_ampGain.setText(str(self.cal.cal_ampGain))               #set text in line edit box
                    print "\tAmplifer Gain set to "+ str(self.cal.cal_ampGain)
                    self.calFreq = self.cb_ampFreqSel.currentText()+" MHz (Manual)"     #set gui display Frequency value in MHz
        else:
            self.cal.cal_ampGain=float(self.e_cal_ampGain.text())                       #apply manually entered gain to amplifier
            self.calFreq = "Manually Entered Gain"                                      #set gui display Frequency value in MHz
        self.cal.update_displayValues()                                                 #update calibration function
            
    def set_fsplMode(self):	    	                                                   #set manual or derived mode for FSPL Loss
        #=======================================================================
        #
        #          Name:    set_fsplMode
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function set the mode for deriving the FSPL wehn the user
        #                    selects "manual" of "derived" fromt he drop down menu
        #
        #=======================================================================
        if str(self.cb_cal_fspl.currentText())=='Manual':
            self.e_cal_fspl.setEnabled(True)
            self.cal.set_fspl()
        else:
            self.e_cal_fspl.setEnabled(False)
            self.cal.set_fspl() 
        
    def refresh_additionalElements(self):	#refresh elements in the Additional Gain/Loss Dialog box
        #=======================================================================
        #
        #          Name:    refresh_additionalElements
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this function refreshes the list of additional gain/loss 
        #                    elements when they are changed
        #
        #=======================================================================
        'Refresh addGainLoss dictionary to display correct information'
 
        #=======================================================================
        # clear data GUI display to prevent double loading data
        #=======================================================================
        
        for i in self.names:
            if i!=None:
                i.deleteLater()
        self.names=[None]      
        
        for i in self.gains:
            if i!=None:
                i.deleteLater()
        self.gains=[None]
        
        for i in self.removeButtons:
            if i!=None:
                i.deleteLater()
        self.removeButtons=[None]
        
        #=======================================================================
        # create new labels and apply to dialog box
        #=======================================================================
        place=0
        #for i in self.cal.addGainLoss:
        for i in self.tempDict:
            self.names.insert(place,QLabel(i))

            self.fbox.addWidget(self.names[place],place+2,0)
            
            #self.gains.append(QLabel(str(self.cal.addGainLoss[i])))
            self.gains.insert(place,QLabel(str(self.tempDict[i])))

            self.fbox.addWidget(self.gains[place],place+2,1)
            
            self.removeButtons.insert(place,QPushButton('Remove '+i))

            self.removeButtons[place].clicked.connect(lambda: self.remove_additionalElement(place))
            
            self.fbox.addWidget(self.removeButtons[place],place+2,3)
            
            self.removeButtDict[place]=i
            
            place=place+1
      
    def add_additionalElement(self):	    #add Additional Gain/Loss Element
        #=======================================================================
        #
        #          Name:    add_additionalElement
        #
        #    Parameters:    None
        #
        #        Return:    None
        #
        #   Description:    this functions adds additional elements to the dictionary
        #                    when the user clicks the "Add" button
        #
        #=======================================================================
        'Add a new gain element to additional gain loss'

        
        name=str(self.e_cal_addName.text())#set name form user input
            
        #corretct if element already exists    
        if name in self.tempDict:
            self.tempCalValue=(self.tempCalValue-self.tempDict[name])
            
        #self.cal.addGainLoss[name]=float(self.e_cal_addGain.text())#add name and gain to cal dictionary
        self.tempDict[name]=float(self.e_cal_addGain.text())#add name and gain to cal dictionary
        
        #self.cal.cal_additionalGain=(self.cal.cal_additionalGain+self.cal.addGainLoss[name])# add elements gain/loss to calibration equation
        self.tempCalValue=(self.tempCalValue+self.tempDict[name])# add elements gain/loss to calibration equation
        
        #clear dialog boxes line edits
        self.e_cal_addName.setText('')
        self.e_cal_addGain.setText('0')
        #refresh display in additional gain/loss box

        
        self.refresh_additionalElements()
        
    def remove_additionalElement(self,Ditem):#remove Additional Gain/loss Element
        #=======================================================================
        #
        #          Name:    remove_additionalElement
        #
        #    Parameters:    (dictionary element)Ditem
        #
        #        Return:    None
        #
        #   Description:    this function removes an element form the dictionary 
        #                    when the user clicks the "Remove XXX" button
        #
        #=======================================================================
        'Removes element from additional Gain Loss List'
        #TODO: Correct removeal(deletes highest value of place variable instead of selected)
        #this has something to do with the way the buttons call this function
        
        #correct for dictionary
        Ditem=Ditem-1
        
        #subtract element for calibration equation
        self.tempCalValue=(self.tempCalValue-self.tempDict[self.removeButtDict[Ditem]])
        #self.cal.cal_additionalGain=(self.cal.cal_additionalGain-self.cal.addGainLoss[self.removeButtDict[Ditem]])
        
        #delete element in cal dictionary
        del(self.tempDict[self.removeButtDict[Ditem]])
        #del(self.cal.addGainLoss[self.removeButtDict[Ditem]])
        #refresh Additional Gain/Loss display

        
        self.refresh_additionalElements()
    
    def get_bestValue2(self,gainDict,testfreq):#get closest value to selected test frequency
        #=======================================================================
        #
        #          Name:    get_bestValue2
        #
        #    Parameters:    (disctionary) gainDict
        #
        #        Return:    (int)
        #
        #   Description:    this function finds the closest frequency to a
        #                    newly selected frequency for elements that are set to auto
        #                    
        #                    if the closest value is between 2 calibrated frequencies
        #                    the frequency with the highest gain will be selected
        #
        #=======================================================================
        'get closest value to selected test frequency, if value is between to frequencies the frequency with the highest gain will be chosen'
        
        bestVal=9999999#set very high initial value to be replaced on first iteration
        
        #iterate through all values in gain dictionary and test against current best value
        for freq in sorted(gainDict):
            if abs(int(freq)-testfreq/1e6)<abs((int(bestVal)-testfreq/1e6)):#if (current frequency)-(test frequency)<(best value)-(test frequency)
                bestVal=freq
            elif abs(int(freq)-testfreq/1e6)==abs((int(bestVal)-testfreq/1e6)):#if (current frequency)-(test frequency)==(best value)-(test frequency): get frequency with higher gain
                
                if gainDict[str(freq)]>=gainDict[str(int(bestVal))]:
                    bestVal=freq
        return int(bestVal)
    
    def get_bestValue(self,gainDict,testFreq):#get closest value to selected test frequency
        #=======================================================================
        #
        #          Name:    get_bestValue
        #
        #    Parameters:    (disctionary) gainDict (testFreq) integer
        #
        #        Return:    (int)
        #
        #   Description:    this function finds the closest frequency to a
        #                    newly selected frequency for elements that are set to auto
        #                    
        #                    if the closest value is between 2 calibrated frequencies
        #                    the frequency with the highest gain will be selected
        #
        #=======================================================================
        'get closest value to selected test frequency, if value is between to frequencies the frequency with the highest gain will be chosen'
        
        retval = {"low":0,"high":0}
        retval["high"]=9999999#set very high initial value to be replaced on first iteration

        #iterate through all values in gain dictionary and test against current best value
        for freq in sorted(gainDict):
            #===================================================================
            # Exact match
            #===================================================================
#             if int(freq)==(self.cal.cal_freq/1e6):
            if int(freq)==(testFreq/1e6):
                retval["low"]=0
                retval["high"]=int(freq)
                break;
            #===================================================================
            # New Value is closer to target frequency
            #===================================================================
#             elif abs(int(freq)-self.cal.cal_freq/1e6)<abs((int(retval["high"])-self.cal.cal_freq/1e6)):#if (current frequency)-(test frequency)<(best value)-(test frequency)
            elif abs(int(freq)-testFreq/1e6)<abs((int(retval["high"])-testFreq/1e6)):#if (current frequency)-(test frequency)<(best value)-(test frequency)
               
                retval["low"]=int(retval["high"])
                retval["high"]=int(freq)
                
            #===================================================================
            # New Value is just as close as previous value to target freq
            #===================================================================
#             elif abs(int(freq)-self.cal.cal_freq/1e6)==abs((int(retval["high"])-self.cal.cal_freq/1e6)):#if (current frequency)-(test frequency)==(best value)-(test frequency): get frequency with higher gain
            elif abs(int(freq)-testFreq/1e6)==abs((int(retval["high"])-testFreq/1e6)):#if (current frequency)-(test frequency)==(best value)-(test frequency): get frequency with higher gain
               
                
                if freq>int(retval["high"]):
                    retval["low"]=int(retval["high"])
                    retval["high"]=int(freq)
                    
        if retval["low"]>retval["high"]:
            temp=retval["low"]
            retval["low"]=retval["high"]
            retval["high"]=temp        
            
            for freq in sorted(gainDict):
                if (abs(int(retval["low"])-int(freq))<abs(int(retval["low"])-int(retval["high"])))and(int(freq)!=retval["low"]):#if (current frequency)-(test frequency)<(best value)-(test frequency)
                    retval["high"]=int(freq)

        return retval   

                     

    def interp(self,x,x1,y1,x3,y3): 
        #=======================================================================
        #
        #          Name:    interp
        #
        #    Parameters:    (float) x, x1, y1, x3, y3
        #
        #        Return:    (float) retval
        #
        #   Description:    returns the linear interpolation at point x between points (x1,y1) and (x3,y3)
        #
        #=======================================================================
        retval=(((x-x1)*(y3-y1))/(x3-x1))+y1
        return retval     
            
            
            
#End of File