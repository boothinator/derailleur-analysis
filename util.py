import numpy as np

# Could calculate using dropout thickness (7 to 8 mm for shimano?) and then use the distance from 
# end of cassette to dropout to figure out the first cog position, maybe
smallest_cog_position = 15 # TODO: put this on the cassette, or figure out from derailleur
jockey_to_cog_links = 2.5
jockey_to_cog_distance = jockey_to_cog_links * 25.4 / 2 
max_cable_pull = 50 # Assume that no shifter will be able to pull 50 mm of cable

def calculate_max_chain_angle(shifter, derailleur, cassette):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
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
      0 if abs(d) < roller_cog_free_play
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
