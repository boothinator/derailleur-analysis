import numpy as np
from pydantic import BaseModel
from typing import Iterable
import math

# Could calculate using dropout thickness (7 to 8 mm for shimano?) and then use the distance from 
# end of cassette to dropout to figure out the first cog position, maybe
smallest_cog_position = 15 # TODO: put this on the cassette, or figure out from derailleur
jockey_to_cog_links = 2.5
jockey_to_cog_distance = jockey_to_cog_links * 25.4 / 2 
max_cable_pull = 50 # Assume that no shifter will be able to pull 50 mm of cable
chain_max_free_yaw = 1.3
link_length = 12.7

def calculate_max_chain_angle(shifter, derailleur, cassette):
  derailleur_curve = get_combined_pull_curve(derailleur)
  shift_spacings = np.array(shifter["shiftSpacings"])
  cassette_pitches = cassette["pitches"]
  roller_cog_free_play = cassette["chainRollerWidth"] - cassette["cogWidth"]
  num_positions = min([cassette["speeds"], shifter["speeds"]])

  # Calculate barrel adjuster
  barrel_adjuster = 0
  barrel_adjuster_values = [barrel_adjuster]

  # Use Newton's method to find the barrel adjuster amount that will minimize distance
  # from jockey to cog for all shifts
  for i in range(0, 5):
    shift_positions = [barrel_adjuster + np.sum([shift_spacings[0:i]])
                      for i in range(0, len(shift_spacings) + 1) ]
    jockey_positions = derailleur_curve(shift_positions)
    cog_positions = [smallest_cog_position + np.sum([cassette_pitches[0:i]])
                    for i in range(0, len(cassette_pitches) + 1) ]
    
    diffs = cog_positions[1:num_positions - 1] - jockey_positions[1:num_positions - 1]
    
    average_diff = np.mean([diffs.min(), diffs.max()])

    barrel_adjuster = barrel_adjuster + average_diff/derailleur["pullRatio"]
    barrel_adjuster_values.append(barrel_adjuster)

  # Review results
  if np.abs(average_diff) > 0.1:
    raise Exception("Failed to converge")

  barrel_adjuster_too_low = barrel_adjuster < 0

  diffs_minus_free_play = np.array([(
      0 if abs(d) < roller_cog_free_play/2
      else (
        d - roller_cog_free_play/2 if d > 0
        else d + roller_cog_free_play/2
      )
    )
    for d in diffs])
  
  max_diff_minus_free_play = max(np.abs([diffs_minus_free_play.min(), diffs_minus_free_play.max()]))

  chain_angles = np.arcsin(diffs_minus_free_play/jockey_to_cog_distance) * 180 / np.pi

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
    "jockey_to_cog_links": jockey_to_cog_links,
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


def calc_pull_ratio(info, coefficients, max_pull):
  if "minDropoutWidth" in info and info["minDropoutWidth"] != None \
    and "maxDropoutWidth" in info and info["maxDropoutWidth"] != None:
    dropout_width = (info["minDropoutWidth"] + info["maxDropoutWidth"])/2
  else:
    dropout_width = 8
  small_cog_offset = info["smallCogOffset"] if "smallCogOffset" in info and info["smallCogOffset"] != None else 3
  small_cog_position = dropout_width + small_cog_offset
  biggest_cog_position = small_cog_position + info["designCogPitch"] * (info["designSpeeds"] - 1)
  second_smallest_cog_position = info["designCogPitch"] + small_cog_position

  total_pitch_inner_cogs = info["designCogPitch"] * (info["designSpeeds"] - 3)

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