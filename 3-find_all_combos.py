
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

combos = []

for shifter in shifters:
  for derailleur in derailleurs:
    for cassette in cassettes:
      
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
          if cassette['brand'] == shifter['brand'] and cassette['speeds'] == shifter['speeds']:
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
          "confidence": confidence,
          "supported": any([combo for combo in supported_combos
              if shifter["partNumber"] == combo["shifterPartNumber"]
              and derailleur["partNumber"] == combo["derailleurPartNumber"]
              and cassette["partNumber"] == combo["cassettePartNumber"]]),
          "shifterType": shifter["type"],
          "noMatchingFrontShifter": shifter["hasMatchingFrontShifters"] == False
            and derailleur["supportsMultipleFrontChainrings"],
          "moreCogsThanShifts": shifter["speeds"] < cassette["speeds"],
          "maxTooth": derailleur["maxTooth"],
          "chainWrap": derailleur["chainWrap"]
        }

        combos.append(combo)



with open(f"combinations.json", "w") as info_file:
  json.dump(combos, info_file, indent=2)