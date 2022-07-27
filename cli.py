import argparse
import json
import base64
from pathlib import PurePath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import geodesy

WGS84_a = 6378137.0
WGS84_b = 6356752.314245

# Print total distance using distance between points on Mercator projection
# This is probably a very bad way of doing this, but it's an interesting reference point
def mercator_distance(latitude, longitude):
	y = geodesy.project_latitude(latitude)
	x = geodesy.project_longitude(longitude)
	# Scale latitude to twice the WGS84 semi-minor axis 
	y = 2 * WGS84_b * y / np.pi
	# Normalize latitude to the smallest value so distances are relatable
	y = y - np.min(y)
	# Scale longitude to the WGS84 equatorial circumference
	x = 2 * np.pi * WGS84_a * x / 2 / np.pi
	# Normalize longitude to the smallest value so distances are relatable
	x = x - np.min(x)
	mercator = np.array([x, y])
	#mercator_distance = np.sum(np.sqrt(np.sum(np.power(data[1:,1:] - data[:-1,1:], 2), 1)))
	mercator_distance = np.sum(np.sqrt(np.sum(np.power(mercator[:,:-1] - mercator[:,1:], 2), 0)))
	return mercator_distance

# Straight line distance between two points. Not arc length.
def cartesian_distance(latitude, longitude):
	phi = np.pi / 2 - latitude * np.pi / 180
	theta = longitude * np.pi / 180
	# Let r be the average radius according to WGS84
	r = (2 * WGS84_a + WGS84_b) / 3
	x = r * np.sin(theta) * np.cos(phi)
	y = r * np.sin(theta) * np.sin(phi)
	z = r * np.cos(theta)
	cartesian = np.array([x, y, z])
	cartesian_distance = np.sum(np.sqrt(np.sum(np.power(cartesian[:,:-1] - cartesian[:,1:], 2), 0)))
	return cartesian_distance

def parse_locations(data_in):
	# Added course and speed
	properties = ['timeInterval', 'longitude', 'latitude', 'altitude', 'horizontalAccuracy', 'verticalAccuracy', 'speed', 'speedAccuracy', 'course', 'courseAccuracy']
	i = len(data_in['locations'])
	j = len(properties)
	data_out = np.zeros((i, j), dtype=float)
	for i, location in enumerate(data_in['locations']):
		for j, prop in enumerate(properties):
			data_out[i, j] = location.get(prop)
	return data_out

def parse_bluetooth(data_in):
	properties = ['timeInterval', 'value']
	i = len(data_in['bluetoothValues'])
	j = len(properties)
	data_out = np.zeros((i, j), dtype=int)
	rr_intervals = np.zeros([0,1])
	energy_values = np.zeros([0,1])
	for i, bluetooth_value in enumerate(data_in['bluetoothValues']):
		for j, prop in enumerate(properties):
			if prop is 'value':
				value, energy_value, rr_interval = geodesy.decode_heart_rate_measurement(base64.b64decode(bluetooth_value[prop]))
				data_out[i, j] = value
				if energy_value:
					energy_values = np.append(energy_values, energy_value)
				if rr_interval:
					rr_intervals = np.append(rr_intervals, rr_interval)
			else:
				data_out[i, j] = bluetooth_value[prop]
	return data_out, energy_values, rr_intervals

parser = argparse.ArgumentParser()
parser.add_argument("input", help="file path to the input data")
parser.add_argument("-split", type=int, required=False, help="index of split in data to process")
parser.add_argument("--track", action='store_true', help="overlay a 400m track on position data")
parser.add_argument("--video", action='store_true', help="render a video of position data")
args = parser.parse_args()

with open(args.input) as f:
	raw_data = json.loads(f.read())

