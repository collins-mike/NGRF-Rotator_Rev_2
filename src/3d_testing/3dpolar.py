'''
=================================
3D surface with polar coordinates
=================================

Demonstrates plotting a surface defined in polar coordinates.
Uses the reversed version of the YlGnBu color map.
Also demonstrates writing axis labels with latex math mode.

Example contributed by Armin Moser.
'''

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt
import numpy as np


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Create the mesh in polar coordinates and compute corresponding Z.
#r = np.linspace(0, 1.25, 300)
r=[10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10]
p = np.linspace(0, 2*np.pi, 300)

R, P = np.meshgrid(r, p)


Z =[10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10,
10,8,6,4,2,4,6,8,10,10]

# Express the mesh in the cartesian system.
X, Y = R*np.cos(P), R*np.sin(P)

# Plot the surface.
ax.plot_surface(X, Y, Z, cmap=plt.cm.brg)

# Tweak the limits and add latex math labels.
ax.set_zlim(0, 20)
ax.set_xlabel(r'x')
ax.set_ylabel('y')
ax.set_zlabel('Z')

plt.show()