import numpy as np

# Could calculate using dropout thickness (7 to 8 mm for shimano?) and then use the distance from 
# end of cassette to dropout to figure out the first cog position, maybe
smallest_cog_position = 15 # TODO: put this on the cassette, or figure out from derailleur
jockey_to_cog_links = 2.5
jockey_to_cog_distance = jockey_to_cog_links * 25.4 / 2 
smallest_cog_jockey_to_cog_links = 3
smallest_cog_jockey_to_cog_distance = smallest_cog_jockey_to_cog_links * 25.4 / 2 
max_cable_pull = 50 # Assume that no shifter will be able to pull 50 mm of cable

def get_cassette_cog_teeth(min_tooth, max_tooth, cog_count):
  min_tooth_x = np.log(min_tooth)
  max_tooth_x = np.log(max_tooth)

  a = (max_tooth_x - min_tooth_x) / (cog_count - 1)

  #teeth_diffs = [round(min_tooth * a * np.power(np.e, a * i))
  #                for i in range(cog_count - 1)]
  #teeth_counts = [min_tooth + sum(teeth_diffs[0:i]) for i in range(cog_count)]

  teeth_counts = [round(min_tooth * np.power(np.e, a * i))
                  for i in range(cog_count)]

  # FIXME: this gives weird teeth amounts

  return teeth_counts

def get_1x_b_gap_mm(teeth):
  if teeth <= 20:
    # Lets assume the distance is closer since the jumps between gears is so small,
    # only 4 mm difference in radius between an 18 and 20 tooth cogs
    return 10
  elif teeth <= 42:
    # SRAM's guidance for their Road 1x derailleurs is good enough https://www.sram.com/en/service/models/rd-riv-b1
    return 15
  else: # teeth > 42
    # Using Shimano's guidance for CUES 10/11 speed https://si.shimano.com/en/cues/technical-assets-tips
    # SRAM's guidance for their Eagle derailleurs implies about 17 mm https://www.sram.com/en/service/models/rd-xx-1-b2
    return 19

def get_2x_b_gap_mm():
  # SRAM's guidance for their Road 22 derailleurs is good enough.
  # Shimano says "as close as possible" https://www.sram.com/en/service/models/rd-riv-1-a2
  # Microshift Sword says 4-6 mm
  return 6

def get_b_gap_mm(teeth, supports_multiple_front_chainrings):
  if supports_multiple_front_chainrings:
    return get_2x_b_gap_mm()
  else:
    return get_1x_b_gap_mm(teeth)

def get_jockey_to_cog_distance_mm(teeth, supports_multiple_front_chainrings):
  # FIXME: Hmm, I think I need to calculate a gap for all cogs based on the b-gap
  b_gap = get_b_gap_mm(teeth, supports_multiple_front_chainrings)
  cog_radius = teeth * (25.4 / 2) / (2 * np.pi)
  jockey_to_cog_distance = np.sqrt(2 * cog_radius * b_gap + b_gap * b_gap)

  # FIXME: really should consider horizonal cage vs slant-parallelogram design differently
  # Horizontal cage - model rotation of jockey wheel axle
  # Slant-parallelogram - completely flat

  return jockey_to_cog_distance

def get_jockey_to_cog_distance_list(min_tooth, max_tooth, cog_count, supports_multiple_front_chainrings):
  # Just use linear interpolation and assume that every derailleur tries to get the jockey to the same distance from the 11-tooth cog

  largest_cog_jockey_to_cog_distance = get_jockey_to_cog_distance_mm(max_tooth, supports_multiple_front_chainrings)
  slope = (largest_cog_jockey_to_cog_distance - smallest_cog_jockey_to_cog_distance) / cog_count

  return [smallest_cog_jockey_to_cog_distance + slope * i for i in range(cog_count)]

