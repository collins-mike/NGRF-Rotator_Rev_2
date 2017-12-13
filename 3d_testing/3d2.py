import numpy as np
from mayavi import mlab

def r(phi,theta):
    r = np.sin(phi)**2
    return r


phi, theta = np.mgrid[0:2*np.pi:201j, 0:np.pi:101j]

x = r(phi,theta)*np.sin(phi)*np.cos(theta)
y = r(phi,theta)*np.sin(phi)*np.sin(theta)
z = r(phi,theta)*np.cos(phi)

intensity = phi * theta

obj = mlab.mesh(x, y, z, scalars=intensity, colormap='jet')
obj.enable_contours = True
obj.contour.filled_contours = True
obj.contour.number_of_contours = 20
mlab.show()