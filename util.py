import numpy as np
from pydantic import BaseModel
from typing import Iterable
import math

# Could calculate using dropout thickness (7 to 8 mm for shimano?) and then use the distance from 
# end of cassette to dropout to figure out the first cog position, maybe
smallest_cog_position = 15 # TODO: put this on the cassette, or figure out from derailleur
default_links_from_jockey_to_smallest_cog = 3
max_cable_pull = 50 # Assume that no shifter will be able to pull 50 mm of cable
chain_max_free_yaw = 1.5
chain_max_free_yaw_rad = math.pi * chain_max_free_yaw / 180
link_length = 12.7

def get_cassette_cog_teeth(min_tooth, max_tooth, cog_count):
  min_tooth_x = np.log(min_tooth)
  max_tooth_x = np.log(max_tooth)

  a = (max_tooth_x - min_tooth_x) / (cog_count - 1)

  cur_teeth = min_tooth
  teeth_counts = [cur_teeth]
  prev_step = 0
  for i in range(1, cog_count - 1):
    teeth_frac = min_tooth * np.power(np.e, a * (i-1))
    cur_step = min_tooth * a * np.power(np.e, a * i)
    cur_step = max(round(cur_step + teeth_frac - cur_teeth), prev_step)
    cur_teeth = cur_teeth + cur_step
    prev_step = cur_step
    teeth_counts.append(cur_teeth)
  
  teeth_counts.append(max_tooth)

  return teeth_counts

def get_cog_radius(teeth):
  half_angle_between_adjacent_teeth = np.pi / teeth
  return (link_length / 2) / math.sin(half_angle_between_adjacent_teeth)

def get_cassette_cog_radii(min_tooth, max_tooth, cog_count):
  return [get_cog_radius(teeth) for teeth in get_cassette_cog_teeth(min_tooth, max_tooth, cog_count)]

def get_straight_parallelogram_b_gap_mm(max_teeth):
  if max_teeth <= 20:
    # Lets assume the distance is closer since the jumps between gears is so small,
    # only 4 mm difference in radius between an 18 and 20 tooth cogs
    return 10
  elif max_teeth <= 42:
    # SRAM's guidance for their Road 1x derailleurs is good enough https://www.sram.com/en/service/models/rd-riv-b1
    return 15
  else: # teeth > 42
    # Using Shimano's guidance for CUES 10/11 speed https://si.shimano.com/en/cues/technical-assets-tips
    # SRAM's guidance for their Eagle derailleurs implies about 17 mm https://www.sram.com/en/service/models/rd-xx-1-b2
    return 19

def get_slant_parallelogram_b_gap_mm(max_teeth):
  if max_teeth <= 44:
    # SRAM's guidance for their Road 22 derailleurs is good enough.
    # Shimano says "as close as possible" https://www.sram.com/en/service/models/rd-riv-1-a2
    # Microshift Sword says 4-6 mm
    return 6
  else: # > 44 teeth
    # Shimano's guidance for CUES 10/11 speed is 9 mm https://si.shimano.com/en/cues/technical-assets-tips
    # Shimano's guidance for rd-5120 and similar is 8-9 mm for a 46 tooth cassette, or 6 for 42 tooth and below
    return 9

def get_b_gap_mm(max_teeth, parallelogram_style):
  if parallelogram_style == 'slant':
    return get_slant_parallelogram_b_gap_mm(max_teeth)
  elif parallelogram_style == 'straight':
    return get_straight_parallelogram_b_gap_mm(max_teeth)
  else:
    raise Exception("Unknown paralleogram style " + parallelogram_style)

def get_jockey_to_cog_distance_mm(teeth, b_gap):

  cog_radius = get_cog_radius(teeth)
  jockey_to_cog_distance = np.sqrt(2 * cog_radius * b_gap + b_gap * b_gap)

  return jockey_to_cog_distance

