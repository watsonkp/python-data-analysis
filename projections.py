import json
import matplotlib.pyplot as plt
import numpy as np

WGS84_a = 6378137.0
WGS84_b = 6356752.314245

# GNSS coordinates in degreses. Returns spherical coordinates in radians
def gnss_to_spherical(latitude, longitude, altitude):
    # TODO: Calculate radius based on latitude and ellipsoid model
    radius = (2 * WGS84_a + WGS84_b) / 3
    return np.array([np.pi / 2 - np.radians(latitude), np.radians(longitude), radius + altitude])

def spherical_to_euclidean(theta, phi, radius):
    x = radius * np.cos(phi) * np.sin(theta)
    y = radius * np.sin(phi) * np.sin(theta)
    z = radius * np.cos(theta)
    return np.array([x, y, z])

def euclidean_distance(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return np.sqrt(np.power(x2 - x1, 2) + np.power(y2 - y1, 2) + np.power(z2 - z1, 2))

def gnss_distance(point1, point2):
    start = spherical_to_euclidean(*gnss_to_spherical(*point1))
    end = spherical_to_euclidean(*gnss_to_spherical(*point2))
    return euclidean_distance(start, end)

def relative_gnss_position(point, origin):
    euclidean_point = spherical_to_euclidean(*gnss_to_spherical(*point))
    euclidean_origin = spherical_to_euclidean(*gnss_to_spherical(*origin))
    return np.array([euclidean_point[0] - euclidean_origin[0],
        euclidean_point[1] - euclidean_origin[1],
        euclidean_point[2] - euclidean_origin[2]])

def haversine_distance(p2, p1):
    φ1, λ1 = p1
    φ1 = np.radians(φ1)
    λ1 = np.radians(λ1)
    φ2, λ2 = p2
    φ2 = np.radians(φ2)
    λ2 = np.radians(λ2)
    radius = (2 * WGS84_a + WGS84_b) / 3
    return 2 * radius * np.arcsin(np.sqrt(np.sin((φ2 - φ1) / 2) ** 2 + np.cos(φ1) * np.cos(φ2) * np.sin((λ2 - λ1) / 2) ** 2))

def gnss_course(point1, point2):
    theta1, phi1, _ = point1
    theta2, phi2, _ = point2
    delta_theta = theta2 - theta1
    delta_phi = phi2 - phi1

def bearing(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2
    x = lon2 - lon1
    y = lat2 - lat1
    return np.arctan2(y, x)

def position_delta(theta, distance):
    return np.array([distance * np.cos(theta), distance * np.sin(theta)])

path = '2022-06-05-16-09-27.json'
with open(path, 'r') as f:
    recording = json.load(f)

# Sort locations in each split by timeInterval
splits = [sorted(split['locations'], key=lambda location: location['timeInterval']) for split in recording]
# Sort splits by their first timeInterval
splits.sort(key=lambda split: split[0]['timeInterval'])

origin = (splits[1][0]['latitude'], splits[1][0]['longitude'], splits[1][0]['altitude'])
#for value in splits[1]:
#    position = relative_gnss_position((value['latitude'], value['longitude'], value['altitude']), origin)
#    distance = gnss_distance(origin, (value['latitude'], value['longitude'], value['altitude']))
data_array = np.array([relative_gnss_position(np.array([value['latitude'], value['longitude'], value['altitude']]), origin) for value in splits[1]])
print(data_array.shape)
#print(np.linalg.eig(data_array))

#positions = [np.array([0.0, 0.0])]
#for pair in zip(splits[1][1:], splits[1]):
#    point1 = pair[0]['latitude'], pair[0]['longitude']
#    point2 = pair[1]['latitude'], pair[1]['longitude']
#    distance = haversine_distance(point2, point1)
#    theta = bearing(point2, point1)
#    positions.append(position_delta(theta, distance))

positions = [np.array([0.0, 0.0])]
for pair in zip(splits[1][1:], splits[1]):
    time_delta = pair[0]['timeInterval'] - pair[1]['timeInterval']
    speed = pair[1]['speed']
    course = pair[1]['course']
    positions.append(position_delta(np.radians(course), speed * time_delta))

#print(np.add.accumulate(np.array(positions)))
#print(data_array[:, 0])
#x = np.linspace(0, 2 * np.pi, 200)
#y = np.sin(x)
fig, ax = plt.subplots()
#fig = plt.figure()
cumulative_positions = np.add.accumulate(np.array(positions))
ax.scatter(cumulative_positions[:, 0], cumulative_positions[:, 1])
#ax = fig.add_subplot(projection='3d')
#ax.stem(cumulative_positions[:, 0], cumulative_positions[:, 1], np.array([location['altitude'] for location in splits[1]]))
#ax.plot(x, y)

#fig = plt.figure()
#ax = fig.add_subplot(projection='3d')
#ax.scatter(data_array[:, 0], data_array[:, 1], data_array[:, 2], marker='o')
#ax.set_xlabel('X Label')
#ax.set_ylabel('Y Label')
#ax.set_zlabel('Z Label')
plt.show()
