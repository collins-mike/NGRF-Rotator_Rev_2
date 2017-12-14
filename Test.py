'''
Created on Dec 13, 2017

@author: Mike Collins
'''
import sys, os, random,csv,time


#===============================================================================
# Definitions
#===============================================================================
    #RX polarity
VERT=0
HORZ=1

class Test():
    '''
    Test object hold all of the test data for one of the plots on the data collection tab
    '''


    def __init__(self, parent=None):
        '''
        Constructor
        '''
        self.parent=parent
        self.freqCenter=1000e6
        self.freqSpan=500e6
        self.title="Title"
        self.axis=None
        self.rxPolarity=VERT
        self.customer=""
        self.dutLabel=""
        self.dutSN=""
        self.testorName=""
        self.comments=""
        self.sweepTime=25/1e3
        self.distance=3
        self.holdsData=False #true if test has been run
        self.color="#00BB00"
        
        
        self.dataArrayRaw=[]
        self.dataArrayCal=[]
        self.angleArray=[]
        
        
        
    #===========================================================================
    # Axis for drawing
    #===========================================================================
    def setAxis(self,axis):
        self.axis=axis
        
        
        
    def getAxis(self):
        return self.axis
    
    #===========================================================================
    # title
    #===========================================================================
    def setTitle(self,title):
        self.title=title
        self.axis.set_title(self.title,color=self.color,fontsize=11,fontweight=100)
    def getTitle(self):
        return self.title  
    
    #===========================================================================
    # Serial Number
    #===========================================================================
    def setSN(self,SN):
        self.dutSN=SN
        self.axis.text(270,1,self.dutSN)
        
    def getSN(self):
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
    # sweeptime
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
        self.rxPolarity=polarity
    def getRxPolarity(self):
        return self.rxPolarity
    
    #===========================================================================
    # holds data variables return true if test has been run
    #===========================================================================
    def setHoldsData(self,trueFalse):
        self.holdsData=trueFalse
    def getHoldsData(self):
        return self.holdsData
    
##EOF    