def get_jockey_to_cog_distance_list(min_tooth, max_tooth, cog_count, b_gap, links_from_jockey_to_smallest_cog):
  # Just use linear interpolation and assume that every derailleur tries to get the
  # jockey to the same distance from the 11-tooth cog
  # This is obviously true of slant-parallelogram derailleurs
  # I've done some modeling of 1x horizontal-parallelogram derailleurs and found that
  # they also move essentially linearly

  #largest_cog_jockey_to_cog_distance = get_jockey_to_cog_distance_mm(max_tooth, b_gap)
  #slope = (largest_cog_jockey_to_cog_distance - smallest_cog_jockey_to_cog_distance) / cog_count
  #dist_old = [smallest_cog_jockey_to_cog_distance + slope * i for i in range(cog_count)]

  cog_radii = get_cassette_cog_radii(min_tooth, max_tooth, cog_count)

  largest_cog_b_gap = b_gap
  largest_cog_to_jockey_edge_radius = largest_cog_b_gap + cog_radii[-1]

  min_jockey_to_cog_chain_length = links_from_jockey_to_smallest_cog * 25.4 / 2 
  smallest_cog_to_jockey_edge_radius = np.sqrt(
    np.pow(cog_radii[0], 2) + np.pow(min_jockey_to_cog_chain_length, 2))

  slope = (largest_cog_to_jockey_edge_radius - smallest_cog_to_jockey_edge_radius) / (cog_count - 1)

  jockey_edge_radii = [smallest_cog_to_jockey_edge_radius + slope * i for i in range(cog_count)]

  distances = np.sqrt([j * j - c * c for j, c in zip(jockey_edge_radii, cog_radii)])
  
  assert(not any(np.isnan(distances)))
  
  return distances

def convert_to_floats(data):
  # Convert to numbers
  for row in data:
    for key in row.keys():
      if len(row[key]) == 0:
        row[key] = np.nan
      else:
        try:
          row[key] = float(row[key])
        except:
          # Ignore failed conversion attempts
          pass

class RollerPositionInfo(BaseModel):
  prev_link_angle_rad: float
  roller_to_cog_distance: float
  roller_lateral_position: float
  can_calculate_next: bool = True

close_enough_roller_to_cog_distance = link_length * 0.1

def calculate_next_roller_position(roller_pos: RollerPositionInfo, cog_lateral_position):
  
  roller_to_cog_angle_rad = math.asin((cog_lateral_position - roller_pos.roller_lateral_position)/roller_pos.roller_to_cog_distance)

  next_link_min_angle_rad = roller_pos.prev_link_angle_rad - chain_max_free_yaw_rad
  next_link_max_angle_rad = roller_pos.prev_link_angle_rad + chain_max_free_yaw_rad

  next_link_angle_rad = min(next_link_max_angle_rad,
                            max(next_link_min_angle_rad, roller_to_cog_angle_rad))
  
  next_roller_to_cog_distance = roller_pos.roller_to_cog_distance \
    - link_length * math.cos(roller_to_cog_angle_rad - next_link_angle_rad)

  next_roller_lateral_position = roller_pos.roller_lateral_position \
    + link_length * math.sin(next_link_angle_rad)
  
  close_enough = next_roller_to_cog_distance <= close_enough_roller_to_cog_distance
  
  can_calculate_next = not close_enough \
                       and abs(cog_lateral_position - next_roller_lateral_position) \
                           <= roller_pos.roller_to_cog_distance

  return RollerPositionInfo(prev_link_angle_rad=next_link_angle_rad,
              roller_to_cog_distance=next_roller_to_cog_distance,
              roller_lateral_position=next_roller_lateral_position,
              can_calculate_next=can_calculate_next)

  

