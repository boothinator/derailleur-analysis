import numpy as np

roller_width = 2.2
smallest_cog_position = 15
jockey_to_cog_distance = 2.5 * 25.4 / 2

def calculate_max_angle(shifter, derailleur, cassette):
  derailleur_curve = np.polynomial.Polynomial(coef=derailleur["coefficients"])
  shift_spacings = np.array(shifter["shiftSpacings"])
  derailleur_range = derailleur["physicalHighLimit"] - derailleur["physicalLowLimit"]
  cassette_pitches = cassette["pitches"]
  cassette_total_pitch = np.sum(cassette_pitches)
  roller_cog_free_play = roller_width - cassette["cogWidth"]
  num_positions = min([cassette["speeds"], shifter["speeds"]])

  if cassette_total_pitch > derailleur_range:
    print(f"Derailleur {derailleur['partNumber']} can't shift cassette {cassette['partNumber']}! derailleurRange: {derailleur_range} cassetteTotalPitch: {cassette_total_pitch}")

  # Calculate barrel adjuster
  barrel_adjuster = 0

  for i in range(0, 5):
    shift_positions = [barrel_adjuster + np.sum([shift_spacings[0:i]])
                      for i in range(0, len(shift_spacings) + 1) ]
    jockey_positions = derailleur_curve(shift_positions)
    cog_positions = [smallest_cog_position + np.sum([cassette_pitches[0:i]])
                    for i in range(0, len(cassette_pitches) + 1) ]
    
    diffs = cog_positions[1:num_positions - 1] - jockey_positions[1:num_positions - 1]
    
    average_diff = np.mean([diffs.min(), diffs.max()])

    barrel_adjuster = max(0, barrel_adjuster + average_diff/derailleur["pullRatio"])

  if np.abs(average_diff) > 0.01:
    print(f"Failed to converge! {derailleur['partNumber']} {cassette['partNumber']}")

  diffs_after_free_play = np.array([(
      0 if abs(d) < roller_cog_free_play
      else (
        d - roller_cog_free_play/2 if d > 0
        else d + roller_cog_free_play/2
      )
    )
    for d in diffs])
  
  max_diff_after_free_play = max(np.abs([diffs_after_free_play.min(), diffs_after_free_play.max()]))

  max_angle = np.arcsin(max_diff_after_free_play/jockey_to_cog_distance) * 180 / np.pi

  print(max_angle)

  return max_angle