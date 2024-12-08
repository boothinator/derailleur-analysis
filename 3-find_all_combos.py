
import json
from scipy.stats import norm
from util import calculate_max_chain_angle

with open(f"all_shifters.json") as f:
  shifters = json.load(f)
with open(f"equivalent_shifters.json") as f:
  equivalent_shifters = json.load(f)
with open(f"all_derailleurs.json") as f:
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
max_chain_angle_max = compatibility_ranges["maxChainAngleMax"]

combos = []
partial_fail_combos = []

for shifter in shifters:
  equiv_shifters = [s for s in equivalent_shifters if s["equivalentPartNumber"] == shifter["partNumber"]]

  for derailleur in derailleurs:
    equiv_derailleurs = [s for s in equivalent_derailleurs if s["equivalentPartNumber"] == derailleur["partNumber"]]

    for speeds in range(9, 14):
      shifter_name = shifter["brand"] + " " + shifter["name"]

      if shifter["brand"] == derailleur["brand"]:
        brand = shifter["brand"]
        derailleur_name = derailleur["name"]
      else:
        brand = "Mixed"
        derailleur_name = derailleur["brand"] + " " + derailleur["name"]

      shifter_name = shifter_name + f' {shifter["speeds"]}-Speed'
      derailleur_name = derailleur_name + f' {derailleur["designSpeeds"]}-Speed'
      
      if shifter["brand"] == derailleur["brand"] \
        and shifter["name"] == derailleur["name"] \
          and speeds == shifter["speeds"] and speeds == derailleur["designSpeeds"]:
        # Same group
        same_group = True
        combo_name = partial_name = f"{shifter["brand"]} {shifter['name']} {speeds}-Speed group"
      else:
        same_group = False
        partial_name = f"{shifter_name} shifter/{derailleur_name} derailleur"
        combo_name = partial_name + f"/{speeds}-Speed cassette"

      # Build combo info
      combo = {
        "brand": brand,
        "name": combo_name,
        "partialName": partial_name,
        "shifterPartialName": shifter_name,
        "derailleurPartialName": derailleur_name,
        "speeds": speeds,
        "accessibleSpeeds": min(shifter["speeds"], speeds),
        "sameGroup": same_group,
        "shifterPartNumber": shifter["partNumber"],
        "shifterName": shifter["name"],
        "shifterBrand": shifter["brand"],
        "derailleurPartNumber": derailleur["partNumber"],
        "derailleurName": derailleur["name"],
        "derailleurBrand": derailleur["brand"],
        "cassettes": [],
        "shifterType": shifter["type"],
        "noMatchingFrontShifter": shifter["hasMatchingFrontShifters"] == False
          and derailleur["supportsMultipleFrontChainrings"],
        "moreCogsThanShifts": shifter["speeds"] < speeds,
        "moreShiftsThanCogs": shifter["speeds"] > speeds,
        "maxToothAvailableAndCompatible": 0,
        "maxToothAvailableAndUnofficiallyCompatible": 0,
        "maxToothAvailableAndCompatibleWithGoatLink": 0,
        "maxToothAvailableAndSupported": 0,
        "supported": False,
        "chainWrap": derailleur["chainWrap"],
        "equivalentShifters": equiv_shifters,
        "equivalentDerailleurs": equiv_derailleurs
      }

      # Look for compatible cassettes
      for cassette in [c for c in cassettes if c["speeds"] == speeds]:
        
        # Check to see how close [cable pull] * [pull ratio] is to [cog pitch]
        multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

        distFromMotionMultiplierAvg = abs(multiplier - motion_multiplier_avg)

        # Confidence = how close to the average motion multiplier are we, assuming a normal distribution?
        # 1.0 means we're dead on, < 0.05 means we're further away than 95% of all groupsets
        confidence = 1 - norm.cdf(distFromMotionMultiplierAvg, scale=motion_multiplier_stdev) \
                    + norm.cdf(-distFromMotionMultiplierAvg, scale=motion_multiplier_stdev)
        
        max_chain_angle_results = calculate_max_chain_angle(shifter, derailleur, cassette)

        barrel_adjuster_too_low = max_chain_angle_results["barrel_adjuster_too_low"]
        least_pull_too_low = max_chain_angle_results["least_pull_too_low"]
        max_chain_angle_too_high = max_chain_angle_results["max_chain_angle"] > max_chain_angle_max
        confidence_too_low = confidence < 0.05
        not_enough_range_on_derailleur = max_chain_angle_results["derailleur_can_clear_cassette"] == False
        smallest_cassette_too_big_official_max_tooth = "minMaxToothAvailable" in cassette and cassette["minMaxToothAvailable"] > derailleur["maxTooth"]
        smallest_cassette_too_big_unofficial_max_tooth = cassette["minMaxToothAvailable"] > derailleur["maxToothUnofficial"] \
          if "minMaxToothAvailable" in cassette and "maxToothUnofficial" in derailleur and derailleur["maxToothUnofficial"] != None \
          else None
        smallest_cassette_too_big_with_goat_link = cassette["minMaxToothAvailable"] > derailleur["maxToothWithGoatLink"] \
          if "minMaxToothAvailable" in cassette and "maxToothWithGoatLink" in derailleur and derailleur["maxToothWithGoatLink"] != None \
          else None
        smallest_cassette_too_big = smallest_cassette_too_big_official_max_tooth \
          and (smallest_cassette_too_big_unofficial_max_tooth or smallest_cassette_too_big_unofficial_max_tooth == None) \
          and (smallest_cassette_too_big_with_goat_link or smallest_cassette_too_big_with_goat_link == None)

        fail_criteria = [
          confidence_too_low, max_chain_angle_too_high, barrel_adjuster_too_low,
          least_pull_too_low, not_enough_range_on_derailleur, smallest_cassette_too_big
        ]

        #Log combos that fail any, but not all criteria
        if any(fail_criteria):
          if not all(fail_criteria):
            partial_fail_combos.append({
              "confidence_too_low": bool(confidence_too_low),
              "max_chain_angle_too_high": bool(max_chain_angle_too_high),
              "barrel_adjuster_too_low": bool(barrel_adjuster_too_low),
              "least_pull_too_low": bool(least_pull_too_low),
              "not_enough_range_on_derailleur": bool(not_enough_range_on_derailleur),
              "smallest_cassette_too_big_official_max_tooth": bool(smallest_cassette_too_big_official_max_tooth),
              "smallest_cassette_too_big_unofficial_max_tooth": smallest_cassette_too_big_unofficial_max_tooth,
              "smallest_cassette_too_big_with_goat_link": smallest_cassette_too_big_with_goat_link,
              "smallest_cassette_too_big": bool(smallest_cassette_too_big),
              **combo,
              "cassettePartNumber": cassette["partNumber"],
              "confidence": confidence,
              "maxChainAngle": max_chain_angle_results["max_chain_angle"],
              "maxAngleAnalysis": max_chain_angle_results,
              "motionMultiplier": multiplier,
              "equivalentShifters": [],
              "equivalentDerailleurs": [],
              "cassettes": []
            })
        else:
        
          if max_chain_angle_results["most_pull_too_high"]:
            print(f"Warning: most pull too high for {combo['name']} with cassette {cassette["partNumber"]}")
          
          maxToothAvailableAndCompatible = min(derailleur["maxTooth"], cassette["maxToothAvailable"])
          maxToothAvailableAndUnofficiallyCompatible = min(derailleur["maxToothUnofficial"], cassette["maxToothAvailable"]) \
            if "maxToothUnofficial" in derailleur and derailleur["maxToothUnofficial"] != None \
            else 0
          maxToothAvailableAndCompatibleWithGoatLink = min(derailleur["maxToothWithGoatLink"], cassette["maxToothAvailable"]) \
            if "maxToothWithGoatLink" in derailleur and derailleur["maxToothWithGoatLink"] != None \
            else 0

          supported = any([combo for combo in supported_combos
                if shifter["partNumber"] == combo["shifterPartNumber"]
                and derailleur["partNumber"] == combo["derailleurPartNumber"]
                and cassette["partNumber"] == combo["cassettePartNumber"]])

          combo["cassettes"].append({
            "cassettePartNumber": cassette["partNumber"],
            "cassetteName": cassette["name"],
            "cassetteBrand": cassette["brand"],
            "confidence": confidence,
            "supported": supported,
            "maxToothAvailableAndCompatible": maxToothAvailableAndCompatible,
            "maxToothAvailableAndUnofficiallyCompatible": maxToothAvailableAndUnofficiallyCompatible,
            "maxToothAvailableAndCompatibleWithGoatLink": maxToothAvailableAndCompatibleWithGoatLink,
            "maxChainAngle": max_chain_angle_results["max_chain_angle"],
            "maxAngleAnalysis": max_chain_angle_results,
            "motionMultiplier": multiplier,
            "smallest_cassette_too_big_official_max_tooth": bool(smallest_cassette_too_big_official_max_tooth),
            "smallest_cassette_too_big_unofficial_max_tooth": smallest_cassette_too_big_unofficial_max_tooth,
            "smallest_cassette_too_big_with_goat_link": smallest_cassette_too_big_with_goat_link
          })

          # Update combo max tooth with cassette info
          combo["maxToothAvailableAndCompatible"] = max(combo["maxToothAvailableAndCompatible"], maxToothAvailableAndCompatible)
          combo["maxToothAvailableAndUnofficiallyCompatible"] = max(combo["maxToothAvailableAndUnofficiallyCompatible"], maxToothAvailableAndCompatible)
          combo["maxToothAvailableAndCompatibleWithGoatLink"] = max(combo["maxToothAvailableAndCompatibleWithGoatLink"], maxToothAvailableAndCompatible)
          if supported:
            combo["maxToothAvailableAndSupported"] = max(combo["maxToothAvailableAndSupported"], maxToothAvailableAndCompatible)
          combo["supported"] = combo["supported"] or supported
      
      # Save combo if compatible cassette was found
      if len(combo["cassettes"]) > 0:
        # Find reviews
        reviews  = [r for r in reviewed_combos
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
        
        combo["reviews"] = reviews

        if len(reviews) > 0:
          positive_reviews = [r for r in reviews if r["sentiment"] == "positive"]
          negative_reviews = [r for r in reviews if r["sentiment"] == "negative"]
          if len(positive_reviews) > 0 and len(negative_reviews) > 0:
            combo["reviewsSentiment"] = "mixed"
          elif len(positive_reviews) > 0:
            combo["reviewsSentiment"] = "positive"
          else:
            combo["reviewsSentiment"] = "negative"
        else:
          combo["reviewsSentiment"] = "none"
        
        combos.append(combo)



with open(f"combinations.json", "w") as info_file:
  json.dump(combos, info_file, indent=2)

with open(f"partial_fail_combos.json", "w") as info_file:
  json.dump(partial_fail_combos, info_file, indent=2)

with open(f"all_cassettes.json", "w") as info_file:
  json.dump(cassettes, info_file, indent=2)