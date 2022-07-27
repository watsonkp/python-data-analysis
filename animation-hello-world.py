import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

fig, ax = plt.subplots()
xdata, ydata = [], []
xdata = np.linspace(0, 2 * np.pi, 128)
ydata = np.sin(xdata)
ln, = plt.plot([], [], 'ro')

def init():
	ax.set_xlim(0, 2 * np.pi)
	ax.set_ylim(-1, 1)
	return ln,

def update(frame):
#	 xdata.append(frame)
#	 ydata.append(np.sin(frame))
	ln.set_data(xdata[:frame], ydata[:frame])
	return ln,

ani = FuncAnimation(fig, update, frames=range(len(xdata)), init_func=init, blit=True)
ani.save('animation.mp4')
