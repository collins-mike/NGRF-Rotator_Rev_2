"""
RF Rotator
Copyright 2013 Travis Fagerness
v2.0 update by mike Collins
"""
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
from worker import *
from setup import *
from specan import *
from arcus import *
from calibrate import *

import numpy as np
import math
import time
from pip._vendor.requests.packages.chardet.latin1prober import FREQ_CAT_NUM

#===============================================================================
# adjust matplotlib display settings
#===============================================================================
matplotlib.rcParams.update({'font.size': 9})

version = "2.0"
year = "2017"
author = "Travis Fagerness v2.0 update by Mike Collins"
website = "http://www.nextgenrf.com"
email = "mike.collins@nextgenrf.com"
#TODO:general===============================================================================
# TODO: create a calibration readout on test start for printing or saving
# 
#     possibly create a heading in csv file that will contain all this information
# TODO: create error margin setting in calibration settings
# TODO: create EMC TEST TAB or add test button to calibration 
# 
# TODO: create calibrated data array
# TODO: add save plot functinality to save current tabs plot
# 
# 
# 
# 
# 
# 
# 
# 
# 
#
# 
# 
#  
#===============================================================================

class AppForm(QMainWindow):#create main application
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
           
		#function and Variable Ddeclaration   
        self.threads=[]#create empty list for threads
        self.legend=[]#create empy list for legend
		
        self.rotationAxis='Z'#set default rotation axis for data collection
		
        
        #=======================================================================
        # setup data collection variables
        #=======================================================================
        self.data=np.array([1,2,3]) #holds raw data
        
        self.zRawData=[]# holds raw z axis data
        self.xRawData=[]# holds raw x axis data
        self.yRawData=[]# holds raw y axis data
        
        self.zCalData=[]# holds calibrated z axis data
        self.xCalData=[]# holds calibrated x axis data
        self.yCalData=[]# holds calibrated y axis data
        
        self.angles=[]# holds angle data
        
        self.color='b'# setup plot color for easy diferentiation
        
        self.data_available=False
        self.deviceIsConnected=False
        
		
        #=======================================================================
        # Setup calibration tab defaults
        #=======================================================================
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
        
        #==================================================
		#setup main window
		#==================================================
        self.setWindowTitle('Rotation RX Strength Plotter')
        self.create_menu()#create menu Qwidget
        self.create_tabs()#create tabs for application(data collection, calibration, 3d rendering)
        self.create_dataCollectionTab()#create data collection tabs
        self.create_calibrationTab()#create calibration tab
        self.create_3dTab()#create 3D rendering tab
        self.create_emcTab()
        self.create_status_bar()#create status bar at bottom of app
        self.textbox.setText('1 2 3 4')
        
        #=======================================================================
        # setup EMC testing tab
        #=======================================================================
        self.emc_regs='FCC'#select regulation set for testing
        self.emc_class='A'#select class of emc testing
        
		#==================================================
		#setup worker object
		#==================================================
        self.worker=Worker()
        self.manual_mode=False
		#set threading to run worker at same time as this object
        self.threads.append(self.worker)
		#worker setup
        self.worker.status_msg.connect(self.status_text.setText)
        self.worker.data_pair.connect(self.on_data_ready)
        self.worker.dev_found.connect(self.device_found)
        self.worker.worker_sleep.connect(self.worker_asleep)
        self.worker.start()
        #self.specan=specanalyzer(self.status_text.setText) #analyzer
        #self.dmx=arcus(self.status_text.setText)
		
        self.setup = Setup(self,self.worker)#create setup object for worker object
        self.worker.set_setup(self.setup) #pass the setup params to the worker
        mpl = multiprocessing.log_to_stderr(logging.CRITICAL)#
    
    def worker_asleep(self):#worker wating for command
        #if the worker is asleep (not paused) the rotation table should be at home
        if self.deviceIsConnected:
            self.b_start.setEnabled(not self.manual_mode)
            self.b_manual.setEnabled(True)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_applyCal.setEnabled(True)
            self.rb_axisSelZ.setEnabled(True)
            self.rb_axisSelX.setEnabled(True)
            self.rb_axisSelY.setEnabled(True)
        else:
            self.b_applyCal.setEnabled(False)
            self.b_start.setEnabled(False)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_manual.setEnabled(False)
            self.rb_axisSelZ.setEnabled(False)
            self.rb_axisSelX.setEnabled(False)
            self.rb_axisSelY.setEnabled(False)
        
    def device_found(self,devices=[False,'Not Found','Not Found']):
        self.deviceIsConnected=devices[0]
    
    def save_csv(self):#create csv file
        file_choices = "CSV (*.csv)"

        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save', '', 
                        file_choices))
        
       #========================================================================
       # make data arrays the same size for export to csv
       #========================================================================
        self.fill_data_array()
       

            #===================================================================
            # save to csv
            #===================================================================
        if path:
            with open(path,'wb') as csvfile:
                csvfile.seek(0)
                writer = csv.writer(csvfile)
                w_legend=["Angle (deg)","Raw Z-axis Data","Calibrated Z-axis Data","Raw X-axis Data","Calibrated X-axis Data","Raw Y-axis Data","Calibrated Y-axis Data"]
                w_legend.extend(self.legend)
                writer.writerow(w_legend)
                i=0
                print self.data
                w_data=np.column_stack((self.angles,self.zRawData,self.zCalData,self.xRawData,self.xCalData,self.yRawData,self.yCalData))
                for row in w_data:
                    writer.writerow(np.atleast_1d(row).tolist())
                    print row
                    i=i+1
                    """
                    if rownum == 0:
                        self.legend=row
                    else:
                        data_convert=[]
                        for col in row:
                            data_convert.append(float(col))
                        self.data.append(data_convert)
                    rownum += 1
                    """
            self.statusBar().showMessage('Saved file %s' % path, 2000)
        
    def open_csv(self):#TODO: fix for all axes
        file_choices = "CSV (*.csv)"

        path = unicode(QFileDialog.getOpenFileName(self, 
                        'Open', '', 
                        file_choices))
        if path:
            with open(path,'rb') as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                reader = csv.reader(csvfile, dialect)
                rownum=0
                self.data=[]
                for row in reader:
                    # Save header row.
                    if rownum == 0:
                        self.legend=row
                    else:
                        data_convert=[]
                        for col in row:
                            data_convert.append(float(col))
                        self.data.append(data_convert)
                    rownum += 1
            
            self.data=np.array(self.data)
            self.angles=self.data[:,0] #pull off angles
            self.data=self.data[:,1:]
            self.legend=self.legend[1:] 
            self.statusBar().showMessage('Opened file %s' % path, 2000)
            self.data_available=True
            self.on_draw()
    
    def save_plot(self):#TODO: add 3d rendering
        file_choices = "PNG *.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    
    def on_about(self):#display program information
        msg = "NGRF Rotator\r\n"\
                + "Version: " + version + "\r\n"\
                + "Author: " + author + "\r\n"\
                + "Contact: " + email + "\r\n"\
                + "Copyright " + year + "\r\n"\
                + website
        QMessageBox.about(self, "About", msg.strip())
    
    def on_pick(self, event):#sets turntable target and begins test
        """
        Uses the button_press_event
        """
        if self.manual_mode:
            print event.xdata
            print event.ydata
            #msg = "You've clicked on a bar with coords:\n %s" % box_points
            worker_data=[event.xdata*180/3.14]
            self.worker.do_work(self.worker.Functions.goto_location,worker_data)

    def on_setup(self):#activates setup dialog
        #self.msg=MessageWindow(self,"Searching for compatible spectrum analzyers...",self.specan)
        #self.msg.setModal(True)
        #self.msg.show()
        #self.worker.do_work("find_device")
        
        self.setup.exec_()
        #self.msg.reject()
        #del self.msg
        #self.b_start.setEnabled(True)
		
	#add data to chart when data become available from worker
   
    def on_data_ready(self,new_data):#sends raw data to data lists and starts drawing plots
        #=======================================================================
        # append new data to appropriate array, V2.0
        #=======================================================================
        if (self.rotationAxis=='Z'):
            self.zRawData.append(new_data[1])
        elif(self.rotationAxis=='X'):
            self.xRawData.append(new_data[1])
        elif(self.rotationAxis=='Y'):
            self.yRawData.append(new_data[1])
            
        #===================================================================
        # create arrays for drawing plot
        #===================================================================
        self.angles.append(new_data[0])
        self.data.append(self.calibrate_data(new_data[1]))#calibrate data and append it to drawing array
        #TODO: create calibrated data array for .csv
        self.progress.setValue(new_data[0])
        
        if (self.rotationAxis=='Z'):
            self.zCalData.append(self.calibrate_data(new_data[1]))
        elif(self.rotationAxis=='X'):
            self.xCalData.append(self.calibrate_data(new_data[1]))
        elif(self.rotationAxis=='Y'):
            self.yCalData.append(self.calibrate_data(new_data[1]))
        
        self.on_draw()#draw new data to graph
            
    def on_start(self):#begins test
        self.b_pause.setEnabled(True)
        self.b_stop.setEnabled(True)
        self.b_start.setEnabled(False)
        self.rb_axisSelZ.setEnabled(False)
        self.rb_axisSelX.setEnabled(False)
        self.rb_axisSelY.setEnabled(False)
        self.b_applyCal.setEnabled(False)
        text, ok = QInputDialog.getText(self, 'Name of data', 
            'Enter a data name:')
        if ok:
            self.legend=[str(text)]
            
        self.data=[]
        self.angles=[]
        self.worker.do_work(self.worker.Functions.rotate)
        
        if (self.rotationAxis=='Z'):
            self.zRawData=[]
            self.zCalData=[]
        elif(self.rotationAxis=='X'):
            self.xRawData=[]
            self.xCalData=[]
        elif(self.rotationAxis=='Y'):
            self.yRawData=[]
            self.yCalData=[]
        
    def on_stop(self):#abort current test
        self.b_pause.setEnabled(False)
        self.b_stop.setEnabled(False)
        self.b_start.setEnabled(True)
        self.b_applyCal.setEnabled(True)
        self.b_manual.setEnabled(True)
        self.rb_axisSelZ.setEnabled(True)
        self.rb_axisSelX.setEnabled(True)
        self.rb_axisSelY.setEnabled(True)
        self.worker.cancel_work=True
        
    def on_pause(self):#pause midtest without reseting data
        self.b_stop.setEnabled(not self.b_pause.isChecked())            
        self.worker.pause_work(self.b_pause.isChecked())
    
    def on_manual(self):#activates manual mode
        self.manual_mode=self.b_manual.isChecked()
        if self.manual_mode:
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_start.setEnabled(False)
            self.rb_axisSelZ.setEnabled(False)
            self.rb_axisSelX.setEnabled(False)
            self.rb_axisSelY.setEnabled(False)
        else:
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_start.setEnabled(True)
            self.rb_axisSelZ.setEnabled(True)
            self.rb_axisSelX.setEnabled(True)
            self.rb_axisSelY.setEnabled(True)
            self.b_manual.setEnabled(True)
    
    def on_reset(self):#clears data from active axis list and plot
        self.data=[]#reset raw data list
        self.angles=[]#reset angles list
        
        #clear data arrays
        if (self.rotationAxis=='Z'):
            self.zRawData=[]
        elif(self.rotationAxis=='X'):
            self.xRawData=[]
        elif(self.rotationAxis=='Y'):
            self.yRawData=[]
            
        self.legend=[]
        self.axes.clear()
        self.axes.grid(self.grid_cb.isChecked())
        self.axes.set_title(self.rotationAxis+'-axis',color=self.color)
        self.canvas.draw() 
            
    def update_plot_settings(self):
        self.axes.grid(self.grid_cb.isChecked())
        self.canvas.draw()
    
    def on_axis_select(self):#select rotation axis for test
        #========================================
        #Change Rotation axis for data collection
        #========================================
        
        self.pltColor='000000'
        
        if (self.rb_axisSelX.isChecked()):
            self.rotationAxis='X'
            self.axes=self.x_axis
            self.pltColor='AA00AA'
            self.color='m'
            
        elif(self.rb_axisSelY.isChecked()):
            self.rotationAxis='Y'
            self.axes=self.y_axis
            self.pltColor='00AA00'
            self.color='g'
        else:
            self.rotationAxis='Z'
            self.axes=self.z_axis
            self.pltColor='0000FF'
            self.color='b'
            
        #change curAxis label and format text
        self.curAxis.setText('<span style=" font-size:14pt; font-weight:600; color:#'+self.pltColor+';">Current Rotation Axis: ' + str(self.rotationAxis)+'</span>')
        
        print "Current Rotation Axis: " + self.rotationAxis
        
    def on_draw(self):#draw plots
        """ Redraws the figure
        """

        # clear the axes and redraw the plot anew
        #
        self.axes.clear()        
        self.axes.grid(self.grid_cb.isChecked())
        self.axes.set_title(self.rotationAxis+'-axis',color=self.color)
        
        r = np.array(self.data)#[:,1]
        theta = np.array(self.angles) * np.pi / 180
        self.axes.plot(theta, r, lw=2,color=self.color)
        
        
        #TODO: decifer this
        gridmin=10*round(np.amin(r)/10)
        if gridmin>np.amin(r):
            gridmin = gridmin-10
        gridmax=10*round(np.amax(r)/10)
        if gridmax < np.amax(r):
                gridmax=gridmax+10
        self.axes.set_ylim(gridmin,gridmax)
        self.axes.set_yticks(np.arange(gridmin,gridmax,(gridmax-gridmin)/5))
        
        

        
        leg = self.axes.legend(self.legend)#,loc='center left', bbox_to_anchor=(1.1, 0.5))
        leg.draggable(True)
        self.canvas.draw()
     
    def calibrate_data(self,data):#calibrate collected data
        #TODO data calibration routine
        temp=(data-self.cal_inputPwr)#subtract input power in dBm
        
        temp=temp-self.cal_ampGain#subtract preamp gain
        
        temp=temp-self.cal_txGain#Subtract tx antenna gain
        
        temp=temp-self.cal_fspl#subtract free space  loss
                
        temp=temp-self.cal_cableLoss#subtract cable loss
        
        temp=temp-self.cal_additionalGain#subtract any additional gain/loss

        return temp
     
    def create_tabs(self):#create tab architecture for application

        #create tab widget to hold tabs
        #self.t_bar=QTabBar(shape=QTabBar.TriangularEast)
        self.tabs=QTabWidget()
        
        #create data collection tab
        
        self.t_data= QWidget()
        self.tabs.addTab(self.t_data,"Data Collection")
        
        #create calibration tab
        self.t_calib=QWidget()
        self.tabs.addTab(self.t_calib,"Calibration")
        
        self.t_emc=QWidget()
        self.tabs.addTab(self.t_emc,"EMC")
        
        #create 3d imaging tab
        self.t_3d=QWidget()
        self.tabs.addTab(self.t_3d,"3D Rendering")
        
        self.setCentralWidget(self.tabs)
        
    def create_dataCollectionTab(self):#create data collection tab as well as main window
        self.main_frame = QWidget()
        
        #==========================================================================
        #create Label for current axis V2.0
        #===========================================================================
        
        self.curAxis=QLabel()
        self.curAxis.setText('<span style=" font-size:14pt; font-weight:600; color:#0000FF">Current Rotation Axis: ' + str(self.rotationAxis)+'</span>')
        self.curAxis.setAlignment(Qt.AlignLeft)
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        
        self.dpi = 100
        #self.fig = Figure(figsize=(6.0, 6.0), dpi=self.dpi)
        
        self.fig = Figure(dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        

        self.canvas.setParent(self.t_data)
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wourotldn't
        # work.
        #
        
        self.z_axis = self.fig.add_subplot(131,polar=True)
        self.z_axis.set_title('Z-axis',color='b')
        self.x_axis = self.fig.add_subplot(132,polar=True)
        self.x_axis.set_title('X-axis',color='m')
        self.y_axis = self.fig.add_subplot(133,polar=True)
        self.y_axis.set_title('Y-axis',color='g')
        
        #adjust spacing and placement of plots
        self.fig.subplots_adjust(wspace=.25,bottom=0,top=1)
        
        self.axes=self.z_axis#set current axis to axes variable
        #self.axes = self.fig.add_subplot(311,polar=True)
        
        
        #shrink # modified for V2.0
        #=======================================================================
        # box = self.axes.get_position()
        # self.axes.set_position([box.x0, box.y0, box.width * 1.0, box.height])
        #=======================================================================
        
        # Bind the 'button_press_event' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('button_press_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas
        #
        #=======================================================================
        # self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        #=======================================================================
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.t_data)
        
        # Other GUI controls
        # 
        
        self.b_setup = QPushButton("&Setup")
        self.connect(self.b_setup, SIGNAL('clicked()'), self.on_setup)
        self.b_setup.setToolTip("Setup tools for test")
        
        
        self.b_manual= QPushButton("&Manual Mode",enabled=False,checkable=True)
        self.b_manual.setEnabled(False)
        self.connect(self.b_manual, SIGNAL('clicked()'), self.on_manual)
        self.b_manual.setToolTip("Move table to specific point while continuously performing test")
        
        self.b_start= QPushButton("&Rotate Start")
        self.b_start.setEnabled(False)
        self.connect(self.b_start, SIGNAL('clicked()'), self.on_start)
        self.b_start.setToolTip("Begin Test")
        
        
        self.b_stop= QPushButton("Stop/&Home",enabled=False)
        self.connect(self.b_stop, SIGNAL('clicked()'), self.on_stop)
        self.b_stop.setToolTip("Abort test and return to home position")
        
        self.b_pause= QPushButton("&Pause",enabled=False,checkable=True)
        self.connect(self.b_pause, SIGNAL('clicked()'), self.on_pause)
        self.b_pause.setToolTip("Pause current test")
        
        self.b_reset= QPushButton("&Clear",enabled=True)
        self.connect(self.b_reset, SIGNAL('clicked()'), self.on_reset)
        self.b_reset.setToolTip("Clear data plot from active rotation axis")
        
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)
        
        self.draw_button = QPushButton("&Draw")
        self.connect(self.draw_button, SIGNAL('clicked()'), self.on_draw)
        
        
        self.grid_cb = QCheckBox("Show &Grid",checked=True)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.update_plot_settings)
        self.b_reset.setToolTip("Show grid on active axis?")
        
        #====================================================================================
        #select active rotation axis
        #=================================================================================
    
        axisVbox=QVBoxLayout()
        axisVbox.addWidget(QLabel("Select Axis"))
        axisHbox=QHBoxLayout()
        self.rb_axisSelZ=QRadioButton('Z')#create axis select radio buttons
        self.rb_axisSelZ.click() #set Z axis to default axis select radio button
        self.rb_axisSelX=QRadioButton('X')#create axis select radio buttons
        self.rb_axisSelY=QRadioButton('Y')#create axis select radio buttons
        axisHbox.addWidget(self.rb_axisSelZ)
        axisHbox.addWidget(self.rb_axisSelX)
        axisHbox.addWidget(self.rb_axisSelY)
        axisVbox.addLayout(axisHbox)
        self.connect(self.rb_axisSelZ, SIGNAL('clicked()'), self.on_axis_select)
        self.connect(self.rb_axisSelX, SIGNAL('clicked()'), self.on_axis_select)
        self.connect(self.rb_axisSelY, SIGNAL('clicked()'), self.on_axis_select)
        self.rb_axisSelZ.setToolTip("Cycle active rotation axis")
        self.rb_axisSelX.setToolTip("Cycle active rotation axis")
        self.rb_axisSelY.setToolTip("Cycle active rotation axis")
        
        
        
        
        
        """
        slider_label = QLabel('Bar width (%):')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(20)
        self.slider.setTracking(True)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.on_draw)
        """
        progess_label = QLabel("Rotation Progress:")
        self.progress = QProgressBar()
        self.progress.setAlignment = Qt.Horizontal
        self.progress.setMaximum(360)
        self.progress.setMinimum(0)
        
        
        #===============================================================================
        # Layout with box sizers
        # ==============================================================================
        hbox = QHBoxLayout()
        
        #=======================================================================
        # create button bar
        #=======================================================================
        hbox.addLayout(axisVbox)
        for w in [  self.b_setup,self.b_manual, self.b_start,self.b_stop,self.b_pause,self.b_reset, self.grid_cb,
                    progess_label, self.progress]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
            
        
        vbox = QVBoxLayout()#create layout    
        vbox.addWidget(self.curAxis)#add current rotation axis display label    
        vbox.addWidget(self.canvas,10)#add graph area to display
        vbox.addWidget(self.mpl_toolbar)#add matplotlib toolbar to display
        vbox.addLayout(hbox)#add control buttons to display
        
        #self.main_frame.setLayout(vbox)#send layout to mainframe
        self.t_data.setLayout(vbox)
        #self.setCentralWidget(self.main_frame)
 
    def create_calibrationTab(self):#Create Calibration TAB
        
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
            with open('calibration/antennaList.csv','r') as file:
                reader=csv.reader(file)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Antenna found")
                        self.cb_antennaSel.addItem(row[0])
                        self.cal_antFile[row[0]]='calibration/antennas/'+row[1]
                        
                    skipHeader=False
            file.close()
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
            with open('calibration/preampList.csv','r') as file:
                reader=csv.reader(file)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_ampSel.addItem(row[0])
                        self.cal_ampFile[row[0]]='calibration/preamps/'+row[1]
                        
                    skipHeader=False
            file.close()
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
            with open('calibration/cableList.csv','r') as file:
                reader=csv.reader(file)
                
                skipHeader=True
                for row in reader:
                    
                    if skipHeader==False:#stop app from importing csv header
                        print(row[0]+" Pre-amplifier found")
                        self.cb_cableSel.addItem(row[0])
                        self.cal_cableFile[row[0]]='calibration/cables/'+row[1]
                        
                    skipHeader=False
            file.close()
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
        
        self.t_calib.setLayout(vbox)#set layout of calibration tab

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
        self.cal_cp_center=100000000#sweep center frequency in Hz
        self.cal_cp_span=10000000#sweep span in Hz
     
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
                with open(self.cal_antFile[str(currentAnt)],'r') as file:
                    reader=csv.reader(file)
                    
                    skipHeader=True
                    self.cb_antennaFreqSel.addItem('Auto')
                    
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_antennaFreqGain[row[0]]=row[1];
                            
                            self.cb_antennaFreqSel.addItem(row[0])
                            
                        skipHeader=False
                file.close()
                
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
                with open(self.cal_ampFile[str(currentAmp)],'r') as file:
                    reader=csv.reader(file)
                    self.cb_ampFreqSel.addItem('Auto')#add auto select frequency
                    
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_ampFreqGain[row[0]]=row[1];
                            
                            self.cb_ampFreqSel.addItem(row[0])
                            
                        skipHeader=False
                file.close()
                
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
                with open(self.cal_cableFile[str(currentCable)],'r') as file:
                    reader=csv.reader(file)
                    self.cb_cableFreqSel.addItem('Auto')#add auto select frequency option
                    skipHeader=True
                    for row in reader:
                        if skipHeader==False:#stop app from importing csv header
                            self.cal_cableFreqGain[row[0]]=row[1];
                            
                            self.cb_cableFreqSel.addItem(row[0])
                            
                        skipHeader=False
                file.close()
                
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

    def create_3dTab(self):#create 3d rendering tab
        
        #==========================================================================
        #create Label for current axis V2.0
        #===========================================================================
        
        self.l_3d=QLabel()
        self.l_3d.setText('<span style=" font-size:14pt; font-weight:600; color:#0000CC;">3D rendering of collected data</span>')
        self.l_3d.setAlignment(Qt.AlignLeft)
        
        #=======================================================================
        # create figure and canvas for 3d rendering
        #=======================================================================
        self.fig3d = Figure(figsize=(6.0, 6.0), dpi=self.dpi)
        self.canvas3d = FigureCanvas(self.fig3d)
        
        #=======================================================================
        # self.canvas.setParent(self.main_frame)
        #=======================================================================
        self.canvas3d.setParent(self.t_3d)
        

        
        #=======================================================================
        # create button
        #=======================================================================
        self.b_render= QPushButton("&Render")
        self.b_render.setEnabled(True)
        self.connect(self.b_render, SIGNAL('clicked()'), self.on_draw_3d)
        self.b_render.setToolTip("render collected data in 3D")
        
        self.plt3d = self.fig3d.add_subplot(111,projection='3d')
        
        self.plt3d.set_title('3D representation')    
        
        #self.canvas3d.draw()
        
        hbox3d = QHBoxLayout()
        
        #=======================================================================
        # create button bar
        #=======================================================================
        hbox3d.addStretch()
        for w in [self.b_render]:
            hbox3d.addWidget(w)
            hbox3d.setAlignment(w, Qt.AlignVCenter)
        hbox3d.addStretch()
            
        
        vbox3d = QVBoxLayout()#create layout 
        vbox3d.addWidget(self.l_3d)     
        vbox3d.addWidget(self.canvas3d,10)#add graph area to display
        vbox3d.addWidget(self.mpl_toolbar)#add matplotlib toolbar to display
        vbox3d.addLayout(hbox3d)#add control buttons to display
        
        self.t_3d.setLayout(vbox3d)
    
    def on_draw_3d(self):#TODO: draw 3d representation of data
        self.b_render.setEnabled(False)#disable button while rendering
        
        
        self.b_render.setEnabled(True)#enable button after rendering
    
    def create_emcTab(self):#create EMC testing tab
        
        #=======================================================================
        # create test result plot
        #=======================================================================

        self.fill_data_array()#populate data arrays
            
        self.figEmc = Figure(figsize=(7.0, 3.0), dpi=self.dpi)
        self.emcCanvas = FigureCanvas(self.figEmc)
        
        self.emcCanvas.setParent(self.t_emc)
        self.emcPlot=self.figEmc.add_subplot(111)

        
        
        #run test button
        self.b_run_test= QPushButton("&Run Test")
        self.b_run_test.setEnabled(True)
        self.connect(self.b_run_test, SIGNAL('clicked()'), self.on_run_emc_test)
        self.b_run_test.setToolTip("Run EMC pre-compliance test on collected data")
        
        #select regulations (FCC/CISPER)
        self.regs=QWidget()
        regVbox=QVBoxLayout()
        regVbox.addWidget(QLabel("Select Regulations"))
        rHbox=QHBoxLayout()
        self.r_fcc=QRadioButton('FCC')
        self.r_cisper=QRadioButton('CISPER')
        rHbox.addWidget(self.r_fcc)
        rHbox.addWidget(self.r_cisper)
        self.connect(self.r_fcc, SIGNAL('clicked()'), self.on_select_regs)
        
        self.connect(self.r_cisper, SIGNAL('clicked()'), self.on_select_regs)
        self.r_fcc.setToolTip("Select radiation regulations")
        self.r_cisper.setToolTip("Select radiation regulations")
        regVbox.addLayout(rHbox)
        self.regs.setLayout(regVbox)
        
        #select regulations (FCC/CISPER)
        classbox=QWidget()
        cVbox=QVBoxLayout()
        cVbox.addWidget(QLabel("Select Device Class"))
        cHbox=QHBoxLayout()
        self.r_classA=QRadioButton('Class A')
        
        self.r_classB=QRadioButton('Class B')
        cHbox.addWidget(self.r_classA)
        cHbox.addWidget(self.r_classB)
        self.connect(self.r_classA, SIGNAL('clicked()'), self.on_select_regs)
        self.connect(self.r_classB, SIGNAL('clicked()'), self.on_select_regs)
        self.r_classA.setToolTip("Select radiation regulations")
        self.r_classB.setToolTip("Select radiation regulations")
        cVbox.addLayout(cHbox)
        classbox.setLayout(cVbox)
        
        
        self.r_classA.click()#set button to default
        self.r_fcc.click()
        #=======================================================================
        # Create Layout for EMC Testing
        #=======================================================================
        
        vbox=QVBoxLayout()
        vbox.setAlignment(Qt.AlignTop)
        vbox.addWidget(QLabel('<span style=" font-size:12pt; font-weight:600;">EMC Pre-Compliance Testing</span>'))
        hbox=QHBoxLayout()
        lfbox=QFormLayout()
        lfbox.setAlignment(Qt.AlignLeft)
        hbox.addLayout(lfbox)
        hbox.addStretch()
        hbox.addWidget(self.emcCanvas)
        vbox.addLayout(hbox)
        
        
        
        vbox.addStretch()
        buttBox=QHBoxLayout()#create button bar at bottom of EMC tab
        vbox.addLayout(buttBox)
        
        #=======================================================================
        # create form elements
        #=======================================================================
        
        #Left form
        self.e_emc_target=QLineEdit('100')
        lfbox.addRow(QLabel("Target Frequency (MHz)"),self.e_emc_target)
        
        self.e_emc_uMargin  =QLineEdit('10')
        lfbox.addRow(QLabel("Upper Gain Margin (+dB form target)"),self.e_emc_uMargin)
        
        
        lfbox.addRow(self.regs)
        
        lfbox.addRow(classbox)
        
        #displays test results
        lfbox.addRow(QLabel('<span style=" font-size:12pt; font-weight:600;">Test Results</span>'))
        
        
        self.emc_testResults=QLabel('<span style="  color:yellow; font-size:14pt; font-weight:600;">No Test Data</span>')
        self.emc_testResults.setAlignment(Qt.AlignCenter)
        self.emc_testResults.setAutoFillBackground(True)
        p = self.emc_testResults.palette()
        p.setColor(self.emc_testResults.backgroundRole(), Qt.darkGray)
        self.emc_testResults.setPalette(p)
        
        lfbox.addRow(self.emc_testResults)
        #=======================================================================
        # populate button box at bottom of tab
        #=======================================================================
        buttBox.addStretch()
        for b in [self.b_run_test]:
            buttBox.addWidget(b)
        buttBox.addStretch()
        
        self.t_emc.setLayout(vbox)
    
    def get_reg_value(self,type,target):#return the max field strength in uV/m type='fcc' or 'cisper' target = target frequency in Hz
        target=target*1000000
        retval=0
        
        if (type=='FCC'):#return FCC values
            if self.emc_class=='A':
                if target<=490000:#490kHz
                    retval = 2400/(target/1000)
                elif target<=1705000:#1.705 MHz
                    retval = 24000/(target/1000)
                elif target<30000000:
                    retval = 30
                elif target<=88000000:#88MHz
                    retval = 90
                elif target<=216000000:#216MHz
                    retval = 150
                elif target<=906000000:#906MHz
                    retval = 210
                else:
                    retval = 300
            else:
                if target<=490000:#490kHz
                    retval = 2400/(target/1000)
                elif target<=1705000:#1.705 MHz
                    retval = 24000/(target/1000)
                elif target<30000000:
                    retval = 30
                elif target<=88000000:#88MHz
                    retval = 100
                elif target<=216000000:#216MHz
                    retval = 150
                elif target<=906000000:#906MHz
                    retval = 200
                else:
                    retval = 500
        else:#return cisper values
            retval = 100
        retval=20*math.log10(float(retval)/1000)+120
        
        print 'retval '+ str(retval)
        
        return retval
    
    def on_run_emc_test(self):#run EMC Test TODO: add classes to test and finish 
        print 'Running EMC TEST\n  -VALUES-\nTarget: ' +str(float(self.e_emc_target.text()))+'\nUpper Margin: '+str(float(self.e_emc_uMargin.text()))
        print "running test"
        
        self.fill_data_array()#fill data array for plotting
        
        self.b_run_test.setEnabled(False)#disable run test button while testing
        
        #===================================================================
        # TODO: plot test data vs regulations
        #===================================================================
        # clear the axes and redraw the plot anew
        self.emcPlot.clear()
        fail=False
        testVal=(self.get_reg_value(self.emc_regs, float(self.e_emc_target.text())))
        
        a=np.array(self.angles)*np.pi/180
        z=np.array(self.zCalData)
        x=np.array(self.xCalData)
        y=np.array(self.yCalData)
        zeros=np.zeros_like(a)
        
        self.emcPlot.plot(a,zeros+testVal,lw=1,color='r',ls='--',label=self.emc_regs+" Max")
        self.emcPlot.plot(a,z,lw=1,color='b',label="Z-axis")       
        self.emcPlot.plot(a,x,lw=1,color='m',label="X-axis")
        self.emcPlot.plot(a,y,lw=1,color='g',label="Y-axis")
        
        self.emcPlot.set_xlabel("Angle (radians)")
        self.emcPlot.set_ylabel("dBuV/m")
        self.figEmc.subplots_adjust(wspace=.1,bottom=.2)
        
        self.emcPlot.set_xlim(0,2*np.pi)
        self.emcPlot.legend(fontsize=8,loc="best")
        
        self.emcCanvas.draw()#draw plot
        #===================================================================
        # Run test
        #===================================================================
        for i in self.zCalData:
            if i+float(self.e_emc_uMargin.text()) > testVal:
                print 'EMC Test complete--FAIL'
                self.b_run_test.setEnabled(True)#enable run test button after test
                self.emc_testResults.setText('<span style="  color:red; font-size:14pt; font-weight:600;">Test Failed</span>')
                return 'Fail' 
        for i in self.xCalData:
            if i+float(self.e_emc_uMargin.text()) > testVal:
                print 'EMC Test complete--FAIL'
                self.b_run_test.setEnabled(True)#enable run test button after test
                self.emc_testResults.setText('<span style="  color:red; font-size:14pt; font-weight:600;">Test Failed</span>')
                return 'Fail'
        for i in self.yCalData:
            if i+float(self.e_emc_uMargin.text()) > testVal:
                print 'EMC Test complete--FAIL'
                self.b_run_test.setEnabled(True)#enable run test button after test
                self.emc_testResults.setText('<span style="  color:red; font-size:14pt; font-weight:600;">Test Failed</span>')
                return 'Fail' 
            
            
        print 'EMC Test complete--PASS'
        self.emc_testResults.setText('<span style="  color:lime; font-size:14pt; font-weight:600;">Test Passed</span>')
        self.b_run_test.setEnabled(True)#enable run test button after test
        return 'Pass'
        
        
        
        self.b_run_test.setEnabled(True)#enable run test button after test
  
    def on_select_regs(self):#TODO: select regulations (FCC/CISPER)
        if self.r_fcc.isChecked():
            self.emc_regs='FCC'
        elif self.r_cisper.isChecked():
            self.emc_regs='CISPER'
        
        if self.r_classA.isChecked():
            self.emc_class='A'
        else:
            self.emc_class='B'
   
    def create_status_bar(self):#create status bar at bottom of aplication
        self.status_text = QLabel("Click Setup to find instruments.")
        self.statusBar().addWidget(self.status_text, 1)
        
    def create_menu(self):#create menu at top of application     
        self.file_menu = self.menuBar().addMenu("&File")
        
        open_file_action = self.create_action("&Open CSV",
            shortcut="Ctrl+O", slot=self.open_csv, 
            tip="Load a CSV file, first row is Title, first column is deg, subsequent columns mag")
        
        save_csv_action = self.create_action("&Save CSV",
            shortcut="Ctrl+S", slot=self.save_csv, 
            tip="Save a CSV file, first row is Title, first column is deg, subsequent columns mag")
        
        save_file_action = self.create_action("Save plot",
            slot=self.save_plot, 
            tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, 
            (open_file_action,save_csv_action,save_file_action, None, quit_action))
        
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About')
        
        self.add_actions(self.help_menu, (about_action,))

    def fill_data_array(self):#fill data arrays so they are all the same size
    #========================================================================
       # make data arrays the same size for export to csv
       #========================================================================
       

        short=101-(len(self.zRawData))
        if short>0:
            for i in range(0,short):
                self.zRawData.append(0)
                 
        short=101-(len(self.xRawData))
        if short>0:
            for i in range(0,short):
                self.xRawData.append(0)
                 
        short=101-(len(self.yRawData))
        if short>0:
            for i in range(0,short):
                self.yRawData.append(0)
                 
        short=101-(len(self.zCalData))
        if short>0:
            for i in range(0,short):
                self.zCalData.append(0)
                 
        short=101-(len(self.xCalData))
        if short>0:
             for i in range(0,short):
                 self.xCalData.append(0)
                 
        short=101-(len(self.yCalData))
        if short>0:
            for i in range(0,short):
                self.yCalData.append(0)
         
        short=101-(len(self.angles))
        if short>0:
            for i in range(0,short):
                self.angles.append((i*3.6))
        
    def add_actions(self, target, actions):#do something..apparently
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


def main():
    app = QApplication(sys.argv)#create Qapplication (pyqt)
    app.setStyle(QStyleFactory.create("plastique"))#change style for readability
    form = AppForm()#create Qmainwindow subclass(pyqt)
    form.resize(800,600)
    form.move(10,10)#move app to upper left corner of display
    form.show()#Make application visible (PYQT)
    app.exec_()#enter main loop of QApplication class (pyqt)


if __name__ == "__main__":
    main()
