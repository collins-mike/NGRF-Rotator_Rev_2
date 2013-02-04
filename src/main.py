"""
RF Rotator
Copyright 2013 Travis Fagerness
"""
import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import multiprocessing,logging

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from specan import *
from arcus import *

import numpy as np


version = "0.1"
year = "2013"
author = "Travis Fagerness"
website = "http://www.nextgenrf.com"
email = "travis.fagerness@nextgenrf.com"
                            
class Setup(QDialog):
    def __init__(self,parent=None,worker=None):
        super(Setup,self).__init__(parent)
        self.worker=worker
        self.setWindowTitle("Setup")
        self.vert = QVBoxLayout()
        self.form = QFormLayout()
        self.b_analyzer = QPushButton("Find Devices")
        self.b_box = QDialogButtonBox(QDialogButtonBox.Ok  | QDialogButtonBox.Cancel)
        self.b_box.addButton(self.b_analyzer,QDialogButtonBox.ActionRole)
        
        self.e_sweep = QLineEdit()
        self.e_cfreq = QLineEdit()
        self.e_span=QLineEdit()
        self.e_offset = QLineEdit()
        self.c_siggen = QCheckBox(enabled=False)
        self.c_maxhold=QCheckBox(checked=False)
        self.e_specan=QLineEdit(enabled=False)
        self.e_rotator=QLineEdit(enabled=False)
        self.form.addRow("Sweep Time (ms)", self.e_sweep)
        self.form.addRow('Center Freq (MHz)',self.e_cfreq)
        self.form.addRow('Span (MHz)',self.e_span)
        self.form.addRow('Offset (dB)',self.e_offset)
        self.form.addRow('Use Sig Gen',self.c_siggen)
        self.form.addRow('Use Max Hold',self.c_maxhold)
        self.form.addRow('Spectrum Analyzer:',self.e_specan)
        self.form.addRow('Rotating Table:',self.e_rotator)
        
        
        self.vert.addLayout(self.form)
        self.vert.addWidget(self.b_box)
        self.setLayout(self.vert)
        
        self.connect(self.b_box, SIGNAL('rejected()'),self.click_cancel)
        self.connect(self.b_box, SIGNAL('accepted()'),self.click_ok)
        self.connect(self.b_analyzer, SIGNAL('clicked()'),self.click_analyzer)
        
        
        #================
        #Defaults - Order of appearance in get_values
        #================
        self.num_st=0.5
        self.num_cfreq=100e6
        self.num_span=10e6
        self.num_offset=0
        self.maxhold=False
        self.usesig=False
        
        self.e_sweep.setText(str(self.num_st*1000))
        self.e_cfreq.setText(str(self.num_cfreq/1e6))
        self.e_span.setText(str(self.num_span/1e6))
        self.e_offset.setText(str(self.num_offset))
        
        self.dev_connected=False
        self.worker.dev_found.connect(self.device_found)
        
    def click_analyzer(self):
        self.worker.do_work(self.worker.Functions.find_device)
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(False)
        self.b_analyzer.setEnabled(False)
        self.b_analyzer.setText("Please wait...")
    
    def click_ok(self):
        """convert values to float, complain if get an exception
        """
        try:
            self.num_st=float(self.e_sweep.text())
            self.num_cfreq=float(self.e_cfreq.text())
            self.num_span=float(self.e_span.text())
            self.num_offset=float(self.e_offset.text())
        except ValueError:
            msg = "Non-numeric data entered!" 
            QMessageBox.critical(self, "Error", msg)
            return
        self.num_st=self.num_st/1000
        self.num_cfreq = self.num_cfreq*1e6
        self.num_span=self.num_span*1e6
        self.maxhold=self.c_maxhold.isChecked()
        if self.dev_connected:
            self.worker.do_work(self.worker.Functions.setup_sa)
        self.close()
        
    def click_cancel(self):
        self.close()
        
    def get_values(self):
        return [self.num_st,
                    self.num_cfreq,
                    self.num_span,
                    self.num_offset,
                    self.maxhold,
                    self.usesig]
                    
    def device_found(self,devices=[False,'Not Found','Not Found']):
        print 'device update....'
        self.b_box.button(QDialogButtonBox.Ok).setEnabled(True)
        self.b_box.button(QDialogButtonBox.Cancel).setEnabled(True)
        self.b_analyzer.setEnabled(True)
        self.b_analyzer.setText('Find Devices')
        self.dev_connected=devices[0]
        if len(devices)>1:
            self.e_rotator.setText(devices[1])
            self.e_specan.setText(devices[2])
        
        
