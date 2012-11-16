#!/usr/bin/env python
#
# matplotlib now has a PolarAxes class and a polar function in the
# matplotlib interface.  This is considered alpha and the interface
# may change as we work out how polar axes should best be integrated
#
# The only function that has been tested on polar axes is "plot" (the
# pylab interface function "polar" calls ax.plot where ax is a
# PolarAxes) -- other axes plotting functions may work on PolarAxes
# but haven't been tested and may need tweaking.
#
# you can get a PolarSubplot instance by doing, for example
#
#   subplot(211, polar=True)
#
# or a PolarAxes instance by doing
#   axes([left, bottom, width, height], polar=True)
#
# The view limits (eg xlim and ylim) apply to the lower left and upper
# right of the rectangular box that surrounds to polar axes.  Eg if
# you have
#
#  r = arange(0,1,0.01)
#  theta = 2*pi*r
#
# the lower left corner is 5/4pi, sqrt(2) and the
# upper right corner is 1/4pi, sqrt(2)
#
# you could change the radial bounding box (zoom out) by setting the
# ylim (radial coordinate is the second argument to the plot command,
# as in MATLAB, though this is not advised currently because it is not
# clear to me how the axes should behave in the change of view limits.
# Please advise me if you have opinions.  Likewise, the pan/zoom
# controls probably do not do what you think they do and are better
# left alone on polar axes.  Perhaps I will disable them for polar
# axes unless we come up with a meaningful, useful and functional
# implementation for them.
#
# See the pylab rgrids and thetagrids functions for
# information on how to customize the grid locations and labels
import matplotlib
import numpy as np
from matplotlib.pyplot import figure, show, rc, grid

# radar green, solid grid lines
rc('grid', linewidth=1, linestyle='-')
rc('xtick', labelsize=15)
rc('ytick', labelsize=15)
"""
# force square figure and square axes looks better for polar, IMO
width, height = matplotlib.rcParams['figure.figsize']
size = min(width, height)
# make a square figure
fig = figure(figsize=(size, size))
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], polar=True)
"""
fig = figure()
ax = fig.add_subplot(111,polar=True)

data=[[   0. ,  -56.8,  -77.4,  -55.3,  -53.6],
	   [  45. ,  -48.8,  -61.5,  -53.9,  -53.6],
	   [  90. ,  -70.5,  -82. ,  -55.8,  -54.5],
	   [ 135. ,  -64.7,  -87.7,  -58.9,  -58.6],
	   [ 180. ,  -72.5,  -85.6,  -58.6,  -56.8],
	   [ 225. ,  -66.6,  -73.5,  -57.1,  -55.5],
	   [ 270. ,  -56.8,  -73.7,  -50.9,  -49.6],
	   [ 315. ,  -55.7,  -64.8,  -48.3,  -48.3],
	   [ 360. ,  -56.8,  -77.4,  -55.3,  -53.6]]
data=np.array(data)
r=data[:,1:]
theta = [   0.,   45.,   90.,  135.,  180.,  225.,  270.,  315.,  360.]
theta = np.array(theta) * np.pi /180
ax.plot(theta, r, lw=1.5)
"""
gridmin=10*round(np.amin(r)/10)
if gridmin>np.amin(r):
	gridmin = gridmin-10
gridmax=10*round(np.amax(r)/10)
if gridmax < np.amax(r):
		gridmax=gridmax+10
ax.set_ylim(gridmin,gridmax)
ax.set_yticks(np.arange(gridmin,gridmax,(gridmax-gridmin)/5))
"""
grid(True)

#shrink
box = ax.get_position()
ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
ax.autoscale_view(True,True,True)
#ax.legend(loc='center left', ('label1', 'label2', 'label3','label4') ,fancybox=True, shadow=True,bbox_to_anchor=(1, 0.5))
leg=ax.legend(('label1', 'label2', 'label3','label4444444444444444444444'))#,loc='center left', bbox_to_anchor=(1, 0.5))
leg.draggable(True)
ax.set_title("And there was much rejoicing!", fontsize=20)
show()