def calculate_max_chain_angle(shifter, derailleur, cassette):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])

  if "yawCoefficients" in derailleur:
    yaw_curve = np.polynomial.Polynomial(coef=derailleur["yawCoefficients"])
  else:
    yaw_curve = np.polynomial.Polynomial(coef=[0])
  
  shift_spacings = np.array(shifter["shiftSpacings"])
  cassette_pitches = cassette["pitches"]
  roller_cog_free_play = cassette["chainRollerWidth"] - cassette["cogWidth"]
  num_positions = min([cassette["speeds"], shifter["speeds"]])
  
  b_gap = derailleur["bGap"] if "bGap" in derailleur \
    else get_b_gap_mm(derailleur["maxTooth"], derailleur["parallelogramStyle"])
  links_from_jockey_to_smallest_cog = derailleur["linksFromJockeyToSmallestCog"] if "linksFromJockeyToSmallestCog" in derailleur\
    else default_links_from_jockey_to_smallest_cog
  jockey_to_cog_distances = get_jockey_to_cog_distance_list(11, derailleur["maxTooth"], num_positions, b_gap, links_from_jockey_to_smallest_cog)

  cog_positions = [smallest_cog_position + np.sum([cassette_pitches[0:i]])
                  for i in range(0, len(cassette_pitches) + 1) ]
  
  # Calculate barrel adjuster
  barrel_adjuster = 0
  barrel_adjuster_values = [barrel_adjuster]

  # Use Newton's method to find the barrel adjuster amount that will minimize chain angles
  for i in range(0, 12):
    cur_jockey_to_cog_distances = jockey_to_cog_distances[1:num_positions - 1]
    shift_positions = [barrel_adjuster + np.sum([shift_spacings[0:i]])
                      for i in range(0, len(shift_spacings) + 1) ]
    jockey_positions = derailleur_curve(shift_positions)
    cur_chain_roller_positions = jockey_positions[1:num_positions - 1]

    chain_roller_positions = []

    chain_at_cog_angles = [None] * (num_positions - 2)
    while any([d for d in cur_jockey_to_cog_distances if d > 0]):
      chain_roller_positions.append(cur_chain_roller_positions)
      diffs = cog_positions[1:num_positions - 1] - cur_chain_roller_positions

      diffs_minus_free_play = np.array([(
          0 if abs(d) < roller_cog_free_play/2
          else (
            d - roller_cog_free_play/2 if d > 0
            else d + roller_cog_free_play/2
          )
        )
        for d in diffs])

      chain_angles = np.arcsin(diffs_minus_free_play/cur_jockey_to_cog_distances) * 180 / np.pi
      
      jockey_angles = yaw_curve(shift_positions)[1:num_positions - 1]
      jockey_max_angles = jockey_angles + chain_max_free_yaw
      jockey_min_angles = jockey_angles - chain_max_free_yaw
      
      next_link_angles = np.min(
        [np.max(
          [chain_angles, jockey_min_angles],
          axis=0),
          jockey_max_angles], axis=0)
      next_link_angles_diff = chain_angles - next_link_angles

      next_roller_position_diffs = np.sin(np.pi * next_link_angles/180) * np.min([[link_length]*8, cur_jockey_to_cog_distances], axis=0)

      cur_chain_roller_positions = cur_chain_roller_positions + next_roller_position_diffs

      chain_at_cog_angles = [p if jcd < link_length else cca for p,jcd,cca
                             in zip(cur_chain_roller_positions, cur_jockey_to_cog_distances, chain_at_cog_angles)]

      cur_jockey_to_cog_distances = cur_jockey_to_cog_distances - link_length

    center_chain_angle = np.mean([chain_angles.min(), chain_angles.max()])

    if np.abs(center_chain_angle) <= 0.01:
      break

    center_diff = np.sin(center_chain_angle * np.pi / 180) * np.max(jockey_to_cog_distances)

    barrel_adjuster = barrel_adjuster + center_diff/derailleur["pullRatio"]
    barrel_adjuster_values.append(barrel_adjuster)

  # Review results
  if np.abs(center_chain_angle) > 0.01:
    raise Exception("Failed to converge")

  barrel_adjuster_too_low = barrel_adjuster < 0
    
  max_diff_minus_free_play = max(np.abs([diffs_minus_free_play.min(), diffs_minus_free_play.max()]))

  max_chain_angle = chain_angles.max()

  cable_pull_at_max_chain_angle = shift_positions[chain_angles.argmax() + 1]

  # Calculate end jockey positions based on second smallest or second biggest positions, plus the cog pitch
  # Yeah, this ignores the motion multiplier, but it shouldn't affect the pull too low or pull too high determinations
  least_pull = get_cable_pull_for_jockey_position(derailleur,
                                                  jockey_positions[1] - cassette_pitches[0])
  least_pull_too_low = least_pull < 0
  most_pull = get_cable_pull_for_jockey_position(derailleur,
                                                 jockey_positions[-2] + cassette_pitches[-1])
  most_pull_too_high = derailleur_curve(most_pull) > derailleur["physicalHighLimit"]
  most_pull_jockey_position_diff = derailleur["physicalHighLimit"] - derailleur_curve(most_pull)
  cassette_total_pitch = max(cog_positions) - min(cog_positions)
  derailleur_range_of_motion = derailleur["physicalHighLimit"] - derailleur["physicalLowLimit"]
  derailleur_can_clear_cassette = derailleur_range_of_motion * 1.03 > cassette_total_pitch

  return {
    "barrel_adjuster": barrel_adjuster,
    "barrel_adjuster_values": barrel_adjuster_values,
    "barrel_adjuster_too_low": bool(barrel_adjuster_too_low),
    "least_pull": least_pull,
    "least_pull_too_low": bool(least_pull_too_low),
    "most_pull": most_pull,
    "most_pull_too_high": bool(most_pull_too_high),
    "most_pull_jockey_position_diff": most_pull_jockey_position_diff,
    "cassette_total_pitch": cassette_total_pitch,
    "derailleur_range_of_motion": derailleur_range_of_motion,
    "derailleur_can_clear_cassette": bool(derailleur_can_clear_cassette),
    "diffs": diffs.tolist(),
    "diffs_minus_free_play": diffs_minus_free_play.tolist(),
    "max_diff_minus_free_play": float(max_diff_minus_free_play),
    "max_chain_angle": float(max_chain_angle),
    "cable_pull_at_max_chain_angle": cable_pull_at_max_chain_angle,
    "jockey_to_cog_links": [float(d) for d in jockey_to_cog_distances / 25.4 * 2],
    "chain_angles": chain_angles.tolist()
  }

