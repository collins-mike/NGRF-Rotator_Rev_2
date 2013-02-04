from specan import *
from arcus import *

def fprint(msg):
	print msg
	
sa = SpecAnalyzer(fprint)
sa.open_device("GPIB0::18")


