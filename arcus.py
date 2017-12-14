#!/usr/bin/env python
#
# matplotlib now has a PolarAxes class and a polar function in the
# matplotlib interface.  This is considered alpha and the interface
# may change as we work out how polar axes should best be integrated

from visa import *
#import visa
import time
import pyvisa

#rm=visa.ResourceManager()

#visa.log_to_screen()
#t=re.open_resource("GPIB::12")
#print(t.query("*IDN"))

posCount=20000.

class Arcus():
    def __init__(self,status_bar=None,error_msg=None):
        self._status_bar=status_bar
        self._error_msg=error_msg
        #have to assume the system is at 0
        self.cur_deg=0
        self.name=""
            
    def _status(self,msg):
        if self._status_bar is None:
            print msg
        else:
            self._status_bar(str(msg))
    
    def _error(self,msg):
        if self._error_msg is None:
            print msg
        else:
            self._error_msg(str(msg))
    
    def find_device(self):
        for device in get_instruments_list():
            print get_instruments_list(False)
        #for device in rm.list_resources():
            if device.find('COM') is not -1:
                
                try:
                    inst = instrument(device,timeout=2)
                    #inst = rm.open_resource(device,timeout=2000)
                    vers=inst.ask("@01VER")
                    if vers.find('V') is not -1:
                        self.name=inst.ask("@01ID")
                        self.ver=vers
                        self._status("Found Device at " + device + ": " + self.name + " " + vers)
                        self.device_addr=device
                        self.instr = inst
                        self.send_cmd("CURR=2500")  #run current 2500mA
                        self.send_cmd("CURI=2500")  #hold the device in position with strong currentprint "\ndebug 1\n\n"
                        self.send_cmd("ABS")        #set abs mode
                        self.send_cmd("LSPD=1")     #set low speed to 1
                        self.send_cmd("HSPD=200")   #set high speed to 200
                        self.send_cmd("DEC=10000")  #set deaccel/accel to 10000
                        self.send_cmd("SSPDM=0")    #set SSPD to 0
                        self.send_cmd("HCA=55")     #home correction to 1deg
                        self.send_cmd("SLA=2")      #correct twice before giving up
                        self.send_cmd("SLT=25")     #set an error tolerance of about 0.5deg to prevent oscillations

                        return True
                except pyvisa.visa_exceptions.VisaIOError:

                    return False
        return False
    
    def set_speed(self,speed):
        spd=str(speed)
        try:
            self.send_cmd("HSPD="+spd)   #set high speed to 200
            return True
        except pyvisa.visa_exceptions.VisaIOError:
            return False
    
    def move_nonblocking(self,deg):
        if self.ask_cmd("EO").find('0') is not -1:
            self.send_cmd("EO=1")
        return self.send_cmd("X"+str(int(posCount*deg/360)))
    
    def snl_status(self):
        try:
            stat=self.ask_cmd("SLS")
        except pyvisa.visa_exceptions.VisaIOError:
            return False
        return stat
    
    def get_pos_deg(self):
        try:
            pos=self.ask_cmd("EX")
        except pyvisa.visa_exceptions.VisaIOError:
            return False
        print pos
        print int(pos)*360/20000.
        return int(pos)*360/20000.
    
    def enable(self,isEnabled):
        try:
            if isEnabled:
                self.send_cmd("EO=1")
            else:
                self.send_cmd("EO=0")
        except:
            return False
        return True
                    
    def move(self,deg):
        if self.ask_cmd("EO").find('0') is not -1:
            self.send_cmd("EO=1")
        try:
            self.send_cmd("X"+str(posCount*deg/360))
        except pyvisa.visa_exceptions.VisaIOError:
            return False
    
        self.cur_deg = deg
        stat=self.ask_cmd("SLS")
        while stat.find('0') is -1 or stat.find('10') is not -1:
            stat=self.ask_cmd("SLS")
            self._status("At position " + str(self.get_pos_deg()))
            print stat
            if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
                self.ask_cmd("CLR")
                self._status("Problem moving, current position is " + str(self.get_pos_deg()))
                print 'problem moving'
                return False
        self._status("Idle at position " + str(self.get_pos_deg()))
        return True
    
    def ask_cmd(self,cmd):
        try:
            returnVal=self.instr.ask("@01"+cmd)
            if returnVal.find("?") is not -1:
                print returnVal
                return False
            else:
                return returnVal
        except pyvisa.visa_exceptions.VisaIOError:
            print "IO Error"
            return False
        return False
    
    def send_cmd(self,cmd):
        try:
            returnVal=self.instr.ask("@01"+cmd)
            if returnVal.find("OK") is not -1:
                return True
            else:
                print returnVal 
                self.ask_cmd("CLR")
        except pyvisa.visa_exceptions.VisaIOError:
            return False
        return False
            
    def pos_home(self):
        self._status("Homing...")
        if self.ask_cmd("EO").find('0') is not -1:
            self.send_cmd("EO=1")
        if self.send_cmd("H-") is False:
            print 'home command failed'
            return False
        stat=self.ask_cmd("SLS")
        print stat
        while stat.find('0') is -1 and stat.find('6') is not -1:
            stat=self.ask_cmd("SLS")
            time.sleep(0.1)
            self._status("Homing: At position " + str(self.get_pos_deg()))
            print stat
            if stat.find('8') is not -1 or stat.find('9') is not -1 or stat.find('10') is not -1:
                self.ask_cmd("CLR")
                self._status("Problem moving, current position is " + self.get_pos_deg())
                return False
        self._status("At home position.")
        self.send_cmd("EO=0")
        return True
        