from math import pi
import numpy as np
import struct

WGS84_a = 6378137.0
WGS84_b = 6356752.314245

def project_latitude(latitude):
	# https://mathworld.wolfram.com/MercatorProjection.html
	if type(latitude) not in [int, float, np.ndarray, np.float64]:
		print(type(latitude))
		raise TypeError("Latitude must be a real number.")
	if type(latitude) is np.ndarray:
		if np.any(latitude, where=(latitude < -90.0)) or np.any(latitude, where=(latitude > 90.0)):
			raise ValueError("Latitude must be between 90 degrees and -90 degrees")
	elif latitude > 90.0 or latitude < -90:
		raise ValueError("Latitude must be between 90 degrees and -90 degrees")

	latitude = pi / 180 * latitude
	return np.log(np.tan(1/4 * pi + 1/2 * latitude))

def project_longitude(longitude):
	return pi / 180 * longitude

def distance(p1, p2):
	return np.sqrt(np.exp(p2[0]-p1[0], 2) + np.exp(p2[1] - p1[1], 2))

def haversine_distance(p1, p2):
	# φ from ctrl + v, u, 03c6
	# λ from ctrl + v, u, 03bb
	λ1 = p1[0]
	λ2 = p2[0]
	φ1 = p1[1]
	φ2 = p2[1]
	radius = (2 * WGS84_a + WGS84_b) / 3
	#print(f"Using r={radius}")
	return 2 * radius * np.arcsin(np.sqrt(np.sin((φ2 - φ1) / 2) ** 2 + np.cos(φ1) * np.cos(φ2) * np.sin((λ2 - λ1) / 2) ** 2))
	

def solve_right_unit_triangle(c, B):
	# A, B, C are angles
	# a, b, c are sides
	# C is 90 deg
	# a is along x axis
	# b is along y axis

	if c == 0:
		return 0,0

	if B == 0:
		return c, 0

	A = np.arctan(np.cos(B) / (np.sin(B) * np.cos(c)))
	b = np.arccos(np.cos(B) / (np.sin(A) * np.sin(np.pi/2)))
	a = np.arccos(np.cos(A) / (np.sin(B) * np.sin(np.pi/2)))
	return a, b

def point(origin, magnitude, direction):
	mean_radius = (2 * WGS84_a + WGS84_b) / 3
	unit_magnitude = magnitude / mean_radius

	rotations = direction / (2 * np.pi)
	if rotations >= 1:
		direction = direction - int(rotations) * 2 * np.pi

	if (direction < 0):
		raise ValueError(f"Direction must be >= 0. direction=={direction}")

	if direction < np.pi / 2:
		x, y = solve_right_unit_triangle(unit_magnitude, direction)
		offsets = np.array([x, y])
	elif direction < np.pi:
		direction = direction - np.pi / 2
		x, y = solve_right_unit_triangle(unit_magnitude, direction)
		offsets = np.array([-1 * y, x])
	elif direction < 3 * np.pi / 2:
		direction = direction - np.pi
		x, y = solve_right_unit_triangle(unit_magnitude, direction)
		offsets = np.array([-1 * x, -1 * y])
	else:
		direction = direction - 3 * np.pi / 2
		x, y = solve_right_unit_triangle(unit_magnitude, direction)
		offsets = np.array([y, -1 * x])

	offsets = offsets * 180 / np.pi

	return origin + offsets

def circle(center, radius):
	n = 40
	steps = np.linspace(0, 2 * np.pi, num=n, endpoint=False)
	return np.array([point(center, radius, step) for step in steps])

def arc(center, radius, start, angle, n=10):
	steps = np.linspace(start, start + angle, num=n)
	return np.array([point(center, radius, step) for step in steps])

def line(start, magnitude, direction, n=10):
	steps = np.linspace(0, magnitude, num=n)
	return np.array([point(start, step, direction) for step in steps])

def track(center, direction):
	track_width = 8 * 1.220
	# Calculate front straight
	center_to_front_magnitude = np.sqrt((84.39/2)**2 + 36.5**2)
	center_to_front_direction = np.arctan(36.5/(84.39/2)) + np.pi + direction
	front_start_point = point(center, center_to_front_magnitude, center_to_front_direction)
	front_start_point_outer = point(front_start_point, track_width, 3 * np.pi / 2 + direction)
	front_straight = line(front_start_point, 84.39, direction)
	front_straight_outer = line(front_start_point_outer, 84.39, direction)
	track_points = np.append(front_straight, front_straight_outer, 0)

	# Calculate first corner
	first_corner_center = point(center, 84.39/2, direction)
	first_corner = arc(first_corner_center, 36.5, 3*np.pi/2 + direction, np.pi)
	first_corner_outer = arc(first_corner_center, 36.5 + track_width, 3*np.pi/2 + direction, np.pi)
	track_points = np.append(track_points, first_corner, 0)
	track_points = np.append(track_points, first_corner_outer, 0)

	# Calculate back straight
	center_to_back_magnitude = np.sqrt((84.39/2)**2 + 36.5**2)
	center_to_back_direction = np.arctan(36.5/(84.39/2)) + direction
	back_start_point = point(center, center_to_back_magnitude, center_to_back_direction)
	back_start_point_outer = point(back_start_point, track_width, np.pi / 2 + direction)
	back_straight = line(back_start_point, 84.39, np.pi + direction)
	back_straight_outer = line(back_start_point_outer, 84.39, np.pi + direction)
	track_points = np.append(track_points, back_straight, 0)
	track_points = np.append(track_points, back_straight_outer, 0)

	# Calculate second corner
	second_corner_center = point(center, 84.39/2, np.pi + direction)
	second_corner = arc(second_corner_center, 36.5, np.pi/2 + direction, np.pi)
	second_corner_outer = arc(second_corner_center, 36.5 + track_width, np.pi/2 + direction, np.pi)
	track_points = np.append(track_points, second_corner, 0)
	track_points = np.append(track_points, second_corner_outer, 0)

	return track_points

def decode_heart_rate_measurement(bs):
	c1 = (bs[0] & 0x1) == 0
	c2 = (bs[0] & 0x1) > 0
	c3 = (bs[0] & 0x8) > 0
	c4 = (bs[0] & 0x10) > 0
	if c1:
		value = struct.unpack('<B', bs[1:2])[0]
		if c3:
			energy = struct.unpack('<H', bs[2:4])[0]
			if c4:
				rr_intervals = [struct.unpack('<H', bs[i:i+2])[0] for i in range(4,len(bs),2)]
				return value, energy, rr_intervals
		elif c4:
			rr_intervals = [struct.unpack('<H', bs[i:i+2])[0] for i in range(2,len(bs),2)]
			return value, None, rr_intervals
		return value, None, None
	if c2:
		value = struct.unpack('<H', bs[1:3])[0]
		if c3:
			energy = struct.unpack('<H', bs[3:5])[0]
			if c4:
				rr_intervals = [struct.unpack('<H', bs[i:i+2])[0] for i in range(5,len(bs),2)]
				return value, energy, rr_intervals
		elif c4:
			rr_intervals = [struct.unpack('<H', bs[i:i+2])[0] for i in range(3,len(bs),2)]
			return value, None, rr_intervals
		return value, None, None
