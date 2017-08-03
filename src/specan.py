#!/usr/bin/env python
#
# matplotlib now has a PolarAxes class and a polar function in the
# matplotlib interface.  This is considered alpha and the interface
# may change as we work out how polar axes should best be integrated

from visa import *
import pyvisa

from SignalHound import SignalHound



class SpecAnalyzer():
	
	def __init__(self,status_bar=None,error_msg=None):
		
		#=======================================================================
		# create type holder for specan: SH = signalhound, HP= HP
		#=======================================================================
		self.SpectrumAnalyzerType = "SH"
		
		self._status_bar=status_bar
		self._error_msg=error_msg
		self.load_supported()
		self.maxhold=False
		self.instr=None
		self.sh=None
		#self.sh=SignalHound()
		self.sh_type="None"
		
		#pointer to calibrator object
		self.cal=None
		
	def _status(self,msg):
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self._status_bar is None:
				pass
			else:
				self._status_bar(str(msg))
				
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			if self._status_bar is None:
				pass
			else:
				self._status_bar(str(msg))
		
	def _error(self,msg):
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self._error_msg is None:
				pass
			else:
				self._error_msg(str(msg))
				
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			if self._error_msg is None:
				pass
			else:
				self._error_msg(str(msg))
		
	def open_device(self,device):
		
		
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			try:
				inst = instrument(device,timeout=2)
			except pyvisa.visa_exceptions.VisaIOError:
				return
			self.instr=inst
			self.device=device
			
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			try:
				inst = instrument(device,timeout=2)
			except pyvisa.visa_exceptions.VisaIOError:
				return
			self.instr=inst
			self.device="BB60C"
		
	def set_frequency(self,center,span):
		#=======================================================================
		#
		#          Name:	set_frequency
		#
		#    Parameters:	(float)center, (float)span
		#
		#        Return:	None
		#
		#   Description:	this function sets the test frequency and test frequency span in Hz for the Specan
		#
		#=======================================================================
		"""Only for the 8566B analyzer to change freq
		:param center: Center freq in Hz.
		:param span: Span freq in Hz.
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self.instr is None:
				return
			self.instr.write('CF '+str(int(center)) + 'HZ;'+'SP ' + str(int(span)) + 'HZ')
			
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			self.sh.configureCenterSpan(center,span) 
		
	def set_sweeptime(self,sweeptime):
		#=======================================================================
		#
		#          Name:	set_sweeptime
		#
		#    Parameters:	(float)sweeptime
		#
		#        Return:	None
		#
		#   Description:	this function sets the sweeptime on the spectrum analyzer
		#
		#					in the case of SignalHound this functions sets RBW and VBW as well
		#
		#=======================================================================
		
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self.instr is None:
				return
			self.instr.write('ST ' + str(int(sweeptime)) + 'MS')
			
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			if (self.device != "BB60C"):
				return
			self.sh.configureSweepCoupling(self.cal.get_RBW(),self.cal.get_VBW(),sweeptime,"native","spur-reject")
			
		
	def clear_trace(self):
		#=======================================================================
		#
		#          Name:	clear_trace
		#
		#    Parameters:	None
		#
		#        Return:	None
		#
		#   Description:	Clears trace of specan (ONLY FOR HP 8566B Specan)
		#
		#=======================================================================
		"""Clear trace, only for the 8566B analyzer
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self.instr is None:
				return
			self.instr.write('A1')
			if self.maxhold:
				self.instr.write('A2')
				
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			pass
		
	def set_max_hold(self,state):
		#=======================================================================
		#
		#          Name:	set_max_hold
		#
		#    Parameters:	state
		#
		#        Return:	None
		#
		#   Description:	set max hold of specan (ONLY FOR HP 8566B Specan)
		#
		#=======================================================================
		"""Set the max hold state for the 8566B analyzer
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self.instr is None:
				return
			self.maxhold=state
			
		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			pass
		
	def find_device(self):
		#=======================================================================
		#
		#          Name:	find_device
		#
		#    Parameters:	None
		#
		#        Return:	True  or False
		#
		#   Description:	Locates Specan Returns true if device is found false if not
		#
		#=======================================================================
		'find device, return True if found, else False'
		
		"""Find a VISA device that matches a device from the config file.
		:return True - Found a device, False - Did not find a device
		Took 3.357seconds to find an HP8566B
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			try:
				self._status("Searching for instruments...")
				id_cmds = ['*IDN?','ID']
				for device in get_instruments_list():
					if device.find("COM") is not -1:
						continue
					inst = instrument(device,timeout=2)
					try:
						for id_cmd in id_cmds:
							inst.write(id_cmd)
							try:
								cur_dev=inst.read()
							except pyvisa.visa_exceptions.VisaIOError as e:
								continue					
							i=0
							for dev in self.supported_dev:
								if cur_dev.find(dev) is not -1:
									self._status("Found Device: " + dev)
									self.device_addr=device
									self.device=dev
									self.instr = inst
									self.cmds = self.supported_dev_cmd[i]
									return True
								i = i + 1
					except pyvisa.visa_exceptions.VisaIOError as e:
						pass					
	 					
			except pyvisa.visa_exceptions.VisaIOError as e:
				pass
			self._status("No Device Found")
			return False
		
		#=======================================================================
		# SIGNALHOUND BB60C
		#=======================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			if self.sh_type =="None":

				self.sh=SignalHound()
				self.sh_type=self.sh.devType
				print self.sh.devType
				print self.sh
				if self.sh_type == "BB60C":
					print self.sh.getDeviceDiagnostics()
					self.device="BB60C";
					return True
					
				else:
					print 7
					return False
			else:
				print self.sh.getDeviceDiagnostics()
				return True
		
	def get_peak_power(self):
		#=======================================================================
		#
		#          Name:	get_peak_power
		#
		#    Parameters:	None
		#
		#        Return:	(float)
		#
		#   Description:	gets the maximum value from a sweep of the specan.
		#					returns the max value as a float
		#
		#=======================================================================
		"""Return the peak power of the current trace in dBm
		:return Peak Power (dBm)
		Returned value in 0.026s from HP
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			if self.instr is None:
				return 1
			try:
				for cmd in self.cmds:
					self.instr.write(cmd)
						
				#self.instr.wait_for_srq()
				data=self.instr.read_values()
				
				return data[0]
			except pyvisa.visa_exceptions.VisaIOError as e:
				self._error(str(e)) #TODO - see what happens if an unhandled exception occurs
				
		#=======================================================================
		# SIGNALHOUND BB60C
		#=======================================================================
		if(self.SpectrumAnalyzerType=="SH"):	
			if self.sh_type == "None":
				return 1
			try:
				#for cmd in self.cmds:
				#	self.instr.write(cmd)
				
				self.sh.initiate(mode = "sweeping", flag = "ignored")
				self.sh.queryTraceInfo()
				data=[]
				data.append(self.sh.fetchTrace())
				
				tmp=data.pop()
				ret=-99999999#start return value very low so first received gain will always be accepted
				#cut gain array to only the max value over the frequency span
				for gain in tmp["max"]:
					if gain>ret:
						ret=gain
				print "max value: " + str(ret)
				
				return ret
				
			except pyvisa.visa_exceptions.VisaIOError as e:
				self._error(str(e)) #TODO - see what happens if an unhandled exception occurs
				
	def load_supported(self):
		#=======================================================================
		#
		#          Name:	load_supported
		#
		#    Parameters:	None
		#
		#        Return:	None
		#
		#   Description:	Loads supported devices (ONLY FOR HP 8566B Specan)
		#
		#=======================================================================
		"""
		This function loads a file with the name returned by *IDN? or ID 
		followed by the commands to set and read a peak marker.
		"""
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			self.supported_dev=[]
			self.supported_dev_cmd=[]
			self._status("Loading supported files...")
			with open('devices.txt','r+') as f:
					linetype='device'
					cmd=[]
					for line in f:
						if line=='\n' or line == '\n\r' or line == '\r' or line =='\r\n':
							linetype='device'
							self.supported_dev_cmd.append(cmd)
							cmd=[]
						else:
							if linetype is 'device':
								self.supported_dev.append(line.strip())
								linetype = 'cmd'
							elif linetype is  'cmd':
								cmd.append(line.strip())
					self.supported_dev_cmd.append(cmd)

		#===================================================================
		# SIGNALHOUND BB60C
		#===================================================================
		if(self.SpectrumAnalyzerType=="SH"):
			pass
						
	def set_SpectrumAnalyzerType(self,specanType):
		#=======================================================================
		#
		#          Name:	set_SpectrumAnalyzerType
		#
		#    Parameters:	(string)specanType					
		#
		#        Return:	None
		#
		#   Description:	this function set the type of spectrum analyzer that will be used for testing
		#					choices are
		#					"SH" = SignalHound BB60C
		#					"HP" = Old HP spectrum analyzer
		#
		#=======================================================================
							
		self.SpectrumAnalyzerType = specanType
		
		#=======================================================================
		# HP 8566B Specan
		#=======================================================================
		if(self.SpectrumAnalyzerType=="HP"):
			self.load_supported()
			
	def set_cal(self,cal):
		#=======================================================================
		#
		#          Name:	set_cal
		#
		#    Parameters:	(pointer to Calibrator Object)cal
		#
		#        Return:	None	
		#
		#   Description:	this function creates a pointer to the Calibrator object
		#
		#=======================================================================
		'create a pointer to Calibrator object'
		self.cal=cal


#End of File