'''
======================
Triangular 3D surfaces
======================

Plot a 3D surface with a triangular mesh.
'''

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np


n_radii = 8
n_angles = 100


# Make radii and angles spaces (radius r=0 omitted to eliminate duplication).
radii = np.linspace(0.125, 20, n_radii)
#angles = np.linspace(0, 2*np.pi, n_angles, endpoint=False)
angles=[
-68.07631393, -65.62100996,	-61.44096837,-59.4762035, -58.4601175, -58.11713228,-59.74490403,-60.80763988,-61.37126124,-61.34877379,
-61.04435235, -60.73300063,	-61.82241352,-66.23947333,-67.56640742,-63.69039879,-62.37221927,-65.57574481,-69.12937471,-67.29072384,
-66.99387459, -70.21430063,	-75.69038103,-72.81268974,-67.37005597,-68.82066627,-78.0904276, -68.17893289,-67.65253544,-77.47222446,
-65.61789733, -62.06122698,	-62.48948178,-67.49615477,-72.35159777,-66.65558318,-65.03312166,-64.86122801,-64.88777268,-65.94398886,
-66.87005078, -68.1186652,	-68.49631656,-71.03915594,-73.62821193,-77.87237493,-77.80020641,-77.51671366,-77.1585423,-77.81257137,
-77.24132592, -75.81842573,	-73.15429506,-73.35627997,-69.91199777,-69.68871323,-68.84561117,-71.0231075, -74.80570806,-77.85146116,
-72.97358413, -71.83732021,	-71.69183458,-76.93780755,-77.72822547,-69.13023109,-64.6426248, -63.93779598,-67.74241415,-76.34882237,
-69.37970882, -66.49575555,	-67.97510085,-68.40106746,-71.09635668,-76.75997278,-68.16501243,-65.36448224,-67.69192959,-77.61635295,
-67.04808028, -63.04667573,	-62.03227738,-62.88693517,-64.40459093,-63.95323083,-64.19280311,-61.2447391, -59.66184834,-60.57570525,
-63.4609012,  -64.00277353,	-60.80242018,-56.96341075,-56.39344622,-56.87008325,-57.65077536,-59.98051915,-63.39141557,-67.1151747,
-67.1151747
]


# Repeat all angles for each radius.
#angles = np.repeat(angles[..., np.newaxis], n_radii, axis=1)

# Convert polar (radii, angles) coords to cartesian (x, y) coords.
# (0, 0) is manually added at this stage,  so there will be no duplicate
# points in the (x, y) plane.
x = np.append(0, (radii*np.cos(angles)).flatten())
y = np.append(0, (radii*np.sin(angles)).flatten())

# Compute z to make the pringle surface.
z = np.sin(-x*y)

fig = plt.figure()
ax = fig.gca(projection='3d')

ax.plot_trisurf(x, y, z, linewidth=0.2, antialiased=True)

plt.show()