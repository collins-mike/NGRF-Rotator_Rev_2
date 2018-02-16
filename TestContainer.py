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
        self.info="Information"
        self.axis=None              #holds plot
        self.rotationAxis="Z"
        self.rxPolarity="Vertical"
        self.customer=""
        self.dutLabel=""
        self.dutSN=""
        self.testorName=""
        self.comments=""
        self.sweepTime=25/1e3
        self.distance=3
        self.holdsData=False        #true if test has been run
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
    # RotationAxis string contains X Y or Z depending on axis 
    #===========================================================================
    def setRotationAxis(self,axis):
        self.rotationAxis=axis
        self.setInfo()
    def getRotationAxis(self):
        return self.rotationAxis
    
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
    # test info located under plot
    #===========================================================================
    def setInfo(self,INFO=None):
        if INFO!=None:
            self.info=INFO
        else:    
            self.info=self.rotationAxis+"\n"+str(self.distance)+"\n"+str(float(self.rbw/1e3))+"KHz\n"+str(self.gain)+"\n"+str(self.reference)
          
    def getInfo(self):
        return self.info 
    
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
        self.setInfo()
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
    # Spectrum analyzer RBW
    #===========================================================================
    def setRBW(self,RBW):
        self.rbw=RBW;
        self.setInfo()
    def getRBW(self):
        return self.rbw
    
    #===========================================================================
    # Spectrum analyzer GAIN
    #===========================================================================
    def setGain(self,GAIN):
        self.gain=GAIN;
        self.setInfo()
    def getGain(self):
        return self.gain
    
    #===========================================================================
    # Spectrum analyzer Reference
    #===========================================================================
    def setReference(self,REF):
        self.reference=REF;
        self.setInfo()
    def getReference(self):
        return self.reference;
    
    #===========================================================================
    # Spectrum analyzer attenuation
    #===========================================================================
    def setAttenuation(self,atten):
        self.attenuation=atten;
        self.setInfo()
    def getAttenuation(self):
        return self.attenuation;
    
    
    
##EOF    