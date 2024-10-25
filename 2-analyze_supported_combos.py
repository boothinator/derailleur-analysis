import numpy as np
import matplotlib.pyplot as plt
import json
import scipy.stats
from util import calculate_max_chain_angle

with open(f"all_shifters.json") as f:
  shifters = json.load(f)
with open(f"all_derailleurs.json") as f:
  derailleurs = json.load(f)
with open(f"cassettes.json") as f:
  cassettes = json.load(f)
with open(f"supported_combinations.json") as f:
  supported_combos = json.load(f)

names = []
motion_multipliers = []
max_chain_angles = []

for combo in supported_combos:
  shifter = [s for s in shifters
             if s["partNumber"] == combo["shifterPartNumber"]
             and s["brand"] == combo["brand"]][0]
  derailleur = [s for s in derailleurs if s["partNumber"] == combo["derailleurPartNumber"]
             and s["brand"] == combo["brand"]][0]
  cassette = [s for s in cassettes if s["partNumber"] == combo["cassettePartNumber"]
             and (s["brand"] == combo["brand"] or
                  ("cassetteBrand" in combo and s["brand"] == combo["cassetteBrand"]))][0]

  motion_multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

  names.append(f"{combo['name']}")
  motion_multipliers.append(motion_multiplier)

  max_chain_angle_results = calculate_max_chain_angle(shifter, derailleur, cassette)
  max_chain_angles.append(max_chain_angle_results["max_chain_angle"])

  if max_chain_angle_results["barrel_adjuster_too_low"]:
    raise Exception("Barrel adjuster too low")
  
  if max_chain_angle_results["least_pull_too_low"]:
    raise Exception("Least pull too low")
  
  if max_chain_angle_results["most_pull_too_high"]:
    print(f"Warning: most pull too high for {combo['name']}")

  if max_chain_angle_results["derailleur_can_clear_cassette"] == False:
    print(f"Warning: derailleur can't clear cassette for {combo['name']}")


motion_multiplier_avg = np.mean(motion_multipliers)
# Perhaps I should use the sample standard deviation (ddof=1), but using 
# regular standard deviation is more conservative
motion_multiplier_stdev = np.std(motion_multipliers)
motion_multiplier_min = motion_multiplier_avg - 2*motion_multiplier_stdev
motion_multiplier_max = motion_multiplier_avg + 2*motion_multiplier_stdev

max_chain_angle_avg = np.mean(max_chain_angles)
max_chain_angle_stdev = np.std(max_chain_angles)
max_chain_angle_max = max_chain_angle_avg + 2*max_chain_angle_stdev

# Validate that all supported combos are in range
out_of_range = [supported_combos[i]["name"] for (i, mm) in enumerate(motion_multipliers)
                if mm < motion_multiplier_min or motion_multiplier_max < mm
                  or max_chain_angles[i] > max_chain_angle_max]

if len(out_of_range) > 0:
  print("out of range: ", out_of_range)
else:
  print("All supported combos are in range")

compatibility_ranges = {
  "motionMultiplierAvg": motion_multiplier_avg,
  "motionMultiplierStdev": motion_multiplier_stdev,
  "motionMultiplierMin": motion_multiplier_min,
  "motionMultiplierMax": motion_multiplier_max,
  "motionMultiplierMinObserved": min(motion_multipliers),
  "motionMultiplierMaxObserved": max(motion_multipliers),
  "maxChainAngleAvg": max_chain_angle_avg,
  "maxChainAngleStdev": max_chain_angle_stdev,
  "maxChainAngleMax": max_chain_angle_max,
  "maxChainAngleMaxObserved": max(max_chain_angles),
  "groups": names,
  "groupMotionMultipliers": motion_multipliers
}

with open(f"compatibility_ranges.json", "w") as info_file:
  json.dump(compatibility_ranges, info_file, indent=2)

plt.clf()
plt.bar(names, motion_multipliers, color="purple")
plt.plot(names,[motion_multiplier_avg]*len(names),
         names,[motion_multiplier_min]*len(names),
         names,[motion_multiplier_max]*len(names))
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
           horizontalalignment="center", verticalalignment="top")
plt.tight_layout()
plt.ylim(motion_multiplier_min - motion_multiplier_stdev, motion_multiplier_max + motion_multiplier_stdev)
plt.savefig(f"motion_multiplier.png")


curve = scipy.stats.norm(motion_multiplier_avg, motion_multiplier_stdev)
x = np.linspace(motion_multiplier_min, motion_multiplier_max)

plt.clf()
plt.hist(motion_multipliers)
plt.plot(x, curve.pdf(x)/10)
plt.savefig(f"motion_multiplier_histogram.png")