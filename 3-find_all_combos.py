
import json
from scipy.stats import norm

with open(f"other_shifters.json") as f:
  shifters = json.load(f)
with open(f"equivalent_shifters.json") as f:
  equivalent_shifters = json.load(f)
with open(f"other_derailleurs.json") as f:
  derailleurs = json.load(f)
with open(f"equivalent_derailleurs.json") as f:
  equivalent_derailleurs = json.load(f)
with open(f"cassettes.json") as f:
  cassettes = json.load(f)
with open(f"supported_combinations.json") as f:
  supported_combos = json.load(f)
with open(f"reviewed_combinations.json") as f:
  reviewed_combos = json.load(f)
with open(f"compatibility_ranges.json") as f:
  compatibility_ranges = json.load(f)

motion_multiplier_avg = compatibility_ranges["motionMultiplierAvg"]
motion_multiplier_stdev = compatibility_ranges["motionMultiplierStdev"]

combos = []

for shifter in shifters:
  equiv_shifters = [s for s in equivalent_shifters if s["equivalentPartNumber"] == shifter["partNumber"]]

  for derailleur in derailleurs:
    equiv_derailleurs = [s for s in equivalent_derailleurs if s["equivalentPartNumber"] == derailleur["partNumber"]]

    for speeds in range(9, 14):
      
      # Generate a name for this combo
      if shifter["brand"] == derailleur["brand"]:
        brand = shifter["brand"]
        
        if shifter["name"] == derailleur["name"]:
          name = f"{shifter["brand"]} {shifter['name']} group with {speeds}-speed cassette"
        else:
          name = f"{shifter["brand"]} {shifter['name']} shifter/" \
              + f"{derailleur['name']} derailleur/{speeds}-speed cassette"
      else:
        brand = "Mixed"

        name = f"{shifter["brand"]} {shifter['name']} shifter/" \
            + f"{derailleur["brand"]} {derailleur['name']} derailleur/" \
            + f"{speeds}-speed cassette"

      # Build combo info
      combo = {
        "brand": brand,
        "name": name,
        "speeds": speeds,
        "shifterPartNumber": shifter["partNumber"],
        "derailleurPartNumber": derailleur["partNumber"],
        "cassettes": [],
        "shifterType": shifter["type"],
        "noMatchingFrontShifter": shifter["hasMatchingFrontShifters"] == False
          and derailleur["supportsMultipleFrontChainrings"],
        "moreCogsThanShifts": shifter["speeds"] < speeds,
        "maxToothAvailableAndCompatible": 0,
        "chainWrap": derailleur["chainWrap"],
        "equivalentShifters": equiv_shifters,
        "equivalentDerailleurs": equiv_derailleurs
      }

      cassettesTested = 0

      # Look for compatible cassettes
      for cassette in [c for c in cassettes if c["speeds"] == speeds]:
        cassettesTested = cassettesTested + 1
        
        # Check to see how close [cable pull] * [pull ratio] is to [cog pitch]
        multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

        distFromMotionMultiplierAvg = abs(multiplier - motion_multiplier_avg)

        # Confidence = how close to the average motion multiplier are we, assuming a normal distribution?
        # 1.0 means we're dead on, < 0.05 means we're further away than 95% of all groupsets
        confidence = 1 - norm.cdf(distFromMotionMultiplierAvg, scale=motion_multiplier_stdev) \
                    + norm.cdf(-distFromMotionMultiplierAvg, scale=motion_multiplier_stdev)

        if confidence > 0.05:
          maxToothAvailableAndCompatible = min(derailleur["maxTooth"], cassette["maxToothAvailable"])

          combo["cassettes"].append({
            "cassettePartNumber": cassette["partNumber"],
            "confidence": confidence,
            "supported": any([combo for combo in supported_combos
                if shifter["partNumber"] == combo["shifterPartNumber"]
                and derailleur["partNumber"] == combo["derailleurPartNumber"]
                and cassette["partNumber"] == combo["cassettePartNumber"]]),
            "maxToothAvailableAndCompatible": maxToothAvailableAndCompatible
          })

          combo["maxToothAvailableAndCompatible"] = max(combo["maxToothAvailableAndCompatible"], maxToothAvailableAndCompatible)
      
      # Save combo if compatible cassette was found
      if len(combo["cassettes"]) > 0:
        # Find reviews
        combo["reviews"] = [r for r in reviewed_combos
                    if (shifter["partNumber"] == r["shifterPartNumber"]
                        or any([e for e in equiv_shifters
                                if e["partNumber"] == r["shifterPartNumber"]])
                      )
                      and (derailleur["partNumber"] == r["derailleurPartNumber"]
                        or any([e for e in equiv_derailleurs
                                if e["partNumber"] == r["derailleurPartNumber"]])
                      )
                      and any([c for c in combo["cassettes"]
                               if c["cassettePartNumber"] == r["cassettePartNumber"]])
                  ]
        
        combos.append(combo)



with open(f"combinations.json", "w") as info_file:
  json.dump(combos, info_file, indent=2)