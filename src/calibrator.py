
import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import multiprocessing,logging


from SignalHound import SignalHound
import math



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
        self.cal_txGain=0#rx antenna gain in dB
        
        self.cal_ampGain=0#input power to Tx
        #cable
        self.cal_cableLoss=0#gain loss due to cable in dB
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
        self.cal_sc_sweepTime=.025#sweep time setting
        self.cal_sc_rbwType="native"# resolution bandwidth type, see signal hound api-datasheet for details
        self.cal_sc_rejection="no-spur-reject"#spurious data rejection setting
        #configure center/ span
        self.cal_cp_center=100e6#sweep center frequency in Hz
        self.cal_cp_span=200e3#sweep span in Hz

    def calibrate_data(self,data):#calibrate collected data
        '''
        Calibrate Collected Data
        '''
        #TODO data calibration routine
        temp=(data-self.cal_inputPwr)#subtract input power in dBm
        
        temp=temp-self.cal_ampGain#subtract preamp gain
        
        temp=temp-self.cal_txGain#Subtract tx antenna gain
        
        temp=temp-self.cal_fspl#subtract free space  loss
                
        temp=temp-self.cal_cableLoss#subtract cable loss
        
        temp=temp-self.cal_additionalGain#subtract any additional gain/loss

        return temp

    def create_GUICal(self,tab):
        '''
        Create Graphical User Interface that is more intuative
        '''
        grid=QGridLayout()#create main box of tab
        #grid.setAlignment(QalignCenter)
        icon=QIcon('images/antenna-2.png')
        
        b_rx=QPushButton('');
        b_tx=QPushButton('');
        b_FSPL=QPushButton('FSPL');
        arrow=QLabel()
        arrowPix=QPixmap('images/Black_Right_Arrow.png')
        arrowPix=arrowPix.scaledToHeight(24)
        arrow.setPixmap(arrowPix)
        b_rx.setIcon(icon)
        b_rx.setIconSize(QSize(24,24))
        
        b_tx.setIcon(icon)
        b_tx.setIconSize(QSize(24,24))
        
        grid.addWidget(b_tx,1,1)
        grid.addWidget(arrow,1,2)
        grid.addWidget(b_FSPL,1,3)
        grid.addWidget(arrow,1,4)
        grid.addWidget(b_rx,1,5)
       
        tab.setLayout(grid)

    def create_calibrationTab(self,tab):#Create Calibration TAB
        
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
        
        self.uptadeCalFunction()  
            
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
        
    def uptadeCalFunction(self):
        
        self.calFunctionDisplay.setText('<span style=" color:light-gray; font-size:13pt; font-weight:600;">(Data)<br/> - ('+str(self.cal_inputPwr)+ ' dBm): Input_Power<br/> - (' +str(self.cal_fspl)+' dB): FSPL<br/> - ('+str(self.cal_txGain)+' dB): Antenna_gain<br/> - ('+str(self.cal_ampGain)+' dB): PreAmp_Gain<br/> - ('+str(self.cal_cableLoss)+' dB): Cable_Loss<br/> - ('+str(self.cal_additionalGain)+' dB): Addidtional_Gain</span>')
        
        if self.calibrate_data(0)>=0:
            self.calFunctionAnswerDisplay.setText('<span style=" color:white; font-size:20pt; font-weight:1000;">Total Calibration:   +'+str(self.calibrate_data(0))+' (dB)</span>')
        else:       
            self.calFunctionAnswerDisplay.setText('<span style=" color:white; font-size:20pt; font-weight:1000;">Total Calibration:   '+str(self.calibrate_data(0))+' (dB)</span>')
       
    def on_cal_reset(self):#reset calibration settings to default
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
        self.cal_sc_sweepTime=.1#sweep time setting
        self.cal_sc_rbwType="native"# resolution bandwidth type, see signal hound api-datasheet for details
        self.cal_sc_rejection="no-spur-reject"#spurious data rejection setting
        #configure center/ span
        self.cal_cp_center=100e6#sweep center frequency in Hz
        self.cal_cp_span=200e3#sweep span in Hz
     
    def on_cal_setFspl(self):

        if str(self.cb_cal_fspl.currentText())=='Manual':
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_fspl=float(self.e_cal_fspl.text())
            self.cal_freq=float(self.e_cal_freq.text())
        else:
            self.cal_dist=float(self.e_cal_dist.text())
            self.cal_freq=float(self.e_cal_freq.text())
            self.cal_fspl= -(20*math.log10(self.cal_freq*1000000)+(20*math.log10(float(self.e_cal_dist.text())))+20*math.log10((4*np.pi)/299792458))       
            self.e_cal_fspl.setText(str(self.cal_fspl))

        self.on_cal_selectAmpGain()
        self.on_cal_selectAntennaGain()
        self.on_cal_selectCableLoss()
        self.uptadeCalFunction()
 
    def on_cal_selectFsplMode(self):
        if str(self.cb_cal_fspl.currentText())=='Manual':
            self.e_cal_fspl.setEnabled(True)
            self.on_cal_setFspl()
        else:
            self.e_cal_fspl.setEnabled(False)
            self.on_cal_setFspl() 
        
        self.uptadeCalFunction()
             
    def on_cal_apply(self):#TODO: add class parameters to modify  thes set up SA
        #TODO: add automatic parameter correction in case of user error
        
        #=======================================================================
        # set calibration variables
        #=======================================================================
        #cable loss
        self.cal_cableLoss=float(self.e_cal_cableLoss.text())
        #distance
        self.cal_dist=float(self.e_cal_dist.text())
        #antenna
        self.cal_txGain=float(self.e_cal_txGain.text())
        #input power
        self.cal_ampGain=float(self.e_cal_ampGain.text())
        #FSPL
        self.cal_fspl=float(self.e_cal_fspl.text())
        
        
        #=======================================================================
        # send calibration to signal hound
        #=======================================================================
        #gain
        if self.cb_autoGain.isChecked():
            self.cal_gain='auto'
        else:
            #if user sets gain >3 it will be automatically corrected to 3
            if float(self.e_cal_gain.text())>3:
                self.e_cal_gain=3
                self.cal_gain=3
            else:
                self.cal_gain=int(self.e_cal_gain.text())
        self.worker.specan.sh.configureGain(self.cal_gain)#set gain in specan
        
        #attenuation
        if self.cb_autoAtten.isChecked():
            self.cal_level_atten="auto"
        else:
            self.cal_level_atten=float(self.e_cal_atten.text())
            
        self.worker.specan.sh.configureLevel(self.cal_level_ref , self.cal_level_atten)#set attenuation in specan
        
        #log or linear units
        self.worker.specan.sh.configureProcUnits("log")
        
        #data units
        self.worker.specan.sh.configureAcquisition(str(self.cal_aq_detector),str(self.cal_aq_scale))
        self.worker.specan.sh.configureSweepCoupling((int(self.e_cal_sc_rbw.text()))*1000,(int(self.e_cal_sc_vbw.text()))*1000,0.1,"native","spur-reject") 
        self.uptadeCalFunction()
        
    def on_cal_autoGain(self):#toggle auto-gain settings
        if self.cb_autoGain.isChecked():
            print "Gain set to AUTO"
            self.cal_gain='auto'
            self.e_cal_gain.setEnabled(False)
        else:
            print "Gain set to ManuaL"
            self.e_cal_gain.setEnabled(True)
        self.uptadeCalFunction()
        
    def on_cal_autoAtten(self):#toggle auto-gain settings
        if self.cb_autoAtten.isChecked():
            print "Attenuation set to Auto"
            self.cal_level_atten='auto'
            self.e_cal_atten.setEnabled(False)
            self.cb_cal_attenRef.setEnabled(True)
        else:
            print "Attenuation set to Manual"
            self.e_cal_atten.setEnabled(True)
            self.cb_cal_attenRef.setEnabled(False)
        self.uptadeCalFunction()
            
    def on_cal_autoAtten_ref(self):#set reference for auto attenuation
        
        self.cal_level_ref=int(self.cb_cal_attenRef.currentText())
        print "Attenuation reference set to " + str(self.cal_level_ref)

    def on_cal_detectorType(self):#set detector type for acquisition
        self.cal_aq_detector=self.cb_cal_aqDet.currentText()
        print "Aquisition detector type set to " + str(self.cal_aq_detector)
  
    def on_cal_setInputPwr(self):
        
        self.cal_inputPwr=float(self.e_cal_inputPwr.text())
        
        self.uptadeCalFunction()
  
    def get_bestValue(self,gainDict):
        bestVal=9999999
        for freq in sorted(gainDict):
            if abs(int(freq)-self.cal_freq)<abs((int(bestVal)-self.cal_freq)):
                bestVal=freq
            elif abs(int(freq)-self.cal_freq)==abs((int(bestVal)-self.cal_freq)):
                
                if gainDict[str(freq)]>=gainDict[str(int(bestVal))]:
                    bestVal=freq
        return int(bestVal)
  
    def on_cal_selectAntenna(self):#import Calibrated antenna info
        
        currentAnt=self.cb_antennaSel.currentText()
        print "Calibrated Antenna Set to " + currentAnt
        
        #clear antenna frequency calibration dictionaries and set to re-populate
        self.cb_antennaFreqSel.clear()
        self.cal_antennaFreqGain.clear()
        
        self.cb_antennaFreqSel.addItem("")
        
        
        
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
        self.uptadeCalFunction()
        
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
               
        self.uptadeCalFunction()
        
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
        
        self.uptadeCalFunction()
        
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
        self.uptadeCalFunction()
        
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
        self.uptadeCalFunction()
    
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
        self.uptadeCalFunction()
    
    def on_cal_setAdditionalGain(self):#set any additional gain parameters
        
        self.cal_additionalGain=float(self.e_cal_additionalGain.text())
            
        self.uptadeCalFunction()
        
    def on_cal_scale(self):#set detector type for acquisition
        self.cal_aq_scale=self.cb_cal_aqScale.currentText()
        print "Aquisition scale set to " + str(self.cal_aq_scale)
        self.uptadeCalFunction()