def calculate_max_chain_angle(shifter, derailleur, cassette):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
  shift_spacings = np.array(shifter["shiftSpacings"])
  cassette_pitches = cassette["pitches"]
  roller_cog_free_play = cassette["chainRollerWidth"] - cassette["cogWidth"]
  num_positions = min([cassette["speeds"], shifter["speeds"]])
  jockey_to_cog_distances = get_jockey_to_cog_distance_list(11, derailleur["maxTooth"], num_positions, derailleur["supportsMultipleFrontChainrings"])

  # Calculate barrel adjuster
  barrel_adjuster = 0
  barrel_adjuster_values = [barrel_adjuster]

  # Use Newton's method to find the barrel adjuster amount that will minimize chain angles
  for i in range(0, 12):
    shift_positions = [barrel_adjuster + np.sum([shift_spacings[0:i]])
                      for i in range(0, len(shift_spacings) + 1) ]
    jockey_positions = derailleur_curve(shift_positions)
    cog_positions = [smallest_cog_position + np.sum([cassette_pitches[0:i]])
                    for i in range(0, len(cassette_pitches) + 1) ]
    
    diffs = cog_positions[1:num_positions - 1] - jockey_positions[1:num_positions - 1]

    diffs_minus_free_play = np.array([(
        0 if abs(d) < roller_cog_free_play/2
        else (
          d - roller_cog_free_play/2 if d > 0
          else d + roller_cog_free_play/2
        )
      )
      for d in diffs])

    chain_angles = np.arcsin(diffs_minus_free_play/jockey_to_cog_distances[1:num_positions - 1]) * 180 / np.pi
    
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
    "jockey_to_cog_links": jockey_to_cog_links, # FIXME: replace with actually used info
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

if __name__ == '__main__':
  print(get_cassette_cog_teeth(11,34, 11))
  print(get_jockey_to_cog_distance_list(11,39, 11, True))

  angles = calculate_max_chain_angle(  {
    "brand": "Shimano",
    "name": "CUES",
    "partNumber": "SL-U6000-10R",
    "type": "flat-bar",
    "speeds": 10,
    "source": "https://youtu.be/_Q_7C2ZrstI",
    "hasMatchingFrontShifters": True,
    "dataVideo": "https://www.youtube.com/watch?v=2-9jvMvxr_M",
    "analysisVideo": "https://youtu.be/_Q_7C2ZrstI",
    "shiftSpacings": [
      4.821666666666666,
      3.700833333333333,
      3.6077777777777778,
      3.4862500000000005,
      3.541666666666666,
      3.575416666666667,
      3.585,
      3.5675000000000003,
      3.6183333333333336
    ],
    "cablePull": 3.5806349206349206,
    "analysisUrl": "https://boothinator.github.io/derailleur-analysis/shifters/Shimano CUES 10-Speed/default.htm"
  },  {
    "brand": "Shimano",
    "name": "CUES",
    "partNumber": "RD-U6020-10",
    "designSpeeds": 10,
    "designCogPitch": 4.05,
    "distanceFromCarriageToJockeyWheel": 34.93,
    "jockeyWheelThickness": 2.2,
    "minDropoutWidth": None,
    "maxDropoutWidth": None,
    "smallCogOffset": None,
    "supportsMultipleFrontChainrings": True,
    "chain": "10-speed",
    "maxTooth": 39,
    "chainWrap": 44,
    "dataVideo": "https://youtu.be/I-ctFLBjlZ0",
    "analysisVideo": "https://youtu.be/anIPVxXD7Lg",
    "pullRatio": 1.0582142182810916,
    "coefficients": [
      8.034542372275181,
      0.9792098840753652,
      0.005067028992561139,
      -8.948602873125939e-05
    ],
    "physicalLowLimit": 8.034542372275181,
    "physicalHighLimit": 50.871216961370294,
    "numberOfMeasurements": 652,
    "Pull Ratio Averaged Across Pulling Runs": "1.062 +/- 0.005",
    "Pull Ratio Averaged Across Relaxing Runs": "1.054 +/- 0.018",
    "Pull Ratio Averaged Across All Runs": "1.058 +/- 0.015",
    "Pull Ratio 95% Confidence Interval": "1.043 to 1.074",
    "analysisUrl": "https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano CUES 10-Speed/default.htm",
    "meas_method_percent_diffs": [
      0.047835446065542034,
      -0.6227544910179423,
      -0.14350633819659214,
      -1.2163129024564703,
      -0.47732696897371996,
      1.711738703348832e-14
    ],
    "Caliper vs Indicator percent difference": "Caliper vs Indicator percent difference: -0.4020108757631942 +/- 0.8749427035283623"
  },  {
    "name": "LinkGlide 10-Speed",
    "brand": "Shimano",
    "partNumber": "CS-LG300-10",
    "speeds": 10,
    "pitches": [
      4.05,
      4.0,
      4.1,
      4.05,
      4.05,
      4.1,
      4.0,
      4.05,
      4.15
    ],
    "averagePitch": 4.05,
    "cogWidth": 1.95,
    "chainRollerWidth": 2.2,
    "minMaxToothAvailable": 39,
    "maxToothAvailable": 48,
    "source": "https://www.youtube.com/watch?v=KNserH4_hL8"
  })

  import json
  print(json.dumps(angles, indent=2))