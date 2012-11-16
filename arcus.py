#!/usr/bin/env python
#
# matplotlib now has a PolarAxes class and a polar function in the
# matplotlib interface.  This is considered alpha and the interface
# may change as we work out how polar axes should best be integrated

from visa import *
import pyvisa,time

class Arcus():
	def __init__(self,status_bar=None,error_msg=None):
		self._status_bar=status_bar
		self._error_msg=error_msg
		#have to assume the system is at 0
		self.cur_deg=0
			
	def _status(self,msg):
		if self._status_bar is None:
			pass
		else:
			self._status_bar(str(msg))
	
	def _error(self,msg):
		if self._error_msg is None:
			pass
		else:
			self._error_msg(str(msg))
	
	def find_device(self):
		pass
	
	def cw_deg(self,deg):
		for i in range(0,deg):
			#time.sleep(0.5)
			self.cur_deg = self.cur_deg+1
			return self.cur_deg
			
	def pos_home(self):
		pass
		