def get_cable_pull_for_jockey_position(derailleur, jockey_position):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
  roots = (derailleur_curve - jockey_position).roots()

  valid_roots = [r for r in roots
                if r > 0 and r < max_cable_pull
                  and np.iscomplex(r) == False  # Don't consider complex results
                  # Commented out because this fails for SRAM GX 10-speed
                  #and derailleur_curve(r) <= derailleur["physicalHighLimit"]]
                ]
  
  # Return -1 since we flag negative values as invalid anyway
  if len(valid_roots) == 0:
    print(f"Warning: no valid cable pull values for jockey position {jockey_position} on {derailleur['partNumber']}.", roots)
    return -1
  
  # Just warn, and return the smallest valid root instead of throwing an error
  if len(valid_roots) > 1:
    print(f"Warning: too many cable pull values for jockey position {jockey_position} on {derailleur['partNumber']}.", valid_roots)

  return np.min(valid_roots)


class PullRatioInfo(BaseModel):
  dropout_width: float
  small_cog_offset: float
  small_cog_position: float
  smallest_cog_pull: float
  second_smallest_cog_pull: float
  second_biggest_cog_pull: float
  biggest_cog_pull: float
  biggest_cog_position: float
  total_pitch_inner_cogs: float
  pull_ratio: float
  coefficients: list[float]



