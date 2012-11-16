"""
This demo demonstrates how to embed a matplotlib (mpl) plot 
into a PyQt4 GUI application, including:

* Using the navigation toolbar
* Adding data to the plot
* Dynamically modifying the plot's properties
* Processing mpl events
* Saving the plot to a file from a menu

The main goal is to serve as a basis for developing rich PyQt GUI
applications featuring mpl plots (using the mpl OO API).

Eli Bendersky (eliben@gmail.com)
License: this code is in the public domain
Last modified: 19.01.2009
"""
import sys, os, random,csv,time
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from specan import *
from arcus import *

import numpy as np
		
class Setup(QDialog):
	def __init__(self,parent=None,worker=None):
		super(Setup,self).__init__(parent)
		self.worker=worker
		self.setWindowTitle("Setup")
		self.vert = QVBoxLayout()
		self.form = QFormLayout()
		self.b_analyzer = QPushButton("Find Analyzer")
		self.b_box = QDialogButtonBox(QDialogButtonBox.Ok  | QDialogButtonBox.Cancel)
		self.b_box.addButton(self.b_analyzer,QDialogButtonBox.ActionRole)
		
		self.e_sweep = QLineEdit()
		self.e_cfreq = QLineEdit()
		self.e_span=QLineEdit()
		self.e_offset = QLineEdit()
		self.c_siggen = QCheckBox(enabled=False)
		self.c_maxhold=QCheckBox(enabled=False)
		self.form.addRow("Sweep Time (ms)", self.e_sweep)
		self.form.addRow('Center Freq (MHz)',self.e_cfreq)
		self.form.addRow('Span (MHz)',self.e_span)
		self.form.addRow('Offset (dB)',self.e_offset)
		self.form.addRow('Use Sig Gen',self.c_siggen)
		self.form.addRow('Use Max Hold',self.c_maxhold)
		
		
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
		self.worker.do_work("find_device")
		self.b_box.setEnabled("False")
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
		if self.dev_connected:
			self.worker.do_work("setup_sa")
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
					
	def device_found(self,isFound):
		print 'device update'
		print isFound
		self.dev_connected=isFound
		
		