def summary(file_name, data, heart_rate, overlay=False):
	sequential_data = data[data[:,0].argsort()]
	figure, ((position_ax, accuracy_ax), (altitude_ax, distance_ax)) = plt.subplots(2,2)
	position_ax.set_aspect('equal')
	figure.set_size_inches(8, 6)
	figure.dpi = 200

	plot_position(position_ax, data, overlay)
	#plot_heart_rate(heart_rate_ax, heart_rate)
	plot_distance(distance_ax, data)

	altitude_ax.set_xlabel('Time (minute)')
	altitude_ax.set_ylabel('Altitude (m)')
	altitude_ax.scatter(sequential_data[:,0] / 60, sequential_data[:,3], marker='.', s=1)

	accuracy_ax.set_xlabel('Time (minute)')
	accuracy_ax.set_ylabel('Accuracy (m)')
	accuracy_ax.scatter(sequential_data[:,0], sequential_data[:,4], marker='.', s=1, label='Horizontal')
	accuracy_ax.scatter(sequential_data[:,0], sequential_data[:,5], marker='.', s=1, label='Vertical')
	accuracy_ax.legend()

	figure.savefig(file_name)

def plot_distance(ax, data):
	ax.yaxis.grid(True, which='major')
	ax.set_xlabel('Time (minute)')
	ax.set_ylabel('Distance (km)')
	sequential_data = data[data[:,0].argsort()]
	distance = np.zeros([len(data[:,1])-1, 1])
	for i in range(len(data[:,1])-1):
		delta = geodesy.haversine_distance(np.radians(sequential_data[i+1,1:3]), np.radians(sequential_data[i,1:3]))
		if i == 0:
			distance[i] = delta
		else:
			distance[i] = distance[i-1] + delta

	ax.scatter(sequential_data[:-1,0] / 60, distance / 1000, marker='.', s=1)

def video(file_name, data):
	sequential_data = data[data[:,0].argsort()]
	figure, ((anim)) = plt.subplots(1,1)
	figure.set_size_inches(8, 6)
	figure.dpi = 200
	#color='#404040')
	plot = anim.scatter([], [], marker='.', s=1)
	# Do not use offsets on axes for readability
	anim.ticklabel_format(useOffset=False)

	# TODO: text vs. figtext?
	text = figure.text(.8, .8, str(-1), fontsize=24)

	def init():
		anim.set_aspect('equal')
		anim.set_xlim(np.min(sequential_data[:,1]), np.max(sequential_data[:,1]))
		anim.set_ylim(np.min(sequential_data[:,2]), np.max(sequential_data[:,2]))
		text.set_text(str(0))
		return [plot, text]

	def update(frame):
		if frame % 100 == 0:
			print(f"Frame {frame}/{len(sequential_data)}")
		plot.set_offsets(sequential_data[max(0,frame-100):frame,1:3])
		text.set_text(str(sequential_data[frame, 0] - sequential_data[0, 0]))
		return [plot, text]

	ani = FuncAnimation(figure, update, frames=range(len(sequential_data)), init_func=init, blit=False)

	ani.save(file_name)

def plot_heart_rate(ax, heart_rate):
	ax.yaxis.grid(True, which='major')
	ax.set_ylabel('Heart Rate (BPM)')
	ax.set_yticks([95, 114, 133, 152, 171, 190])
	ax.set_xlabel('Time (minute)')
	ax.scatter(heart_rate[:,0] / 60, heart_rate[:,1], marker='.', s=1)

def heart_summary(file_name, heart_rate, rr_intervals):
	figure, ((beats, rr_rate), (intervals, variability)) = plt.subplots(2,2)
	figure.set_size_inches(8, 6)
	figure.dpi = 200
	plot_heart_rate(beats, heart_rate)
	rr_rate.scatter(range(len(rr_intervals)), rr_intervals / 1024), marker='.', s=1)
	intervals.scatter(range(len(rr_intervals)), rr_intervals, marker='.', s=1)
	variability.hist(rr_intervals, bins=40)
	figure.savefig(file_name)

def plot_velocity(ax, data):
	ax.set_ylabel('Velocity m/s')
	ax.set_xlabel('Time (minute)')
	ax.scatter(data[:,0], data[:,6], marker='.', s=1)

