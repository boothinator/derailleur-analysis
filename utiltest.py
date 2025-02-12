import unittest
import math
from util import link_length, calculate_chain_angle_at_cog, RollerPositionInfo,\
  calculate_next_roller_position

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

    self.assertGreater(0.1, roller_pos.chain_length_from_roller_to_cog)
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

    self.assertLess(0, roller_pos.chain_length_from_roller_to_cog)
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

    self.assertLess(0, roller_pos.chain_length_from_roller_to_cog)
    self.assertAlmostEqual(cog_lateral_position, roller_pos.roller_lateral_position,
                           delta=close_enough_roller_to_cog_distance)
    # TODO: is this right?
    self.assertAlmostEqual(-0.0066, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position3(self):
     
    link_angle_rad = 0.021156368536983477
    roller_lateral_position = 49.848494563158035
    roller_to_cog_distance = 28.52043214062909
    cog_lateral_position = 44.760000000000005

    print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

    result = calculate_chain_angle_at_cog(jockey_angle_rad=link_angle_rad,
                                          jockey_to_cog_distance=roller_to_cog_distance,
                                          jockey_lateral_position=roller_lateral_position,
                                          cog_lateral_position=cog_lateral_position,
                                          free_play_between_cog_and_chain=0)

    roller_pos = result.roller_pos_list[-1]

    self.assertLess(0, roller_pos.chain_length_from_roller_to_cog)
    self.assertNotAlmostEqual(cog_lateral_position, roller_pos.roller_lateral_position,
                           delta=close_enough_roller_to_cog_distance)
    # TODO: is this right?
    self.assertNotAlmostEqual(-0.0066, roller_pos.prev_link_angle_rad, places=4)
    self.assertEqual(False, roller_pos.can_calculate_next)

  def test_calculate_next_roller_position4(self):
    roller_pos = RollerPositionResult(prev_link_angle_rad= -0.005023570242931465,
                                      chain_length_from_roller_to_cog= 16.012976140890295,
                                      roller_lateral_position= 49.78469548941524)
    
    cog_lateral_position = 44.760000000000005
    
    result = calculate_next_roller_position(roller_pos, cog_lateral_position)

    self.assertEqual(False, result.can_calculate_next)

  def test_calculate_next_roller_position5(self):
    # CUES 10 speed 2nd largest cog
    roller_pos = RollerPositionInfo(prev_link_angle_rad= 0,
                                      chain_length_from_roller_to_cog= 46.5132,
                                      roller_lateral_position= 46.513)
    
    cog_lateral_position = 47.760000000000005
    
    result = calculate_next_roller_position(roller_pos, cog_lateral_position)
    angle_deg = math.degrees(result.prev_link_angle_rad)
    pass

  def test_calculate_next_roller_position6(self):
    # CUES 10 speed 2nd largest cog
    
    cog_lateral_position = 47.760000000000005
    
    result = calculate_chain_angle_at_cog(jockey_angle_rad=0,
                                          jockey_to_cog_distance=46.5132,
                                          jockey_lateral_position=46.513,
                                          cog_lateral_position=cog_lateral_position,
                                          free_play_between_cog_and_chain=0)
    pass

if __name__ == '__main__':
    unittest.main()