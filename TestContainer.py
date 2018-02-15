'''
Created on Dec 13, 2017

@author: Mike Collins
'''
import sys, os, random,csv,time


#===============================================================================
# Definitions
#===============================================================================
    #RX polarity

class TestContainer():
    '''
    Test object hold all of the test data for one of the plots on the data collection tab
    '''


    def __init__(self, parent=None):
        '''
        Constructor
        '''
        self.parent=parent
        self.freqCenter=100e6
        self.freqSpan=200e3
        self.title="Title"
        self.axis=None
        self.rxPolarity="Vertical"
        self.customer=""
        self.dutLabel=""
        self.dutSN=""
        self.testorName=""
        self.comments=""
        self.sweepTime=25/1e3
        self.distance=3
        self.holdsData=False #true if test has been run
        self.rbw=10e3
        self.gain="auto"
        self.reference=0
        self.attenuation="auto"
        
        
        self.dataArrayRaw=[]
        self.dataArrayCal=[]
        self.angleArray=[]
        
    #===========================================================================
    # data control
    #===========================================================================
    def appendToRawData(self,data):
        self.dataArrayRaw.append(data)
        
    def appendToCalData(self,data):
        self.dataArrayCal.append(data)
        
    def appendToAngleArray(self,data):
        self.angleArray.append(data)
        
    def clearAllData(self):
        self.dataArrayRaw[:] = []
        self.dataArrayCal[:] = []
        self.angleArray[:]   = []
        
    def clearRawData(self):
        self.dataArrayRaw[:] = []
        
    def clearCalData(self):
        self.dataArrayCal[:] = []
        
    def clearAngleArray(self):
        self.angleArray[:]   = []
        
    #===========================================================================
    # holds data variables return true if test has been run
    #===========================================================================
    def setHoldsData(self,trueFalse):
        self.holdsData=trueFalse
        
    def getHoldsData(self):
        return self.holdsData
    
    #===========================================================================
    # matplotlib axis(subplot) control
    #===========================================================================
    def setSubplot(self,axis):
        self.axis=axis
    def getSubplot(self):
        return self.axis
    
    #===========================================================================
    # title
    #===========================================================================
    def setTitle(self,titl=None):
        if titl!=None:
            self.title=titl
        else:    
            self.title=str(self.dutLabel)+"\nSN: "+str(self.dutSN)+"\nFrequency: "+str(self.freqCenter/1e6)+"MHz\nRX Polarity: "+str(self.getRxPolarity())
    def getTitle(self):
        return self.title  
    
    #===========================================================================
    # Serial Number
    #===========================================================================
    def setSN(self,SN):
        self.dutSN=SN
        self.setTitle()
    def getSN(self):
        return self.dutSN  
    
    #===========================================================================
    # Label
    #===========================================================================
    def setLabel(self,labl):
        self.dutLabel=labl
        self.setTitle()
    def getLabel(self):
        return self.dutSN 
      
    #===========================================================================
    # frequency
    #===========================================================================
    def setFreqCenter(self,freq):
        self.freqCenter=freq
    def getFreqCenter(self):
        return self.freqCenter
    
    def setFreqSpan(self,span):
        self.freqSpan=span;
    def getFreqSpan(self):
        return self.freqSpan
    
    #===========================================================================
    # sweep time
    #===========================================================================
    def setSweepTime(self,swpTme):
        self.sweepTime=swpTme
    def getSweepTime(self):
        return self.sweepTime
    
    #===========================================================================
    # testing distance
    #===========================================================================
    def setDistance(self,dist):
        self.distance=dist
    def getDistance(self):
        return self.distance
    
    #===========================================================================
    # RX Polarity
    #===========================================================================
    def setRxPolarity(self,polarity):
        self.rxPolarity=str(polarity)
        self.setTitle()
    def getRxPolarity(self):
        return self.rxPolarity
    
    #===========================================================================
    # Specan RBW
    #===========================================================================
    def setRBW(self,RBW):
        self.rbw=RBW;
    def getRBW(self):
        return self.rbw
    
    #===========================================================================
    # Specan GAIN
    #===========================================================================
    def setGain(self,GAIN):
        self.gain=GAIN;
    def getGain(self):
        return self.gain
    
    #===========================================================================
    # Specan Reference
    #===========================================================================
    def setReference(self,REF):
        self.reference=REF;
    def getReference(self):
        return self.reference;
    
    #===========================================================================
    # Specan attenuation
    #===========================================================================
    def setAttenuation(self,atten):
        self.attenuation=atten;
    def getAttenuation(self):
        return self.attenuation;
    
    
    
##EOF    