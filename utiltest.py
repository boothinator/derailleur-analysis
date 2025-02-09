import unittest
import math
from util import link_length, close_enough_roller_to_cog_distance, calculate_chain_angle_at_cog

class TestUtil(unittest.TestCase):
  def test_calculate_next_roller_position(self):
     
    link_angle_rad = math.radians(0)
    roller_lateral_position = 15
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    result = calculate_chain_angle_at_cog(jockey_angle_rad=link_angle_rad,
                                          jockey_to_cog_distance=roller_to_cog_distance,
                                          jockey_lateral_position=roller_lateral_position,
                                          cog_lateral_position=cog_lateral_position,
                                          free_play_between_cog_and_chain=0)

    roller_pos = result.roller_pos_list[-1]

    self.assertGreater(0.1, roller_pos.roller_to_cog_distance)
    self.assertAlmostEqual(cog_lateral_position, roller_pos.roller_lateral_position,
                           delta=close_enough_roller_to_cog_distance)
    self.assertEqual(0, roller_pos.prev_link_angle_rad)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position2(self):
     
    link_angle_rad = math.radians(-1.8)
    roller_lateral_position = 15
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    result = calculate_chain_angle_at_cog(jockey_angle_rad=link_angle_rad,
                                          jockey_to_cog_distance=roller_to_cog_distance,
                                          jockey_lateral_position=roller_lateral_position,
                                          cog_lateral_position=cog_lateral_position,
                                          free_play_between_cog_and_chain=0)

    roller_pos = result.roller_pos_list[-1]

    self.assertLess(0, roller_pos.roller_to_cog_distance)
    self.assertAlmostEqual(cog_lateral_position, roller_pos.roller_lateral_position,
                           delta=close_enough_roller_to_cog_distance)
    self.assertAlmostEqual(0.0026, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position3(self):
     
    link_angle_rad = math.radians(-3)
    roller_lateral_position = 15.5
    roller_to_cog_distance = link_length * 3
    cog_lateral_position = 15

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    result = calculate_chain_angle_at_cog(jockey_angle_rad=link_angle_rad,
                                          jockey_to_cog_distance=roller_to_cog_distance,
                                          jockey_lateral_position=roller_lateral_position,
                                          cog_lateral_position=cog_lateral_position,
                                          free_play_between_cog_and_chain=0)

    roller_pos = result.roller_pos_list[-1]

    self.assertLess(0, roller_pos.roller_to_cog_distance)
    self.assertAlmostEqual(cog_lateral_position, roller_pos.roller_lateral_position,
                           delta=close_enough_roller_to_cog_distance)
    # TODO: is this right?
    self.assertAlmostEqual(-0.0066, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

if __name__ == '__main__':
    unittest.main()