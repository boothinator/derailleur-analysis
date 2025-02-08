import unittest
import math
from util import link_length, RollerPositionInfo, calculate_next_roller_position

class TestUtil(unittest.TestCase):
  def test_calculate_next_roller_position(self):
     
    link_angle_rad = math.radians(0)
    roller_lateral_position = 15
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    roller_pos = RollerPositionInfo(prev_link_angle_rad=link_angle_rad,
                                      roller_lateral_position=roller_lateral_position,
                                      roller_to_cog_distance=roller_to_cog_distance)

    while roller_pos.can_calculate_next:
      roller_pos = calculate_next_roller_position(roller_pos, cog_lateral_position)

    self.assertEqual(0, roller_pos.roller_to_cog_distance)
    self.assertEqual(cog_lateral_position, roller_pos.roller_lateral_position)
    self.assertEqual(0, roller_pos.prev_link_angle_rad)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position2(self):
     
    link_angle_rad = math.radians(-1.8)
    roller_lateral_position = 15
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    roller_pos = RollerPositionInfo(prev_link_angle_rad=link_angle_rad,
                                      roller_lateral_position=roller_lateral_position,
                                      roller_to_cog_distance=roller_to_cog_distance)

    while roller_pos.can_calculate_next:
      roller_pos = calculate_next_roller_position(roller_pos, cog_lateral_position)

    self.assertEqual(0, roller_pos.roller_to_cog_distance)
    self.assertEqual(cog_lateral_position, roller_pos.roller_lateral_position)
    self.assertAlmostEqual(0.0026, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position3(self):
     
    link_angle_rad = math.radians(-3)
    roller_lateral_position = 15.5
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    roller_pos = RollerPositionInfo(prev_link_angle_rad=link_angle_rad,
                                      roller_lateral_position=roller_lateral_position,
                                      roller_to_cog_distance=roller_to_cog_distance)

    while roller_pos.can_calculate_next:
      roller_pos = calculate_next_roller_position(roller_pos, cog_lateral_position)

    self.assertEqual(0, roller_pos.roller_to_cog_distance)
    self.assertEqual(cog_lateral_position, roller_pos.roller_lateral_position)
    # TODO: is this right?
    self.assertAlmostEqual(-0.0066, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

if __name__ == '__main__':
    unittest.main()