import argparse
import json
from pathlib import PurePath
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def load_acceleration(file_name):
	with open(file_name) as f:
		raw_data = json.loads(f.read())
	raw_data = raw_data
	rows = len(raw_data)
	columns = len(['timestamp', 'x', 'y', 'z'])
	data = np.zeros((rows, columns))
	for i, datum in enumerate(raw_data):
		data[i,0] = datum["timestamp"]
		data[i,1] = datum["x"]
		data[i,2] = datum["y"]
		data[i,3] = datum["z"]
	start = np.min(data[:,0])
	data[:,0] = data[:,0] - start
	return data

def periodicity(data):
	#data - np.mean(data)
	#data / np.var(data)
	correlation = signal.correlate(data[:500], data, mode="valid")
	lags = signal.correlation_lags(data[:500].size, data.size, mode="valid")
	lag = lags[np.argmax(correlation)]
	return lags, correlation

def peak_lag_correlations(data):
	min_height = np.max(data) * 0.9
#	data > threshold
	peaks, properties = signal.find_peaks(data, height=min_height)
	return peaks

def detect_repeats(data):
	print('Detect repeating motion')
	print(data.shape)
	variance = np.var(data)
	variance = variance ** 2
	mean = np.mean(data)
	data = data - mean
	print(f"mean={mean}, variance={variance}")
	sample_period = 0.01
	window_period = 3.0
	n = int(window_period / sample_period)
	# vectorize?
	# Don't bother since it will be a stream?
	i = 0
	print(f"i={i}, n={n}")
	motion = data[i:i+n]
	print(f"motion={len(motion)}, {motion.shape}")
	window = data[i+n:i+3*n]
	print(f"window={len(window)}, {window.shape}")
	correlation = signal.correlate(motion, window, mode="valid")
	correlation = correlation / variance
	print(f"correlation={len(correlation)}, {correlation.shape}")
	lags = signal.correlation_lags(motion.size, window.size, mode="valid")
	max_height = np.max(correlation)
	print(max_height)
	# TODO: Need to normalize to 1.0 so that weak peaks can be ignored
	peaks, properties = signal.find_peaks(correlation, height=0.9 * max_height)

def plot_acceleration(file_name, data):
	figure, ((acceleration_x),(acceleration_y),(acceleration_z),(frequency),(correlations)) = plt.subplots(5, 1)
	figure.set_size_inches(16, 8)
	figure.dpi = 200
	acceleration_x.scatter(data[:,0], data[:,1], marker='.', s=1)
	acceleration_x.set_ylabel('Acceleration in x (G)')
	acceleration_x.set_xlabel('Time (seconds)')
	acceleration_x.set_ylim(bottom=-3, top=3)
	acceleration_y.scatter(data[:,0], data[:,2], marker='.', s=1)
	acceleration_y.set_ylabel('Acceleration in y (G)')
	acceleration_y.set_xlabel('Time (seconds)')
	acceleration_y.set_ylim(bottom=-3, top=3)
	acceleration_z.scatter(data[:,0], data[:,3], marker='.', s=1)
	acceleration_z.set_ylabel('Acceleration in z (G)')
	acceleration_z.set_xlabel('Time (seconds)')
	acceleration_z.set_ylim(bottom=-3, top=3)
	frequency.magnitude_spectrum(data[:,1], Fs=1/0.01)
	frequency.set_xlim(left=0, right=10)

#	lags, correlation = periodicity(data[:,1])
#	peak_lags = peak_lag_correlations(correlation)
#	colors = np.array(['b'] * len(lags))
#	colors[peak_lags[0]] = 'r'
#	colors[peak_lags] = 'r'
#	correlations.scatter(0.01 * lags, correlation, marker='.', s=1, c=colors)
#	correlations.set_xlabel('Lag (seconds)')
#	occurences = 0.01 * lags[peak_lags]
	detect_repeats(data[:,1])

	figure.savefig(file_name)

parser = argparse.ArgumentParser()
parser.add_argument("input", help="file path to the input data")
args = parser.parse_args()

data = load_acceleration(args.input)
truncated_output_name = PurePath(args.input).with_suffix('').name + '-motion'
truncated_output_path = PurePath('output').joinpath(truncated_output_name).with_suffix('.png')
output_name = PurePath(args.input).with_suffix('').name + '-motion-full'
output_path = PurePath('output').joinpath(output_name).with_suffix('.png')
plot_acceleration(truncated_output_path, data[1200:2400])
plot_acceleration(output_path, data[:1500])
