import numpy as np
from pydantic import BaseModel
from typing import Iterable
import math
import drawsvg as draw

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
  chain_length_from_roller_to_cog: float
  roller_lateral_position: float

def calculate_next_roller_position(roller_pos: RollerPositionInfo, cog_lateral_position: float) -> RollerPositionInfo:

  roller_to_cog_angle_rad = math.asin(
    max(
      min(((cog_lateral_position - roller_pos.roller_lateral_position)
         /max(roller_pos.chain_length_from_roller_to_cog, link_length)),
         1),
      -1))

  next_link_min_angle_rad = roller_pos.prev_link_angle_rad - chain_max_free_yaw_rad
  next_link_max_angle_rad = roller_pos.prev_link_angle_rad + chain_max_free_yaw_rad

  next_link_angle_rad = min(next_link_max_angle_rad,
                            max(next_link_min_angle_rad, roller_to_cog_angle_rad))
  
  next_chain_length_from_roller_to_cog = roller_pos.chain_length_from_roller_to_cog - link_length * math.cos(next_link_angle_rad)

  next_roller_lateral_position = roller_pos.roller_lateral_position \
    + link_length * math.sin(next_link_angle_rad)

  return RollerPositionInfo(prev_link_angle_rad=next_link_angle_rad,
              chain_length_from_roller_to_cog=next_chain_length_from_roller_to_cog,
              roller_lateral_position=next_roller_lateral_position)

class ChainAngleAtCogResult(BaseModel):
  roller_pos_list: list[RollerPositionInfo]
  angle_deg: float
  chain_to_cog_lateral_distance_at_axle: float

def calculate_chain_angle_at_cog(jockey_angle_rad: float, jockey_to_cog_distance: float,
                                 jockey_lateral_position: float, cog_lateral_position: float,
                                 free_play_between_cog_and_chain: float) -> ChainAngleAtCogResult:
  
  assert(jockey_to_cog_distance > 0)

  # TODO: Maybe this value should be rounded by the nearest number of links, since if it's slightly bigger
  # than n + half a link, then it the nth link won't touch, and if it's slightly smaller,
  # the nth link will definitely touch
  # Actually, maybe I should track when the tooth in front of the touch point starts going
  # through the link

  roller_pos_list = [RollerPositionInfo(prev_link_angle_rad=jockey_angle_rad,
                                    roller_lateral_position=jockey_lateral_position,
                                    chain_length_from_roller_to_cog=jockey_to_cog_distance)]

  last_pos = None

  while roller_pos_list[-1].chain_length_from_roller_to_cog > -link_length:
    roller_pos_list.append(
      calculate_next_roller_position(roller_pos_list[-1], cog_lateral_position))

    if not last_pos and roller_pos_list[-1].chain_length_from_roller_to_cog <= 0:
      last_pos = roller_pos_list[-1]

  chain_position_at_axle = roller_pos_list[-2].roller_lateral_position \
    + math.sin(last_pos.prev_link_angle_rad) * roller_pos_list[-2].chain_length_from_roller_to_cog

  lateral_position_diff = cog_lateral_position - chain_position_at_axle

  if lateral_position_diff < -free_play_between_cog_and_chain:
    chain_to_cog_lateral_distance_at_axle = lateral_position_diff - free_play_between_cog_and_chain
  elif lateral_position_diff > free_play_between_cog_and_chain:
    chain_to_cog_lateral_distance_at_axle = lateral_position_diff + free_play_between_cog_and_chain
  else:
    chain_to_cog_lateral_distance_at_axle = 0
  
  return ChainAngleAtCogResult(roller_pos_list=roller_pos_list,
                               angle_deg=math.degrees(last_pos.prev_link_angle_rad),
                               chain_to_cog_lateral_distance_at_axle=chain_to_cog_lateral_distance_at_axle)


