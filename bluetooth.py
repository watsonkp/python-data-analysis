import json
import base64
import struct

import numpy as np
import matplotlib.pyplot as plt

with open('2021-12-03-21-58-15.json', 'r') as f:
	encoded_values = json.loads(f.read())[0]['bluetoothValues']

def decode(encoded_value):
	bs = base64.b64decode(encoded_value)
	# WARNING: An index produces an int. A range retains the bytes type.
	flags = struct.unpack('<B', bs[0:1])[0]
	heart_rate_format = (flags & 0x1) > 0
	sensor_contact_status = (flags & 0x6) > 0
	energy_expended_status = (flags & 0x8) > 0
	rr_interval_flag = (flags & 0x10) > 0

	if not rr_interval_flag:
		return []

	if heart_rate_format and energy_expended_status:
		start = 1 + 2 + 2
	elif heart_rate_format and not energy_expended_status:
		start = 1 + 2
	elif not heart_rate_format and energy_expended_status:
		start = 1 + 1 + 2
	elif not heart_rate_format and not energy_expended_status:
		start = 1 + 1
	return [struct.unpack('<H', bs[i:i + 2])[0] for i in range(start, len(bs), 2)]

def decodeAll(encoded_values):
	encoded_values.sort(key=lambda x: x['timeInterval'])
	rr_intervals = []
	for encoded_value in encoded_values:
		rr_intervals.extend(decode(encoded_value['value']))
	return rr_intervals

decoded_values = decodeAll(encoded_values)
rr_intervals = np.array(decoded_values) / 1024
mean = np.mean(rr_intervals)
std = np.std(rr_intervals)
print(f'n={len(rr_intervals)}, min={np.min(rr_intervals)}, max={np.max(rr_intervals)}, mean={np.mean(rr_intervals)}, σ²={np.var(rr_intervals)}, σ={np.std(rr_intervals)}')

fig, ((full_histogram, partial_histogram)) = plt.subplots(1, 2)
fig.set_size_inches(8, 8)
fig.dpi = 200
full_histogram.hist(rr_intervals, bins=50, density=True)
partial_histogram.hist(rr_intervals, bins=50, range=(mean - 2 * std, mean + 2 * std), density=True)
fig.savefig('rr-intervals.png')
