import numpy as np

roller_width = 2.2 # TODO: take this from the cassette, since cog spacing determines chain roller width
smallest_cog_position = 15 # TODO: put this on the cassette, or figure out from derailleur
jockey_to_cog_distance = 2.5 * 25.4 / 2 
max_cable_pull = 50 # Assume that no shifter will be able to pull 50 mm of cable

def calculate_max_chain_angle(shifter, derailleur, cassette):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
  shift_spacings = np.array(shifter["shiftSpacings"])
  cassette_pitches = cassette["pitches"]
  average_cog_pitch = np.mean(cassette_pitches)
  roller_cog_free_play = roller_width - cassette["cogWidth"]
  num_positions = min([cassette["speeds"], shifter["speeds"]])

  # Calculate barrel adjuster
  barrel_adjuster = 0
  barrel_adjuster_values = [barrel_adjuster]

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
  if np.abs(average_diff) > 0.01:
    raise Exception("Failed to converge")

  barrel_adjuster_too_low = barrel_adjuster < 0

  diffs_minus_free_play = np.array([(
      0 if abs(d) < roller_cog_free_play
      else (
        d - roller_cog_free_play/2 if d > 0
        else d + roller_cog_free_play/2
      )
    )
    for d in diffs])
  
  max_diff_minus_free_play = max(np.abs([diffs_minus_free_play.min(), diffs_minus_free_play.max()]))

  max_chain_angle = np.arcsin(max_diff_minus_free_play/jockey_to_cog_distance) * 180 / np.pi

  least_pull = get_cable_pull_for_jockey_position(derailleur,
                                                  jockey_positions[1] - average_cog_pitch)
  least_pull_too_low = least_pull < 0
  most_pull = get_cable_pull_for_jockey_position(derailleur,
                                                 jockey_positions[-2] + average_cog_pitch)
  most_pull_too_high = derailleur_curve(most_pull) > derailleur["physicalHighLimit"]

  return {
    "barrel_adjuster": barrel_adjuster,
    "barrel_adjuster_values": barrel_adjuster_values,
    "barrel_adjuster_too_low": bool(barrel_adjuster_too_low),
    "least_pull": least_pull,
    "least_pull_too_low": bool(least_pull_too_low),
    "most_pull": most_pull,
    "most_pull_too_high": bool(most_pull_too_high),
    "diffs": diffs.tolist(),
    "diffs_minus_free_play": diffs_minus_free_play.tolist(),
    "max_chain_angle": max_chain_angle
  }

def derailleur_can_clear_cassette(derailleur, cassette):
  
  derailleur_range = derailleur["physicalHighLimit"] - derailleur["physicalLowLimit"]
  cassette_total_pitch = np.sum(cassette["pitches"])

  return {
    "derailleur_range": derailleur_range,
    "cassette_total_pitch": cassette_total_pitch,
    "can_clear": cassette_total_pitch > (derailleur_range * 1.02)
  }

def get_cable_pull_for_jockey_position(derailleur, jockey_position):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
  roots = (derailleur_curve - jockey_position).roots()

  valid_roots = [r for r in roots
                if r > 0 and r < max_cable_pull
                  and np.iscomplex(r) == False  # Don't consider complex results
                  #and derailleur_curve(r) <= derailleur["physicalHighLimit"]]
                ]
  
  if len(valid_roots) == 0:
    print(f"Warning: no valid cable pull values for jockey position {jockey_position} on {derailleur['partNumber']}.", roots)
    return -1
  
  if len(valid_roots) > 1:
    print(f"Warning: too many cable pull values for jockey position {jockey_position} on {derailleur['partNumber']}.", valid_roots)

  return np.min(valid_roots)