def render_rollers(rollers: list[RollerPositionInfo], chain_to_cog_lateral_distance_at_axle: float,
                   start_y = None, **kwargs):
  g = draw.Group(**kwargs)

  link_scale = 7

  link_pixels = link_scale * link_length
  inner_link_width_pixels = 20
  outer_link_width_pixels = 30

  angle_scale = 4

  prev_roller_x = 400 - rollers[0].chain_length_from_roller_to_cog * link_scale
  prev_roller_y = 0
  offset_y = 50
  roller_diameter_pixels = 10
  roller_width_pixels = 10

  cog_width_pixels = 6

  min_roller_y = prev_roller_y

  roller_coords = []
  render_cog = False
  for i,r in enumerate(rollers):
    
    scaled_angle = angle_scale * r.prev_link_angle_rad
    
    cur_roller_x = prev_roller_x + link_pixels * math.cos(scaled_angle)
    cur_roller_y = prev_roller_y + link_pixels * math.sin(scaled_angle)

    if not render_cog and r.chain_length_from_roller_to_cog < link_length:
      render_cog = True

      if chain_to_cog_lateral_distance_at_axle > 0:
        cog_y = cur_roller_y + 20
      elif chain_to_cog_lateral_distance_at_axle < 0:
        cog_y = cur_roller_y - 20
      else:
        cog_y = cur_roller_y + link_scale * r.chain_length_from_roller_to_cog * math.sin(angle_scale * r.prev_link_angle_rad)

      if r.chain_length_from_roller_to_cog > 0:
        cog_contact_line_x = cur_roller_x + link_scale * r.chain_length_from_roller_to_cog * math.cos(angle_scale * r.prev_link_angle_rad)
        cog_contact_line_y = cur_roller_y + link_scale * r.chain_length_from_roller_to_cog * math.sin(angle_scale * r.prev_link_angle_rad)


    roller_coords.append((prev_roller_x, prev_roller_y, cur_roller_x, cur_roller_y, scaled_angle, render_cog))

    prev_roller_x = cur_roller_x
    prev_roller_y = cur_roller_y

    min_roller_y = min(cur_roller_y, min_roller_y)

  if start_y:
    offset_y = start_y - roller_coords[-1][3]
  else:
    offset_y = offset_y - min_roller_y

  roller_coords = [(px, py + offset_y, x, y + offset_y, angle, rc) for px, py, x, y, angle, rc in roller_coords]

  # Draw jockey contact line
  g.append(draw.Line(roller_coords[0][2],roller_coords[0][3] - 20, roller_coords[0][2],roller_coords[0][3] + 20, stroke="red", stroke_width="2px"))

  # Draw cog contact line
  g.append(draw.Line(cog_contact_line_x,cog_contact_line_y + offset_y - 20, cog_contact_line_x,cog_contact_line_y + offset_y + 20, stroke="red", stroke_width="2px"))

  chain_group = draw.Group(fill="black", stroke="black", stroke_width="2px")
  roller_group = draw.Group(fill="black", stroke="black", stroke_width="2px")

  for i,(prev_roller_x, prev_roller_y, cur_roller_x, cur_roller_y, link_angle, render_cog) \
      in enumerate(roller_coords):

    if i % 2 == 0:
      link_width = inner_link_width_pixels
    else:
      link_width = outer_link_width_pixels

    # Render roller
    rg = draw.Group(transform=f"rotate({math.degrees(link_angle)}, {prev_roller_x}, {prev_roller_y})")
    rg.append(draw.Rectangle(prev_roller_x - roller_diameter_pixels/2, prev_roller_y - roller_width_pixels/2,
                             roller_diameter_pixels, roller_width_pixels))
    chain_group.append(rg)

    if i < len(roller_coords) - 1:
      # Render link
      lg = draw.Group(transform=f"rotate({math.degrees(link_angle)}, {prev_roller_x}, {prev_roller_y})")
      lg.append(draw.Line(prev_roller_x - roller_diameter_pixels/2, prev_roller_y - link_width/2, cur_roller_x + roller_diameter_pixels/2, prev_roller_y - link_width/2))
      lg.append(draw.Line(prev_roller_x - roller_diameter_pixels/2, prev_roller_y + link_width/2, cur_roller_x + roller_diameter_pixels/2, prev_roller_y + link_width/2))
      roller_group.append(lg)
      
      if render_cog:
        # TODO: Start rendering the cog teeth here if the chain length from roller to cog is less than the link length
        g.append(draw.Circle(prev_roller_x + link_pixels/2, cog_y + offset_y, cog_width_pixels, fill="blue"))

  g.append(chain_group)
  g.append(roller_group)

  jockey_group = draw.Group(fill="green")
  jockey_tooth_delta_x = (roller_coords[0][2] - roller_coords[0][0])/2
  jockey_tooth_delta_y = (roller_coords[0][3] - roller_coords[0][1])/2
  first_jockey_tooth_x = roller_coords[0][0] + jockey_tooth_delta_x
  first_jockey_tooth_y = roller_coords[0][1] + jockey_tooth_delta_y
  second_jockey_tooth_x = roller_coords[0][2] + jockey_tooth_delta_x
  second_jockey_tooth_y = roller_coords[0][3] + jockey_tooth_delta_y
  jockey_group.append(draw.Circle(first_jockey_tooth_x, first_jockey_tooth_y, roller_width_pixels))
  jockey_group.append(draw.Circle(second_jockey_tooth_x, second_jockey_tooth_y, roller_width_pixels))
  g.append(jockey_group)

  # These circles represent teeth now, not lands
  #g.append(draw.Circle(roller_coords[][2] - link_pixels/2, (roller_coords[0][3] + roller_coords[1][3])/2, 10, fill="green"))
  #g.append(draw.Circle(roller_coords[2][2] - link_pixels/2, (roller_coords[1][3] + roller_coords[2][3])/2, 10, fill="green"))
  
  return g

