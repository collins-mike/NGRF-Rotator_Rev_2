'''
========================
3D surface (solid color)
========================

Demonstrates a very basic plot of a 3D surface using a solid color.
'''

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np

size=100


fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x_vals = np.ndarray(shape=(size,size))
y_vals = np.ndarray(shape=(size,size))
z_vals = np.ndarray(shape=(size,size))
#z_vals = np.ndarray(shape=size,dtype= np.int32)

# Make data
u = np.ndarray(shape=size)
for i in range (0,size):
	u[i]=(i*((2*np.pi)/size))
	
v = np.ndarray(shape=size)
for i in range (0,size):
	v[i]=(i*(np.pi/size))

	

for i in range(0,size):
	x_vals[i]=(10 * np.outer(np.cos(u[i]), np.sin(v[i])))
print x_vals
for i in range(0,size):
	y_vals[i]=(10 * np.outer(np.sin(u[i]), np.sin(v[i])))
print y_vals
for i in range(0,size):
	z_vals[i]=(10 * np.outer(np.ones(np.size(u[i])), np.cos(v[i])))
print z_vals
	
# Plot the surface
ax.plot_surface(x_vals, y_vals, z_vals, color='b')


plt.show()