class Worker(QThread):
    class Functions:
        sleep,find_device,rotate,setup_sa,goto_location = range(5)
            
    status_msg = pyqtSignal(object)
    data_pair = pyqtSignal(object)
    dev_found=pyqtSignal(object)
    worker_sleep=pyqtSignal(object)
    degreeRes=3.6
    def __init__(self,setup=None):
        super(Worker,self).__init__()
        #QThread.__init__(self)
        self.cond = QWaitCondition()
        self.mut = QMutex()
        self.specan = SpecAnalyzer(self._status)
        self.dmx=Arcus(self._status)
        self.ang=self.degreeRes
        self.task=-1
        self.work_data=[]
        self.cancel_work=False
        self.task_awake=-1
        self.setup=setup
        
    def _status(self,msg):
        self.status_msg.emit(msg)
    
    def run(self):
        
        print 'started worker thread'
        while self.isRunning():
            try:
                if self.task is self.Functions.find_device:
                    print 'worker is finding dmx'
                    foundDMX=False
                    foundDMX=self.dmx.find_device()
                    foundSpec=False
                    print 'worker finding specan'
                    foundSpec=self.specan.find_device()
                    print foundSpec
                    if foundDMX and not foundSpec:   
                        self._status("Spectrum Analyzer not found!")
                        self.dev_found.emit([True,self.dmx.name,'Not Found'])#allow the program to run without analyzer
                        self.dmx.pos_home()
                    elif not foundDMX and foundSpec:
                        self._status("Rotating Table not found!")
                        self.dev_found.emit([False,'Not Found',self.specan.device])
                    elif foundDMX and foundSpec:
                        self._status("Ready!")
                        self.dev_found.emit([True,self.dmx.name,self.specan.device])
                        self.dmx.pos_home()
                    else:
                        self._status("No devices found.")
                        self.dev_found.emit([False,'Not Found','Not Found'])
                    self.task = self.Functions.sleep
                elif self.task is self.Functions.rotate:
                    print 'worker is rotating table'
                    print time.time()
                    if self.ang-self.degreeRes < 0.1:
                        self.dmx.enable(True)
                        self._status("Returning to home position, please wait...")
                        #self.dmx.move(3) #work around in case sitting at home
                        while not self.dmx.pos_home():
                            pass
                    print time.time()
                    settings=self.setup.get_values()
                    self.specan.clear_trace()
                    print time.time() 
                    while not self.dmx.move_nonblocking(self.ang):
                        pass
                    time.sleep(settings[0]) #sleeping while the trace loads allows other threads to run
                    stat=self.dmx.ask_cmd("SLS")
                    while stat is False:
                        stat=self.dmx.ask_cmd("SLS")
                    while stat.find('0') is -1 or stat.find('10') is not -1:
                        stat=self.dmx.ask_cmd("SLS")
                        self._status("At position " + str(self.dmx.get_pos_deg()))
                        print stat
                        if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
                            self.dmx.ask_cmd("CLR")
                            self._status("Problem moving, current position is " + str(self.dmx.get_pos_deg()))
                            print 'problem moving'
                    self._status("At position " + str(self.dmx.get_pos_deg()))
                    print "At position " + str(self.dmx.get_pos_deg()) + " expect pos " + str(self.ang)
                    print time.time()
                    mag=self.specan.get_peak_power()
                    print time.time()
                    self.data_pair.emit([self.ang,mag])
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
                elif self.task is self.Functions.setup_sa:
                    settings=self.setup.get_values()
                    print settings
                    print 'worker is setting up sa'
                    try:
                        #self.specan.set_frequency(settings[1],settings[2])
                        self.specan.set_max_hold(settings[4])
                        #self.specan.set_sweeptime(settings[0]*1000)
                    except:
                        print 'unexpected error:',sys.exc_info()
                    self.task = self.Functions.sleep
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
                else:
                    if self.task is self.Functions.sleep:
                        self.worker_sleep.emit(True)
                    self.cancel_work=False
                    print 'worker sleeping'
                    self.mut.lock()
                    self.cond.wait(self.mut)
                    self.mut.unlock()
                    print 'worker awake'
            except Exception,e:
                print 'exception in worker: ' + str(e)
            
    def do_work(self,work,work_data=[]):
        self.task=work
        self.work_data=work_data
        print work
        self.cond.wakeAll()
    
    def pause_work(self,pause_pressed):
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
        self.setup=setup
        

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
            
        self.threads=[]
        self.legend=[]
        self.setWindowTitle('Rotation RX Strength Plotter')
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        self.textbox.setText('1 2 3 4')
        self.data=np.array([1,2,3])
        self.angles=np.array([45,90,270])
        self.data_available=False
        self.deviceIsConnected=False
        self.worker=Worker()
        self.manual_mode=False
        self.threads.append(self.worker)
        self.worker.status_msg.connect(self.status_text.setText)
        self.worker.data_pair.connect(self.on_data_ready)
        self.worker.dev_found.connect(self.device_found)
        self.worker.worker_sleep.connect(self.worker_asleep)
        self.worker.start()
        #self.specan=specanalyzer(self.status_text.setText) #analyzer
        #self.dmx=arcus(self.status_text.setText)
        self.setup = Setup(self,self.worker)
        self.worker.set_setup(self.setup) #pass the setup params to the worker
        mpl = multiprocessing.log_to_stderr(logging.CRITICAL)
    
    def worker_asleep(self):
        #if the worker is asleep (not paused) the rotation table should be at home
        if self.deviceIsConnected:
            self.b_start.setEnabled(not self.manual_mode)
            self.b_manual.setEnabled(True)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
        else:
            self.b_start.setEnabled(False)
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_manual.setEnabled(False)
        
    def device_found(self,devices=[False,'Not Found','Not Found']):
        self.deviceIsConnected=devices[0]
    
    def save_csv(self):
        file_choices = "CSV (*.csv)"

        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save', '', 
                        file_choices))
        if path:
            with open(path,'wb') as csvfile:
                csvfile.seek(0)
                writer = csv.writer(csvfile)
                w_legend=["Angle (deg)"]
                w_legend.extend(self.legend)
                writer.writerow(w_legend)
                i=0
                print self.data
                w_data=np.column_stack((self.angles,self.data))
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
        
    def open_csv(self):
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
    
    
    def save_plot(self):
        file_choices = "PNG *.png"
        
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file', '', 
                        file_choices))
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            self.statusBar().showMessage('Saved to %s' % path, 2000)
    
    def on_about(self):
        msg = "NGRF Rotator\r\n"\
                + "Version: " + version + "\r\n"\
                + "Author: " + author + "\r\n"\
                + "Contact: " + email + "\r\n"\
                + "Copyright " + year + "\r\n"\
                + website
        QMessageBox.about(self, "About", msg.strip())
    
    def on_pick(self, event):
        """
        Uses the button_press_event
        """
        if self.manual_mode:
            print event.xdata
            print event.ydata
            #msg = "You've clicked on a bar with coords:\n %s" % box_points
            worker_data=[event.xdata*180/3.14]
            self.worker.do_work(self.worker.Functions.goto_location,worker_data)

    
    def on_setup(self):
        #self.msg=MessageWindow(self,"Searching for compatible spectrum analzyers...",self.specan)
        #self.msg.setModal(True)
        #self.msg.show()
        #self.worker.do_work("find_device")
        
        self.setup.exec_()
        #self.msg.reject()
        #del self.msg
        #self.b_start.setEnabled(True)
    
    def on_data_ready(self,new_data):
        self.angles.append(new_data[0])
        self.data.append(new_data[1])
        self.progress.setValue(new_data[0])
        self.on_draw()
        
    def on_start(self):
        self.b_pause.setEnabled(True)
        self.b_stop.setEnabled(True)
        self.b_start.setEnabled(False)
        
        text, ok = QInputDialog.getText(self, 'Name of data', 
            'Enter a data name:')
        if ok:
            self.legend=[str(text)]
            
        self.data=[]
        self.angles=[]
        self.worker.do_work(self.worker.Functions.rotate)
        
    def on_stop(self):
        self.b_pause.setEnabled(False)
        self.b_stop.setEnabled(False)
        self.b_start.setEnabled(True)
        self.b_manual.setEnabled(True)
        self.worker.cancel_work=True
        
    def on_pause(self):
        self.b_stop.setEnabled(not self.b_pause.isChecked())            
        self.worker.pause_work(self.b_pause.isChecked())
    
    def on_manual(self):
        self.manual_mode=self.b_manual.isChecked()
        if self.manual_mode:
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_start.setEnabled(False)
        else:
            self.b_pause.setEnabled(False)
            self.b_stop.setEnabled(False)
            self.b_start.setEnabled(True)
            self.b_manual.setEnabled(True)
    
    def on_reset(self):
        self.data=[]
        self.angles=[]
        self.data=[]
        self.legend=[]
        self.axes.clear()
        self.axes.grid(self.grid_cb.isChecked())
        self.canvas.draw() 
            
    def update_plot_settings(self):
        self.axes.grid(self.grid_cb.isChecked())
        self.canvas.draw()
        
        
    def on_draw(self):
        """ Redraws the figure
        """

        # clear the axes and redraw the plot anew
        #
        self.axes.clear()        
        self.axes.grid(self.grid_cb.isChecked())
        r = np.array(self.data)#[:,1]
        theta = np.array(self.angles) * np.pi / 180
        self.axes.plot(theta, r, lw=2)
        
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
    
    def create_main_frame(self):
        self.main_frame = QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((6.0, 6.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        
        self.axes = self.fig.add_subplot(111,polar=True)
        #shrink
        box = self.axes.get_position()
        self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        
        # Bind the 'button_press_event' event for clicking on one of the bars
        #
        self.canvas.mpl_connect('button_press_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls
        # 
        self.b_setup = QPushButton("&Setup")
        self.connect(self.b_setup, SIGNAL('clicked()'), self.on_setup)
        
        self.b_manual= QPushButton("&Manual Mode",enabled=False,checkable=True)
        self.b_manual.setEnabled(False)
        self.connect(self.b_manual, SIGNAL('clicked()'), self.on_manual)
        
        self.b_start= QPushButton("&Rotate Start")
        self.b_start.setEnabled(False)
        self.connect(self.b_start, SIGNAL('clicked()'), self.on_start)
        
        self.b_stop= QPushButton("Stop/&Home",enabled=False)
        self.connect(self.b_stop, SIGNAL('clicked()'), self.on_stop)
        
        self.b_pause= QPushButton("&Pause",enabled=False,checkable=True)
        self.connect(self.b_pause, SIGNAL('clicked()'), self.on_pause)
        
        self.b_reset= QPushButton("&Clear",enabled=True)
        self.connect(self.b_reset, SIGNAL('clicked()'), self.on_reset)
        
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(200)
        self.connect(self.textbox, SIGNAL('editingFinished ()'), self.on_draw)
        
        self.draw_button = QPushButton("&Draw")
        self.connect(self.draw_button, SIGNAL('clicked()'), self.on_draw)
        
        self.grid_cb = QCheckBox("Show &Grid",checked=True)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.update_plot_settings)
        
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
        
        
        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()
        
        for w in [  self.b_setup,self.b_manual, self.b_start,self.b_stop,self.b_pause,self.b_reset, self.grid_cb,
                    progess_label, self.progress]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
            
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas,10)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
    
    def create_status_bar(self):
        self.status_text = QLabel("Click Setup to find instruments.")
        self.statusBar().addWidget(self.status_text, 1)
        
    def create_menu(self):        
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

    def add_actions(self, target, actions):
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
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()