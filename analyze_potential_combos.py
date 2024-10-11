
import json
from scipy.stats import norm

with open(f"other_shifters.json") as f:
  shifters = json.load(f)
with open(f"other_derailleurs.json") as f:
  derailleurs = json.load(f)
with open(f"cassettes.json") as f:
  cassettes = json.load(f)
with open(f"supported_combinations.json") as f:
  supported_combos = json.load(f)
with open(f"compatibility_ranges.json") as f:
  compatibility_ranges = json.load(f)

motion_multiplier_avg = compatibility_ranges["motionMultiplierAvg"]
motion_multiplier_stdev = compatibility_ranges["motionMultiplierStdev"]
motion_multiplier_min = compatibility_ranges["motionMultiplierMin"]
motion_multiplier_max = compatibility_ranges["motionMultiplierMax"]

potential_combos = []
extra_gear_potential_combos = []

for shifter in shifters:
  for derailleur in derailleurs:
    for cassette in cassettes:
      
      # Ignore supported combos
      if any([combo for combo in supported_combos
              if shifter["partNumber"] == combo["shifterPartNumber"]
              and derailleur["partNumber"] == combo["derailleurPartNumber"]
              and cassette["partNumber"] == combo["cassettePartNumber"]]):
        continue
      
      # Check to see how close [cable pull] * [pull ratio] is to [cog pitch]
      multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

      distFromMotionMultiplierAvg = abs(multiplier - motion_multiplier_avg)

      # Confidence = how close to the average motion multiplier are we, assuming a normal distribution?
      # 1.0 means we're dead on, < 0.05 means we're further away than 95% of all groupsets
      confidence = 1 - norm.cdf(distFromMotionMultiplierAvg, scale=motion_multiplier_stdev) \
                   + norm.cdf(-distFromMotionMultiplierAvg, scale=motion_multiplier_stdev)

      if confidence > 0.05:
        if shifter["brand"] == derailleur["brand"] and derailleur["brand"] == cassette["brand"]:
          brand = shifter["brand"]
        else:
          brand = "Mixed"
        
        if shifter['name'] == derailleur['name']:
          if cassette['brand'] == shifter['brand']:
            name = shifter['name']
          else:
            name = f"{shifter['name']}/{cassette['name']}"

        else:
          name = f"{shifter['name']}/{derailleur['name']}/{cassette['name']}"

        combo = {
          "brand": brand,
          "name": name,
          "shifterPartNumber": shifter["partNumber"],
          "derailleurPartNumber": derailleur["partNumber"],
          "cassettePartNumber": cassette["partNumber"],
          "confidence": confidence
        }

        # Record combos with more gears than shifts separately
        if shifter["speeds"] < cassette["speeds"]:
          extra_gear_potential_combos.append(combo)
        else:
          potential_combos.append(combo)



with open(f"potential_combos.json", "w") as info_file:
  json.dump(potential_combos, info_file, indent=2)

with open(f"extra_gear_potential_combos.json", "w") as info_file:
  json.dump(extra_gear_potential_combos, info_file, indent=2)