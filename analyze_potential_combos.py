
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
      
      multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

      distFromMotionMultiplierAvg = abs(multiplier - motion_multiplier_avg)

      confidence = 1 - norm.cdf(distFromMotionMultiplierAvg, scale=motion_multiplier_stdev) \
                   + norm.cdf(-distFromMotionMultiplierAvg, scale=motion_multiplier_stdev)

      minCogPitch = shifter["cablePull"] * derailleur["pullRatio"] * motion_multiplier_min
      maxCogPitch = shifter["cablePull"] * derailleur["pullRatio"] * motion_multiplier_max

      if minCogPitch <= cassette["averagePitch"] and cassette["averagePitch"] <= maxCogPitch:
        if shifter["brand"] == derailleur["brand"] and derailleur["brand"] == cassette["brand"]:
          brand = shifter["brand"]
        else:
          brand = "Mixed"
        
        name = f"{shifter['name']} {derailleur['name']} {cassette['name']}"

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