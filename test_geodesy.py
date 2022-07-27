import unittest
from geodesy import project_latitude
import numpy as np
import geodesy

class TestGeodesy(unittest.TestCase):
	def test_projection(self):
		self.assertAlmostEqual(project_latitude(0.0), 0.0)
		# TODO: Address limits
#		 self.assertEqual(project_latitude(90.0), np.pi/4)
#		 self.assertEqual(project_latitude(-90.0), -np.pi/4)
#		 self.assertEqual(project_latitude(45.0), np.pi/8)

	def test_values(self):
		self.assertRaises(ValueError, project_latitude, 135.0)

	def test_types(self):
		self.assertRaises(TypeError, project_latitude, "45.0")

#	def test_solve_triangle(self):
#		self.assertEqual(geodesy.solve_right_unit_triangle(np.pi/64, np.pi/8), 4)

	def test_haversine(self):
		p1 = np.radians([-74, 40 + 42/60])
		p2 = np.radians([5/60, 51 + 32/60])
		np.testing.assert_allclose(geodesy.haversine_distance(p1, p2), 5533093.4, rtol=1)

		p1 = np.radians([-99.436554, 41.507483])
		p2 = np.radians([-98.315949, 38.504048])
		np.testing.assert_allclose(geodesy.haversine_distance(p1, p2), 347300, rtol=1)

#	def test_add_bearing(self):
#		point = np.array([0.0, 0.0])
#		magnitude = 5000000
#		direction = np.pi / 4
#		self.assertTrue((geodesy.add_bearing(point, magnitude, direction) == np.array([45.0, 45.0])).all())
#
#	def test_add_bearing_north(self):
#		point = np.array([0.0, 0.0])
#		magnitude = 5000000
#		direction = 0
#		self.assertRaises(ValueError, geodesy.add_bearing, point, magnitude, direction)