def calc_pull_ratio(info, coefficients, max_pull = 100, design_cog_pitch = None, design_speeds = None):
  design_cog_pitch = design_cog_pitch or info["designCogPitch"]
  design_speeds = design_speeds or info["designSpeeds"]

  if "minDropoutWidth" in info and info["minDropoutWidth"] != None \
    and "maxDropoutWidth" in info and info["maxDropoutWidth"] != None:
    dropout_width = (info["minDropoutWidth"] + info["maxDropoutWidth"])/2
  else:
    dropout_width = 8
  small_cog_offset = info["smallCogOffset"] if "smallCogOffset" in info and info["smallCogOffset"] != None else 3
  small_cog_position = dropout_width + small_cog_offset
  biggest_cog_position = small_cog_position + design_cog_pitch * (design_speeds - 1)
  second_smallest_cog_position = design_cog_pitch + small_cog_position

  total_pitch_inner_cogs = design_cog_pitch * (design_speeds - 3)

  second_biggest_cog_position = second_smallest_cog_position + total_pitch_inner_cogs

  curve = np.polynomial.polynomial.Polynomial(coefficients)

  smallest_cog_pull = [r for r in (curve - small_cog_position).roots() if r >= 0][0]
  if smallest_cog_pull > max_pull:
    print(f"Warning: smallest_cog_pull {smallest_cog_pull} > max_pull {max_pull}", (curve - small_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)

  second_smallest_cog_pull = [r for r in (curve - second_smallest_cog_position).roots() if r >= 0][0]
  if second_smallest_cog_pull > max_pull:
    print(f"Warning: second_smallest_cog_pull {second_smallest_cog_pull} > max_pull {max_pull}", (curve - second_smallest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)
  
  second_biggest_cog_pull = [r for r in (curve - second_biggest_cog_position).roots() if r >= 0][0]
  if second_biggest_cog_pull > max_pull:
    print(f"Warning: second_biggest_cog_pull {second_biggest_cog_pull} > max_pull {max_pull}",(curve - second_biggest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)

  biggest_cog_pull = [r for r in (curve - biggest_cog_position).roots() if r >= 0][0]
  if biggest_cog_pull > max_pull:
    print(f"Warning: biggest_cog_pull {biggest_cog_pull} > max_pull {max_pull}",(curve - biggest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)
  

  pull_ratio = total_pitch_inner_cogs/(second_biggest_cog_pull - second_smallest_cog_pull)

  return PullRatioInfo(
    dropout_width=dropout_width,
    small_cog_offset=small_cog_offset,
    small_cog_position=small_cog_position,
    smallest_cog_pull=float(smallest_cog_pull),
    second_smallest_cog_pull=float(second_smallest_cog_pull),
    second_biggest_cog_pull=float(second_biggest_cog_pull),
    biggest_cog_pull=float(biggest_cog_pull),
    biggest_cog_position=biggest_cog_position,
    total_pitch_inner_cogs=total_pitch_inner_cogs,
    pull_ratio=float(pull_ratio),
    coefficients=[float(c) for c in curve.convert().coef]
    )

def get_jockey_offset_curve(yaw_angle_curve):

  def calc_yaw_offset_curve(x):
    y = yaw_angle_curve(x)

    if y < -chain_max_free_yaw:
      return math.sin((y + chain_max_free_yaw)/180*math.pi) * link_length
    elif y > chain_max_free_yaw:
      return math.sin((y - chain_max_free_yaw)/180*math.pi) * link_length
    else:
      return 0
  
  def yaw_offset_curve(x):
    if isinstance(x, Iterable):
      return np.array([calc_yaw_offset_curve(_x) for _x in x])
    else:
      return calc_yaw_offset_curve(x)

  return yaw_offset_curve

# Differentiate get_jockey_offset_curve() using chain rule
def get_jockey_offset_rate_curve(yaw_angle_curve):
  
  deriv = yaw_angle_curve.deriv()
  
  def calc_yaw_offset_rate_curve(x):
    y = yaw_angle_curve(x)

    if y < -chain_max_free_yaw:
      return math.cos((y + chain_max_free_yaw)/180*math.pi) * link_length * deriv(x) / 180 * math.pi
    elif y > chain_max_free_yaw:
      return math.cos((y - chain_max_free_yaw)/180*math.pi) * link_length * deriv(x) / 180 * math.pi
    else:
      return 0
  
  def yaw_offset_rate_curve(x):
    if isinstance(x, Iterable):
      return np.array([calc_yaw_offset_rate_curve(_x) for _x in x])
    else:
      return calc_yaw_offset_rate_curve(x)

  return yaw_offset_rate_curve

def get_combined_pull_curve(info):
  pull_curve = np.polynomial.polynomial.Polynomial(info["coefficients"])

  if "yawCoefficients" not in info:
    return pull_curve

  yaw_angle_curve = np.polynomial.polynomial.Polynomial(info["yawCoefficients"])
  jockey_offset_curve = get_jockey_offset_curve(yaw_angle_curve)

  def combined_pull_curve(x):
    if isinstance(x, Iterable):
      return np.array([pull_curve(_x) + jockey_offset_curve(_x) for _x in x])
    else:
      return pull_curve(x) + jockey_offset_curve(x)
  
  return combined_pull_curve

def get_combined_pull_ratio_curve(info):
  pull_curve = np.polynomial.polynomial.Polynomial(info["coefficients"])

  if "yawCoefficients" not in info:
    return pull_curve.deriv()

  yaw_angle_curve = np.polynomial.polynomial.Polynomial(info["yawCoefficients"])
  jockey_offset_rate_curve = get_jockey_offset_rate_curve(yaw_angle_curve)

  def combined_pull_ratio_curve(x):
    if isinstance(x, Iterable):
      return np.array([pull_curve(_x) + jockey_offset_rate_curve(_x) for _x in x])
    else:
      return pull_curve(x) + jockey_offset_rate_curve(x)
  
  return combined_pull_ratio_curve

if __name__ == '__main__':
  print()

  link_angle_rad = math.radians(-1.6)
  roller_lateral_position = 15.5
  roller_to_cog_distance = link_length * 3
  cog_lateral_position = 15

  print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

  roller_pos = RollerPositionInfo(prev_link_angle_rad=link_angle_rad,
                                    roller_lateral_position=roller_lateral_position,
                                    roller_to_cog_distance=roller_to_cog_distance)

  while roller_pos.can_calculate_next:
    roller_pos = calculate_next_roller_position(roller_pos, cog_lateral_position)
    print(roller_pos)
  
  print("Chain at cog angle", math.degrees(roller_pos.prev_link_angle_rad), "deg")

  print("Gen:", get_cassette_cog_teeth(11,34, 10), "\nAct:", [11, 13, 15, 17, 19, 21, 23, 26, 30, 34], "\n")
  print("Gen:", get_cassette_cog_teeth(11,34, 11), "\nAct:", [11, 13, 15, 17, 19, 21, 23, 25, 27, 30, 34], "\n")
  print("Gen:", get_cassette_cog_teeth(12,30, 10), "\nAct:", [12, 13, 14, 15, 17, 19, 21, 24, 27, 30], "\n")
  print("Gen:", get_cassette_cog_teeth(11,36, 10), "\nAct:", [11, 13, 15, 17, 19, 21, 24, 28, 32, 36], "\n")
  print("Gen:", get_cassette_cog_teeth(10,52, 12), "\nAct:", [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 52], "\n")
  print(get_jockey_to_cog_distance_list(11,39, 11, True, 3))

  print(get_cog_radius(11), 11 * (25.4 / 2) / (2 * np.pi))
  print(get_cog_radius(32), 32 * (25.4 / 2) / (2 * np.pi))
  print(get_cog_radius(52), 52 * (25.4 / 2) / (2 * np.pi))

  angles = calculate_max_chain_angle(
  {
    "brand": "Microshift",
    "name": "Advent X",
    "partNumber": "SB-M100A",
    "type": "drop-bar",
    "speeds": 10,
    "source": "https://youtu.be/FzP2hvDBTLs",
    "hasMatchingFrontShifters": False,
    "dataVideo": "https://youtu.be/JO-I4XVTsu4",
    "analysisVideo": "https://youtu.be/FzP2hvDBTLs",
    "shiftSpacings": [
      3.6966666666666668,
      3.4158333333333335,
      3.1622222222222223,
      3.3045833333333334,
      3.4354166666666663,
      3.3204166666666666,
      3.518333333333333,
      3.714166666666667,
      4.45
    ],
    "cablePull": 3.410138888888889,
    "analysisUrl": "https://boothinator.github.io/derailleur-analysis/shifters/Microshift Advent X/default.htm"
  },{
    "brand": "Microshift",
    "name": "Advent X",
    "partNumber": "RD-M6205AM",
    "designSpeeds": 10,
    "designCogPitch": 3.95,
    "distanceFromCarriageToJockeyWheel": 35.75,
    "jockeyWheelThickness": 2.2,
    "minDropoutWidth": 12,
    "maxDropoutWidth": 12,
    "smallCogOffset": None,
    "supportsMultipleFrontChainrings": True,
    "parallelogramStyle": "slant",
    "maxTooth": 44,
    "maxToothUnofficial": None,
    "maxToothWithGoatLink": None,
    "chainWrap": 35,
    #"linksFromJockeyToSmallestCog": 4,
    "pullRatio": 1.0547866001173967,
    "basePullRatio": 1.0480941756972713,
    "maxPull": 44.80833333333334,
    "coefficients": [
      10.63609527393101,
      0.8516019652813257,
      0.008326715295997324,
      -0.00010488856209232585
    ],
    "physicalLowLimit": 10.63609527393101,
    "physicalHighLimit": 56.076868483895375,
    "numberOfMeasurements": 577,
    "Base Pull Ratio Averaged Across Pulling Runs": "1.048 +/- 0.011",
    "Base Pull Ratio Averaged Across Relaxing Runs": "1.047 +/- 0.014",
    "Base Pull Ratio Averaged Across All Runs": "1.048 +/- 0.013",
    "Base Pull Ratio 95% Confidence Interval": "1.035 to 1.061",
    "meas_method_percent_diffs": [
      -0.08646779074792921,
      0.1503113592441492,
      -0.464396284829739,
      -0.17714791851195372,
      0.3050773589017227,
      -0.1530723813689206
    ],
    "Caliper vs Indicator percent difference": "Caliper vs Indicator percent difference: -0.07094927621877843 +/- 0.4922167734024139",
    "pullRatioCalc": {
      "dropout_width": 12.0,
      "small_cog_offset": 3.0,
      "small_cog_position": 15.0,
      "smallest_cog_pull": 4.903749371851818,
      "second_smallest_cog_pull": 9.052737563946664,
      "second_biggest_cog_pull": 35.433954673187,
      "biggest_cog_pull": 39.252946798054474,
      "biggest_cog_position": 50.550000000000004,
      "total_pitch_inner_cogs": 27.650000000000002,
      "pull_ratio": 1.0480941756972713,
      "coefficients": [
        10.63609527393101,
        0.8516019652813257,
        0.008326715295997324,
        -0.00010488856209232585
      ]
    },
    "yawCoefficients": [
      -4.121358373136494,
      0.2973675581670828,
      -0.006696452527693453,
      8.710513798395399e-05
    ],
    "yawNumberOfMeasurements": 141,
    "yawAffectsPullRatio": True,
    "analysisUrl": "https://boothinator.github.io/derailleur-analysis/derailleurs/Microshift RD-M6205AM/default.htm"
  },
  {
    "name": "Generic 10-Speed",
    "brand": "Generic",
    "partNumber": "generic-10-speed",
    "speeds": 10,
    "pitches": [ 3.95, 3.95, 3.95, 3.95, 3.95, 3.95, 3.95, 3.95, 3.95 ],
    "averagePitch": 3.95,
    "cogWidth": 1.65,
    "chainRollerWidth": 2.2,
    "maxToothAvailable": 48,
    "source": "https://en.wikibooks.org/wiki/Bicycles/Maintenance_and_Repair/Gear-changing_Dimensions#Cog-set_Stack_Width"
  })

  import json
  print(json.dumps(angles, indent=2))