def velocity_summary(file_name, data):
	sequential_data = data[data[:,0].argsort()]
	figure, ((speed, course), (speed_accuracy, course_accuracy)) = plt.subplots(2,2)
	figure.set_size_inches(8, 6)
	figure.dpi = 200
	plot_velocity(speed, sequential_data)
	
	speed_accuracy.scatter(data[:,0], data[:,7], marker='.', s=1)
	speed_accuracy.set_ylabel('Speed accuracy')
	speed_accuracy.set_xlabel('Time (minute)')

	# Quiver plot of course at projection of latitude and longitude
	vector_x = np.sin(sequential_data[:,8] * np.pi / 180)
	vector_y = np.cos(sequential_data[:,8] * np.pi / 180)
	position = np.zeros(sequential_data.shape)
	position[:,1] = geodesy.project_longitude(sequential_data[:,1])
	position[:,2] = geodesy.project_latitude(sequential_data[:,2])
	course.set_aspect('equal')
	course.quiver(position[20:70,1], position[20:70,2], vector_x[20:70], vector_y[20:70])

	course_accuracy.scatter(data[:,0], data[:,9], marker='.', s=1)
	course_accuracy.set_ylabel('Course accuracy')
	course_accuracy.set_xlabel('Time (minute)')

	figure.savefig(file_name)

def plot_position(ax, data, overlay=False):
	ax.set_xlabel('Longitude (degrees)')
	ax.set_ylabel('Latitude (degrees)')
	ax.set_aspect('equal')

	# Optionally add an overlay of a 400m track
	if overlay:
		center_x = (np.max(data[:,1]) + np.min(data[:,1])) / 2
		center_y = (np.max(data[:,2]) + np.min(data[:,2])) / 2
		track_overlay = geodesy.track([center_x, center_y], np.pi/4)
		track_overlay[:,0] = geodesy.project_longitude(track_overlay[:,0])
		track_overlay[:,1] = geodesy.project_latitude(track_overlay[:,1])
		ax.scatter(track_overlay[:,0], track_overlay[:,1], marker='.', s=4)

	# Project position data onto plot
	projection = np.zeros(data.shape)
	projection[:,1] = geodesy.project_longitude(data[:,1])
	projection[:,2] = geodesy.project_latitude(data[:,2])
	ax.scatter(projection[:,1], projection[:,2], marker='.', s=1)

	# Do not use offsets on axes for readability
	ax.ticklabel_format(useOffset=False)

split_suffix = ''
if args.split is not None:
	split_suffix = '-' + str(args.split)
	data = parse_locations(raw_data[args.split])
	heart_rate, _, rr_intervals = parse_bluetooth(raw_data[args.split])
else:
	data = np.concatenate([parse_locations(data) for data in raw_data], axis=0)
	heart_rate = []
	rr_intervals = []
	for b_data in raw_data:
		hr, _, rr = parse_bluetooth(b_data)
		heart_rate.append(hr)
		rr_intervals.append(rr)
	heart_rate = np.concatenate(heart_rate, 0)
	rr_intervals = np.concatenate(rr_intervals, 0)

if args.video:
	name = PurePath(args.input).with_suffix('').name + '-video' + split_suffix
	video_path = PurePath('output').joinpath(name).with_suffix('.mp4')
	video(video_path, data)

name = PurePath(args.input).with_suffix('').name + split_suffix
summary_path = PurePath('output').joinpath(name).with_suffix('.png')

# Render a scatter plot of the position data
position_figure, ((position_ax)) = plt.subplots(1,1)
position_figure.set_size_inches(8, 6)
position_figure.dpi = 200
if args.track:
	plot_position(position_ax, data, overlay=True)
	summary(summary_path, data, heart_rate, overlay=True)
else:
	plot_position(position_ax, data)
	summary(summary_path, data, heart_rate)
name = PurePath(args.input).with_suffix('').name + '-position' + split_suffix
position_path = PurePath('output').joinpath(name).with_suffix('.png')
position_figure.savefig(position_path)

name = PurePath(args.input).with_suffix('').name + '-heart-rate' + split_suffix
heart_summary_path = PurePath('output').joinpath(name).with_suffix('.png')
heart_summary(heart_summary_path, heart_rate, rr_intervals)

name = PurePath(args.input).with_suffix('').name + '-velocity' + split_suffix
velocity_summary_path = PurePath('output').joinpath(name).with_suffix('.png')
velocity_summary(velocity_summary_path, data)