class Worker(QThread):
	status_msg = pyqtSignal(object)
	data_pair = pyqtSignal(object)
	dev_found=pyqtSignal(object)
	def __init__(self,setup=None):
		#super(SpecAn,self).__init__()
		QThread.__init__(self)
		self.cond = QWaitCondition()
		self.mut = QMutex()
		self.specan = SpecAnalyzer(self._status)
		self.dmx=Arcus(self._status)
		self.ang=0
		
		#==============
		#Worker functions
		#==============
		self.find_device = False
		self.is_rotating = False
		self.setup_sa = False
		
		
		self.setup=setup
		
	def _status(self,msg):
		print 'sent message'
		self.status_msg.emit(msg)
	
	def run(self):
		print 'started worker thread'
		while self.isRunning():
			if self.find_device:
				print 'worker is finding device'
				self.dev_found.emit(self.specan.find_device())
				self.find_device=False
			elif self.is_rotating:
				settings=self.setup.get_values()
				print 'worker is rotating'
				time.sleep(settings[0]) #sleeping while the trace loads allows other threads to run
				mag=self.specan.get_peak_power()
				ang=self.dmx.cw_deg(1)
				self.ang = self.ang+1
				self.data_pair.emit([ang,mag])
				if self.ang ==360:
					self.is_rotating=False
					self.ang=0 #TODO - would reset the spinner potentially
			elif self.setup_sa:
				settings=self.setup.get_values()
				print settings
				print 'worker is setting up sa'
				try:
					self.specan.set_frequency(settings[1],settings[2])
					self.specan.set_max_hold(settings[4])
				except:
					print 'unexpected error:',sys.exc_info()
				self.setup_sa=False
			else:
				print 'worker sleeping'
				self.mut.lock()
				self.cond.wait(self.mut)
				self.mut.unlock()
				print 'worker awake'
			
	def do_work(self,work):
		if work is "find_device":
			self.find_device=True
		elif work is "rotate":
			self.is_rotating=True
		elif work is 'setup_sa':
			self.setup_sa=True
			
		self.cond.wakeAll()
		
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
		self.worker=Worker()
		self.threads.append(self.worker)
		self.worker.status_msg.connect(self.status_text.setText)
		self.worker.data_pair.connect(self.on_data_ready)
		self.worker.dev_found.connect(self.device_found)
		self.worker.start()
		#self.specan=specanalyzer(self.status_text.setText) #analyzer
		#self.dmx=arcus(self.status_text.setText)
		self.setup = Setup(self,self.worker)
		self.worker.set_setup(self.setup) #pass the setup params to the worker
		
	def device_found(self):
		self.b_start.setEnabled(True)
		
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
	
	
	def save_plot(self):
		file_choices = "PNG *.png"
		
		path = unicode(QFileDialog.getSaveFileName(self, 
						'Save file', '', 
						file_choices))
		if path:
			self.canvas.print_figure(path, dpi=self.dpi)
			self.statusBar().showMessage('Saved to %s' % path, 2000)
	
	def on_about(self):
		msg = """ A demo of using PyQt with matplotlib:
		
		 * Use the matplotlib navigation bar
		 * Add values to the text box and press Enter (or click "Draw")
		 * Show or hide the grid
		 * Drag the slider to modify the width of the bars
		 * Save the plot to a file using the File menu
		 * Click on a bar to receive an informative message
		"""
		QMessageBox.about(self, "About the demo", msg.strip())
	
	def on_pick(self, event):
		# The event received here is of the type
		# matplotlib.backend_bases.PickEvent
		#
		# It carries lots of information, of which we're using
		# only a small amount here.
		# 
		box_points = event.artist.get_bbox().get_points()
		msg = "You've clicked on a bar with coords:\n %s" % box_points
		
		QMessageBox.information(self, "Click!", msg)
	
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
		self.data=[]
		self.angles=[]
		self.worker.do_work("rotate")
	
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
		
		# Bind the 'pick' event for clicking on one of the bars
		#
		#self.canvas.mpl_connect('pick_event', self.on_pick)
		
		# Create the navigation toolbar, tied to the canvas
		#
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
		
		# Other GUI controls
		# 
		self.b_setup = QPushButton("&Setup")
		self.connect(self.b_setup, SIGNAL('clicked()'), self.on_setup)
		
		self.b_start= QPushButton("&Start")
		self.b_start.setEnabled(False)
		self.connect(self.b_start, SIGNAL('clicked()'), self.on_start)
		
		self.b_stop= QPushButton("&Stop",enabled=False)
		
		self.b_pause= QPushButton("&Pause",enabled=False)
		
		self.b_reset= QPushButton("&Reset",enabled=False)
		
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
		
		for w in [  self.b_setup, self.b_start,self.b_stop,self.b_pause,self.b_reset, self.grid_cb,
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
		self.status_text = QLabel("Ready")
		self.statusBar().addWidget(self.status_text, 1)
		
	def create_menu(self):		
		self.file_menu = self.menuBar().addMenu("&File")
		
		open_file_action = self.create_action("&Open CSV",
			shortcut="Ctrl+O", slot=self.open_csv, 
			tip="Load a CSV file, first row is Title, first column is deg, subsequent columns mag")
		
		save_file_action = self.create_action("&Save plot",
			shortcut="Ctrl+S", slot=self.save_plot, 
			tip="Save the plot")
		quit_action = self.create_action("&Quit", slot=self.close, 
			shortcut="Ctrl+Q", tip="Close the application")
		
		self.add_actions(self.file_menu, 
			(open_file_action,save_file_action, None, quit_action))
		
		self.help_menu = self.menuBar().addMenu("&Help")
		about_action = self.create_action("&About", 
			shortcut='F1', slot=self.on_about, 
			tip='About the demo')
		
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