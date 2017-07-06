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
from openpyxl import *

from Calibrator import Calibrator

import numpy as np
import math
import time
import datetime


from pip._vendor.requests.packages.chardet.latin1prober import FREQ_CAT_NUM

from SignalHound.bb_api_h import BB_TIME_GATE

#===============================================================================
# adjust matplotlib display settings
#===============================================================================
matplotlib.rcParams.update({'font.size': 8})

version = "2.0"
year = "2017"
author = "Travis Fagerness v2.0 update by Mike Collins"
website = "http://www.nextgenrf.com"
email = "mike.collins@nextgenrf.com"
#General TODOs===============================================================================
# TODO: create a calibration readout on test start for printing or saving
# TODO: possibly create a heading in csv file that will contain all calibration information
# TODO: create error margin setting in calibration settings
# TODO: create EMC TEST TAB or add test button to calibration 
# TODO: add save plot functionality to save current tabs plot
# TODO: connect specan setup to program
# TODO: remove unnecasary elements from setup dialog and change to "Find Devices" Dialog
# TODO: add way to select old specan
# TODO: update signalhound specan file to get rid of unneccasary elements
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
        self.legend=""#create empy list for legend
        self.rotationAxis='Z'#set default rotation axis for data collection
        
        self.csvLegend=['Angles','Z (Raw)','Z (Cal)','X (Raw)','X (Cal)','Y (Raw)','Y (Cal)']
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
        
        self.cal=Calibrator()

        #==================================================
        #setup main window
        #==================================================
        self.setWindowTitle('Rotation RX Strength Plotter')
        self.create_menu()#create menu Qwidget
        self.create_tabs()#create tabs for application(data collection, calibration, 3d rendering)
        self.create_dataCollectionTab()#create data collection tabs
        self.cal.create_GUICal(self.t_GUICal)
        #self.cal.create_calibrationTab(self.t_calib)#create calibration tab
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
        #create worker object
        #==================================================
        self.worker=Worker()
        self.worker.cal=self.cal #give worker access to calibrator
        self.manual_mode=False
        #set threading to run worker at same time as this object
        self.threads.append(self.worker)
        #worker setup
        self.worker.status_msg.connect(self.status_text.setText)
        self.worker.data_pair.connect(self.on_data_ready)
        self.worker.dev_found.connect(self.device_found)
        self.worker.worker_sleep.connect(self.worker_asleep)
        self.worker.set_cal(self.cal) #pass the calibrator to the worker
        self.worker.start()
        
        #self.specan=specanalyzer(self.status_text.setText) #analyzer
        #self.dmx=arcus(self.status_text.setText)
        
        #=======================================================================
        # create setup dialog box object
        #=======================================================================
        self.setup = Setup(self,self.worker,self.cal)#create setup object for worker object
        
        self.worker.set_setup(self.setup) #pass the setup params to the worker
        
        #=======================================================================
        # setup worker and setup access for calibrator
        #=======================================================================
        self.cal.set_setup(self.setup)
        self.cal.set_worker(self.worker)

        #TODO: fix mpl = multiprocessing.log_to_stderr(logging.CRITICAL)#
    
    def worker_asleep(self):#worker wating for command
        'enable/disable GUI buttons for when worker is asleep'
        #if the worker is asleep (not paused) the rotation table should be at home
        if self.deviceIsConnected:
            self.b_start.setEnabled(not self.manual_mode)
            self.b_manual.setEnabled(True)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.cal.b_specan.setEnabled(True)
            self.rb_axisSelZ.setEnabled(True)
            self.rb_axisSelX.setEnabled(True)
            self.rb_axisSelY.setEnabled(True)
            
            #display specan type in calibration tab
            self.cal.gui_specan.setText(self.worker.specan.sh_type)
            
        else:
            self.cal.b_specan.setEnabled(False)
            self.b_start.setEnabled(False)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_manual.setEnabled(False)
            self.rb_axisSelZ.setEnabled(False)
            self.rb_axisSelX.setEnabled(False)
            self.rb_axisSelY.setEnabled(False)
            
            #display specan type in calibration tab
            self.cal.gui_specan.setText("--Spectrum analyzer not detected--")
        
    def device_found(self,devices=[False,'Not Found','Not Found']):
        'set if specan AND turntable are found'
        self.deviceIsConnected=devices[0]
    
    def save_csv(self):#create csv file
        'save current plot data as .csv'
        #file_choices = "CSV (*.csv *.xlsx)"
        file_choices = "Excel Workbook ( *.xlsx)"
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
#             #===================================================================
#             # .csv
#             #===================================================================
#             with open(path,'wb') as csvfile:
#                 csvfile.seek(0)
#                 writer = csv.writer(csvfile)
#                 w_legend=["Angle (deg)"]
#                 w_legend.extend(self.csvLegend)#FIXME: add proper titles to data arrays
#                 
#                 writer.writerow(w_legend)#write row to csv
#                 i=0
#                 print self.data#print data to be written to csv
#                 w_data=np.column_stack((self.angles,self.zRawData,self.zCalData,self.xRawData,self.xCalData,self.yRawData,self.yCalData))
#                 for row in w_data:
#                     writer.writerow(np.atleast_1d(row).tolist())
#                     print row
#                     i=i+1
# 
#             self.statusBar().showMessage('Saved file %s' % path, 2000)
            
            #===================================================================
            # .xlsx
            #===================================================================
            wb = Workbook()

            # grab the active worksheet
            ws = wb.active
            
            #===================================================================
            # Write data and angles to xlsx file
            #===================================================================
            
            ws.column_dimensions['A'].width = 20
            ws['A10']= self.csvLegend[0]+" (degrees)"
            ws['A10'].style='Headline 4'
            i=11
            for angle in self.angles:
                ws['A'+str(i)] = angle
                i=i+1
            
            ws.column_dimensions['B'].width = 15
            ws['B10']= self.csvLegend[1]
            ws['B10'].style='Headline 4'
            i=11
            for zraw in self.zRawData:
                ws['B'+str(i)] = zraw
                i=i+1  
                
            ws['C10']= self.csvLegend[2]
            ws['C10'].style='Headline 4'
            i=11
            for zcal in self.zRawData:
                ws['C'+str(i)] = zcal
                i=i+1 
            
            ws['D10']= self.csvLegend[3]
            ws['D10'].style='Headline 4'
            i=11
            for xraw in self.zRawData:
                ws['D'+str(i)] = xraw
                i=i+1
                
            ws['E10']= self.csvLegend[4]
            ws['E10'].style='Headline 4'
            i=11
            for xcal in self.zRawData:
                ws['E'+str(i)] = xcal
                i=i+1     
            
            ws['F10']= self.csvLegend[5]
            ws['F10'].style='Headline 4'
            i=11
            for yraw in self.zRawData:
                ws['F'+str(i)] = yraw
                i=i+1 
            
            ws['G10']= self.csvLegend[6]
            ws['G10'].style='Headline 4'
            i=11
            for ycal in self.zRawData:
                ws['G'+str(i)] = ycal
                i=i+1 
            #===================================================================
            # Write averages and headers
            #===================================================================
            
            ws.merge_cells('A1:D1')
            #ws.column_dimensions['B'].auto_size = True
            ws['A1']= 'Title'
            ws['A1'].style='Title'
            
            ws['A2']= 'Date'
            ws['A2'].style='Headline 4'
            ws["B2"]= datetime.date.today()
            
            ws['A8']= 'Max (dBi)'
            ws['A8'].style='Headline 4'
            
            ws['A9']= 'Average (dBi)'
            ws['A9'].style='Headline 4'
            
            ws['B8'] = "=MAX(B11:B111)"
            ws['B9'] = "=AVERAGE(B11:B111)"
            
            ws['C8'] = "=MAX(C11:C111)"
            ws['C9'] = "=AVERAGE(C11:C111)"
            
            ws['D8'] = "=MAX(D11:D111)"
            ws['D9'] = "=AVERAGE(D11:D111)"
            
            ws['E8'] = "=MAX(E11:E111)"
            ws['E9'] = "=AVERAGE(E11:E111)"
            
            ws['F8'] = "=MAX(F11:F111)"
            ws['F9'] = "=AVERAGE(F11:F111)"
            
            ws['G8'] = "=MAX(G11:G111)"
            ws['G9'] = "=AVERAGE(G11:G111)"
            
            
            #ws['B'].dimensions.ColumnDimension.auto_size=True
            #save .xlsx file
            wb.save(path)
            
        
    def open_csv(self):#TODO: Add ability to open data in all axes
        'open .csv file of previous test'
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
        'Saves plot as .png'
        file_choices = "PNG *.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    
    def on_about(self):#display program information
        'calls about data'
        msg = "NGRF Rotator\r\n"\
                + "Version: " + version + "\r\n"\
                + "Author: " + author + "\r\n"\
                + "Contact: " + email + "\r\n"\
                + "Copyright " + year + "\r\n"\
                + website
        QMessageBox.about(self, "About", msg.strip())
    
    def on_pick(self, event):#sets turntable target and begins test
        """
        Uses the button_press_event to begin manual mode test
        """
        if self.manual_mode:
            print event.xdata
            print event.ydata
            #msg = "You've clicked on a bar with coords:\n %s" % box_points
            worker_data=[event.xdata*180/3.14]
            self.worker.do_work(self.worker.Functions.goto_location,worker_data)

    def on_setup(self):#activates setup dialog
        'initiates setup dialog'
        #self.msg=MessageWindow(self,"Searching for compatible spectrum analzyers...",self.specan)
        #self.msg.setModal(True)
        #self.msg.show()
        #self.worker.do_work("find_device")
        
        self.setup.exec_()
        #self.msg.reject()
        #del self.msg
        #self.b_start.setEnabled(True)
   
    def on_data_ready(self,new_data):#sends raw data to data lists and starts drawing plots
        'adds new data to dat arrays, calls to redraw plot'
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
        self.data.append(self.cal.calibrate_data(new_data[1]))#calibrate data and append it to drawing array
        self.progress.setValue(new_data[0])
        
        if (self.rotationAxis=='Z'):
            self.zCalData.append(self.cal.calibrate_data(new_data[1]))
        elif(self.rotationAxis=='X'):
            self.xCalData.append(self.cal.calibrate_data(new_data[1]))
        elif(self.rotationAxis=='Y'):
            self.yCalData.append(self.cal.calibrate_data(new_data[1]))
        
        self.on_draw()#draw new data to graph
            
    def on_start(self):#begins test
        'begin test'
        
        #=======================================================================
        # enable/disabkle gui buttons during test
        #=======================================================================
        self.b_pause.setEnabled(True)
        self.b_stop.setEnabled(True)
        self.b_start.setEnabled(False)
        self.rb_axisSelZ.setEnabled(False)
        self.rb_axisSelX.setEnabled(False)
        self.rb_axisSelY.setEnabled(False)
        self.cal.b_specan.setEnabled(False)
        
        #=======================================================================
        # get name of plotfordisplay
        #=======================================================================
        text, ok = QInputDialog.getText(self, 'Name of data', 
            'Enter a data name:')
        if ok:
            self.legend=str(text)
        #=======================================================================
        # clear arrays that will store axis data
        #=======================================================================
        self.data=[]
        self.angles=[]
        self.worker.do_work(self.worker.Functions.rotate)
        #TODO: Output Data Heading needs to read what the user inputs when taking a test
        if (self.rotationAxis=='Z'):
            self.zRawData=[]
            self.zCalData=[]

            #set legend for .csv output
            self.csvLegend.pop(0)
            self.csvLegend.insert(0, str(text)+" (Raw)")
            self.csvLegend.pop(1)
            self.csvLegend.insert(1, str(text)+" (Calibrated)")
                
        elif(self.rotationAxis=='X'):
            self.xRawData=[]
            self.xCalData=[]
            
            #set legend for .csv output
            self.csvLegend.pop(2)
            self.csvLegend.insert(2, str(text)+" (Raw)")
            self.csvLegend.pop(3)
            self.csvLegend.insert(3,str(text)+" (Calibrated)")
            
        elif(self.rotationAxis=='Y'):
            self.yRawData=[]
            self.yCalData=[]
            
            #set legend for .csv output
            self.csvLegend.pop(4)
            self.csvLegend.insert(4, str(text)+" (Raw)")
            self.csvLegend.pop(5)
            self.csvLegend.insert(5,str(text)+" (Calibrated)")
        
    def on_stop(self):#abort current test
        'abort current test'
        
        self.b_pause.setEnabled(False)
        self.b_stop.setEnabled(False)
        self.b_start.setEnabled(True)
        self.cal.b_specan.setEnabled(True)
        self.b_manual.setEnabled(True)
        self.rb_axisSelZ.setEnabled(True)
        self.rb_axisSelX.setEnabled(True)
        self.rb_axisSelY.setEnabled(True)
        self.worker.cancel_work=True
        
    def on_pause(self):#pause midtest without reseting data
        'Pause mid-test'
        self.b_stop.setEnabled(not self.b_pause.isChecked())            
        self.worker.pause_work(self.b_pause.isChecked())
    
    def on_manual(self):#activates manual mode
        'switch to manual mode'
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
        'clears data arrays and resest plot data'
        
        self.data=[]#reset raw data list
        self.angles=[]#reset angles list
        
        #clear data arrays
        if (self.rotationAxis=='Z'):
            self.zRawData=[]
        elif(self.rotationAxis=='X'):
            self.xRawData=[]
        elif(self.rotationAxis=='Y'):
            self.yRawData=[]
            
        self.legend=""
        self.axes.clear()
        self.axes.grid(self.grid_cb.isChecked())
        self.axes.set_title(self.rotationAxis+'-axis',color=self.color)
        self.canvas.draw() 
            
    def update_plot_settings(self):
        'update grid setting for Plot'
        self.axes.grid(self.grid_cb.isChecked())
        self.canvas.draw()
    
    def on_axis_select(self):#select rotation axis for test
        'select rotation axis for test'
        
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
        self.axes.clear()        
        self.axes.grid(self.grid_cb.isChecked())
        #self.axes.set_title(self.legend,color=self.color)
        self.axes.set_title(self.legend,fontsize=14,fontweight=300)
        
        r = np.array(self.data)#[:,1]
        theta = np.array(self.angles) * np.pi / 180
        self.axes.plot(theta, r, lw=2,color=self.color)
        
        
        gridmin=10*round(np.amin(r)/10)
        if gridmin>np.amin(r):
            gridmin = gridmin-10
        gridmax=10*round(np.amax(r)/10)
        if gridmax < np.amax(r):
                gridmax=gridmax+10
        self.axes.set_ylim(gridmin,gridmax)
        self.axes.set_yticks(np.arange(gridmin,gridmax,(gridmax-gridmin)/5))
        
        #create legend for plot
        leg = self.axes.legend([self.legend], loc=(-.1,-.2))
        
        leg.draggable(True)
        self.canvas.draw()

    def create_tabs(self):#create tab architecture for application

        #create tab widget to hold tabs
        #self.t_bar=QTabBar(shape=QTabBar.TriangularEast)
        self.tabs=QTabWidget()
        
        #create data collection tab
        
        self.t_data= QWidget()
        self.tabs.addTab(self.t_data,"Data Collection")
        
        #create calibration tab
        # self.t_calib=QWidget()
        # self.tabs.addTab(self.t_calib,"Calibration")
        
        #create GUI calibration tab
        self.t_GUICal=QWidget()
        self.tabs.addTab(self.t_GUICal,"Calibration")
        
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
        self.z_axis.set_title('Z-axis',color='b',fontsize=14,fontweight=300)
        self.x_axis = self.fig.add_subplot(132,polar=True)
        self.x_axis.set_title('X-axis',color='m',fontsize=14,fontweight=300)
        self.y_axis = self.fig.add_subplot(133,polar=True)
        self.y_axis.set_title('Y-axis',color='g',fontsize=14,fontweight=300)
        
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
        #Create rotation axis selection controls
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
        
        self.t_data.setLayout(vbox)
        
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
        'create EMC pre compliance testing tab'
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
    
    def get_reg_value(self,regType,target):#return the max field strength in uV/m type='fcc' or 'cisper' target = target frequency in Hz
        target=target*1000000
        retval=0
        
        if (regType=='FCC'):#return FCC values
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
        
        # clear the axes and redraw the plot anew
        self.emcPlot.clear()
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
  
    def on_select_regs(self):
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
        
        save_csv_action = self.create_action("&Save xlsx",
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
    form.showMaximized()
    #form.show()#Make application visible (PYQT)
    app.exec_()#enter main loop of QApplication class (pyqt)


if __name__ == "__main__":
    main()