def calculate_max_chain_angle(shifter, derailleur, cassette):
  # TODO: account for interference with adjacent cogs
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
  
  # Calculate initial barrel adjuster
  candidate_barrel_adjuster_values = (derailleur_curve - cog_positions[0]).roots()
  valid_initial_barrel_adjuster_values = [r for r in candidate_barrel_adjuster_values
                                          if r >= 0 and r < max_cable_pull]
  if valid_initial_barrel_adjuster_values:
    barrel_adjuster = np.min(valid_initial_barrel_adjuster_values)
  else:
    barrel_adjuster = 0
  
  barrel_adjuster_values = [barrel_adjuster]

  # Use Newton's method to find the barrel adjuster amount that will minimize chain angles
  for i in range(0, 12):
    shift_positions = [barrel_adjuster + np.sum([shift_spacings[0:i]])
                      for i in range(0, len(shift_spacings) + 1) ]
    jockey_lateral_positions = derailleur_curve(shift_positions)

    # chain_angles = np.arcsin(diffs_minus_free_play/jockey_to_cog_distances[1:num_positions - 1]) * 180 / np.pi

    jockey_yaw_angles_rad = np.deg2rad(yaw_curve(shift_positions))

    chain_angle_results = [calculate_chain_angle_at_cog(jockey_angle_rad, jockey_to_cog_distance,
                              jockey_lateral_position, cog_lateral_position, roller_cog_free_play)
                           for jockey_angle_rad, jockey_to_cog_distance,
                              jockey_lateral_position, cog_lateral_position
                           in zip(jockey_yaw_angles_rad, jockey_to_cog_distances,
                                  jockey_lateral_positions, cog_positions)]

    chain_angles = np.array([r.angle_deg for r in chain_angle_results])

    chain_angles_excluding_first_and_last = chain_angles[1:-1]
    
    center_chain_angle = np.mean([chain_angles_excluding_first_and_last.min(), chain_angles_excluding_first_and_last.max()])

    if np.abs(center_chain_angle) <= 0.01:
      break
    
    if i > 15:
      mult = 0.001
    elif i > 10:
      mult = 0.01
    elif i > 5:
      mult = 0.1
    else:
      mult = 1

    center_diff = np.sin(center_chain_angle * np.pi / 180) * np.max(jockey_to_cog_distances)

    barrel_adjuster = barrel_adjuster + mult * center_diff/derailleur["pullRatio"]
    barrel_adjuster_values.append(barrel_adjuster)

  # Review results
  failed_to_converge = np.abs(center_chain_angle) > 0.1
  if failed_to_converge:
    print("Failed to converge", shifter["name"], derailleur["name"], cassette["name"])


  barrel_adjuster_too_low = barrel_adjuster < 0
    
  diffs = cog_positions[1:num_positions - 1] - jockey_lateral_positions[1:num_positions - 1]

  diffs_minus_free_play = np.array([(
      0 if abs(d) < roller_cog_free_play/2
      else (
        d - roller_cog_free_play/2 if d > 0
        else d + roller_cog_free_play/2
      )
    )
    for d in diffs])
    
  max_diff_minus_free_play = max(np.abs([diffs_minus_free_play.min(), diffs_minus_free_play.max()]))

  max_chain_angle = chain_angles_excluding_first_and_last.max()

  cable_pull_at_max_chain_angle = shift_positions[chain_angles_excluding_first_and_last.argmax() + 1]

  # Calculate end jockey positions based on second smallest or second biggest positions, plus the cog pitch
  # Yeah, this ignores the motion multiplier, but it shouldn't affect the pull too low or pull too high determinations
  least_pull = get_cable_pull_for_jockey_position(derailleur,
                                                  jockey_lateral_positions[1] - cassette_pitches[0])
  least_pull_too_low = least_pull < 0
  most_pull = get_cable_pull_for_jockey_position(derailleur,
                                                 jockey_lateral_positions[-2] + cassette_pitches[-1])
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
    "failed_to_converge": bool(failed_to_converge),
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
    "chain_angles": chain_angles.tolist(),
    "chain_angle_results": chain_angle_results
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

  link_angle_rad = math.radians(-1.5)
  roller_lateral_position = 16
  roller_to_cog_distance = link_length * 3
  cog_lateral_position = 15
  free_play_between_cog_and_chain = 2.2 - 1.65
  positions = []

  print(math.degrees(math.asin((cog_lateral_position - roller_lateral_position)/roller_to_cog_distance)), "deg")

  roller_pos = RollerPositionInfo(prev_link_angle_rad=link_angle_rad,
                                    roller_lateral_position=roller_lateral_position,
                                    chain_length_from_roller_to_cog=roller_to_cog_distance)

  #positions.append(roller_pos)
  
  #while roller_pos.can_calculate_next:
  #  roller_pos = calculate_next_roller_position(roller_pos, cog_lateral_position)
  #  print(roller_pos)
  #  positions.append(roller_pos)
  
  #print("Chain at cog angle", math.degrees(roller_pos.prev_link_angle_rad), "deg")

  result = calculate_chain_angle_at_cog(link_angle_rad, roller_to_cog_distance, roller_lateral_position,
                               cog_lateral_position, free_play_between_cog_and_chain)
  
  positions=result.roller_pos_list

  d = draw.Drawing(600, 600)
  d.append(render_rollers(positions, result.chain_to_cog_lateral_distance_at_axle ))
  d.save_svg("test.svg")

  print("Gen:", get_cassette_cog_teeth(11,34, 10), "\nAct:", [11, 13, 15, 17, 19, 21, 23, 26, 30, 34], "\n")
  print("Gen:", get_cassette_cog_teeth(11,34, 11), "\nAct:", [11, 13, 15, 17, 19, 21, 23, 25, 27, 30, 34], "\n")
  print("Gen:", get_cassette_cog_teeth(12,30, 10), "\nAct:", [12, 13, 14, 15, 17, 19, 21, 24, 27, 30], "\n")
  print("Gen:", get_cassette_cog_teeth(11,36, 10), "\nAct:", [11, 13, 15, 17, 19, 21, 24, 28, 32, 36], "\n")
  print("Gen:", get_cassette_cog_teeth(10,52, 12), "\nAct:", [10, 12, 14, 16, 18, 21, 24, 28, 32, 36, 42, 52], "\n")
  print(get_jockey_to_cog_distance_list(11,39, 11, True, 3))

  print(get_cog_radius(11), 11 * (25.4 / 2) / (2 * np.pi))
  print(get_cog_radius(32), 32 * (25.4 / 2) / (2 * np.pi))
  print(get_cog_radius(52), 52 * (25.4 / 2) / (2 * np.pi))

  import json
  
  with open(f"all_shifters.json") as f:
    shifters = json.load(f)
  with open(f"all_derailleurs.json") as f:
    derailleurs = json.load(f)
  with open(f"cassettes.json") as f:
    cassettes = json.load(f)

  angles = calculate_max_chain_angle([s for s in shifters if s["partNumber"] == "SB-M100A"][0],
                                     [d for d in derailleurs if d["partNumber"] == "RD-M6205AM"][0],
                                     [c for c in cassettes if c["partNumber"] == "generic-10-speed"][0])

  #print(json.dumps(angles, indent=2, default=lambda _: "skipped"))

  # TODO: Update render_rollers to put teeth at correct distance for size of cog

  d = draw.Drawing(1000, 1200)
  for i,r in enumerate(angles["chain_angle_results"]):
    d.append(render_rollers(r.roller_pos_list, r.chain_to_cog_lateral_distance_at_axle,
                            start_y=i*100 + 100))
  d.save_svg("test2.svg")

  

  angles = calculate_max_chain_angle([s for s in shifters if s["partNumber"] == "SL-U6000-10R"][0],
                                     [d for d in derailleurs if d["partNumber"] == "RD-U6020-10"][0],
                                     [c for c in cassettes if c["partNumber"] == "CS-LG300-10"][0])

  d = draw.Drawing(1000, 1200)
  for i,r in enumerate(angles["chain_angle_results"]):
    d.append(render_rollers(r.roller_pos_list, r.chain_to_cog_lateral_distance_at_axle,
                            start_y=i*100 + 100))
  d.save_svg("test3.svg")

  angles = calculate_max_chain_angle([s for s in shifters if s["partNumber"] == "SL-M5100"][0],
                                     [d for d in derailleurs if d["partNumber"] == "RD-M5120"][0],
                                     [c for c in cassettes if c["partNumber"] == "shimano-11-speed"][0])

  d = draw.Drawing(1000, 1200)
  for i,r in enumerate(angles["chain_angle_results"]):
    d.append(render_rollers(r.roller_pos_list, r.chain_to_cog_lateral_distance_at_axle,
                            start_y=i*100 + 100))
  d.save_svg("test4.svg")