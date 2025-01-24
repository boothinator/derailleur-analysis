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

for combo in supported_combos:
  shifter = [s for s in shifters
             if s["partNumber"] == combo["shifterPartNumber"]][0]
  derailleur = [s for s in derailleurs if s["partNumber"] == combo["derailleurPartNumber"]][0]
  cassette = [s for s in cassettes if s["partNumber"] == combo["cassettePartNumber"]][0]

  combo["shifter"] = shifter
  combo["derailleur"] = derailleur
  combo["cassette"] = cassette

  motion_multiplier = cassette["averagePitch"] / (shifter["cablePull"] * derailleur["pullRatio"])

  combo["motion_multiplier"] = motion_multiplier

  max_chain_angle_results = calculate_max_chain_angle(shifter, derailleur, cassette)
  combo["max_chain_angle"] = max_chain_angle_results["max_chain_angle"]

  if max_chain_angle_results["barrel_adjuster_too_low"]:
    raise Exception("Barrel adjuster too low")
  
  if max_chain_angle_results["least_pull_too_low"]:
    raise Exception("Least pull too low")
  
  if max_chain_angle_results["most_pull_too_high"]:
    print(f"Warning: most pull too high for {combo['name']}")

  if max_chain_angle_results["derailleur_can_clear_cassette"] == False:
    print(f"Warning: derailleur can't clear cassette for {combo['name']}")

names = [c["name"] for c in supported_combos]
motion_multipliers = [c["motion_multiplier"] for c in supported_combos]
max_chain_angles = [c["max_chain_angle"] for c in supported_combos]


motion_multiplier_avg = np.mean(motion_multipliers)
# Perhaps I should use the sample standard deviation (ddof=1), but using 
# regular standard deviation is more conservative
motion_multiplier_stdev = np.std(motion_multipliers)
motion_multiplier_min = motion_multiplier_avg - 2*motion_multiplier_stdev
motion_multiplier_max = motion_multiplier_avg + 2*motion_multiplier_stdev

max_chain_angle_avg = np.mean(max_chain_angles)
max_chain_angle_stdev = np.std(max_chain_angles)
max_chain_angle_num_stdevs = 2.6
max_chain_angle_max = max_chain_angle_avg + max_chain_angle_num_stdevs*max_chain_angle_stdev

# Validate that all supported combos are in range
motion_multiplier_out_of_range = [supported_combos[i]["name"] for (i, mm) in enumerate(motion_multipliers)
                if mm < motion_multiplier_min or motion_multiplier_max < mm]
max_chain_angle_out_of_range = [supported_combos[i]["name"] for (i, mm) in enumerate(max_chain_angles)
                if max_chain_angles[i] > max_chain_angle_max]

if len(motion_multiplier_out_of_range) > 0:
  print("Motion multiplier out of range: ", motion_multiplier_out_of_range)

if len(max_chain_angle_out_of_range) > 0:
  print("Max chain angle out of range: ", max_chain_angle_out_of_range)

if not motion_multiplier_out_of_range and not max_chain_angle_out_of_range:
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
  "maxChainAngleNumStdevs": max_chain_angle_num_stdevs,
  "maxChainAngleMax": max_chain_angle_max,
  "maxChainAngleMaxObserved": max(max_chain_angles),
  "groups": names,
  "groupMotionMultipliers": motion_multipliers,
  "groupMaxChainAngles": max_chain_angles
}

with open(f"compatibility_ranges.json", "w") as info_file:
  json.dump(compatibility_ranges, info_file, indent=2)

prefixes = []
max_chain_angle_avgs = []
motion_multiplier_avgs = []
max_chain_angle_stdevs = []
motion_multiplier_stdevs = []
counts = []

def graph_combos(prefix, combos):

  names = [c["name"] for c in combos]
  motion_multipliers = [c["motion_multiplier"] for c in combos]
  max_chain_angles = [c["max_chain_angle"] for c in combos]

  motion_multiplier_avg = np.mean(motion_multipliers)
  # Perhaps I should use the sample standard deviation (ddof=1), but using 
  # regular standard deviation is more conservative
  motion_multiplier_stdev = np.std(motion_multipliers)
  motion_multiplier_min = motion_multiplier_avg - 2*motion_multiplier_stdev
  motion_multiplier_max = motion_multiplier_avg + 2*motion_multiplier_stdev

  max_chain_angle_avg = np.mean(max_chain_angles)
  max_chain_angle_stdev = np.std(max_chain_angles)
  max_chain_angle_num_stdevs = 2.6
  max_chain_angle_max = max_chain_angle_avg + max_chain_angle_num_stdevs*max_chain_angle_stdev
  max_chain_angle_min = max(max_chain_angle_avg - max_chain_angle_num_stdevs*max_chain_angle_stdev, 0)

  prefixes.append(prefix)
  max_chain_angle_avgs.append(max_chain_angle_avg)
  motion_multiplier_avgs.append(motion_multiplier_avg)
  max_chain_angle_stdevs.append(max_chain_angle_stdev)
  motion_multiplier_stdevs.append(motion_multiplier_stdev)
  counts.append(len(combos))

  plt.clf()
  plt.bar(names, motion_multipliers, color="purple")
  plt.plot(names,[motion_multiplier_avg]*len(names),
          names,[motion_multiplier_min]*len(names),
          names,[motion_multiplier_max]*len(names))
  plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
            horizontalalignment="center", verticalalignment="top")
  plt.tight_layout()
  plt.ylim(motion_multiplier_min - motion_multiplier_stdev, motion_multiplier_max + motion_multiplier_stdev)
  plt.savefig(f"combo_analysis/{prefix}motion_multiplier.png")


  curve = scipy.stats.norm(motion_multiplier_avg, motion_multiplier_stdev)
  x = np.linspace(motion_multiplier_min, motion_multiplier_max)

  plt.clf()
  plt.hist(motion_multipliers)
  plt.plot(x, curve.pdf(x)/10)
  plt.savefig(f"combo_analysis/{prefix}motion_multiplier_histogram.png")


  plt.clf()
  plt.bar(names, max_chain_angles, color="purple")
  plt.plot(names,[max_chain_angle_avg]*len(names),
          names,[max_chain_angle_min]*len(names),
          names,[max_chain_angle_max]*len(names))
  plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
            horizontalalignment="center", verticalalignment="top")
  plt.tight_layout()
  plt.ylim(0, max_chain_angle_max + max_chain_angle_stdev)
  plt.savefig(f"combo_analysis/{prefix}max_chain_angle.png")


  curve = scipy.stats.norm(max_chain_angle_avg, max_chain_angle_stdev)
  x = np.linspace(max_chain_angle_min, max_chain_angle_max)

  plt.clf()
  plt.hist(max_chain_angles)
  plt.plot(x, curve.pdf(x)/10)
  plt.savefig(f"combo_analysis/{prefix}max_chain_angle_histogram.png")

graph_combos("all_", supported_combos)
graph_combos("10_speed_", [c for c in supported_combos if c["shifter"]["speeds"] == 10])
graph_combos("11_speed_", [c for c in supported_combos if c["shifter"]["speeds"] == 11])
graph_combos("slant_", [c for c in supported_combos if c["derailleur"]["parallelogramStyle"] == "slant"])
graph_combos("straight_", [c for c in supported_combos if c["derailleur"]["parallelogramStyle"] == "straight"])
graph_combos("34t_or_less_", [c for c in supported_combos if c["derailleur"]["maxTooth"] <= 34])
graph_combos("34t_through_42t_", [c for c in supported_combos if c["derailleur"]["maxTooth"] > 34 and c["derailleur"]["maxTooth"] <= 42])
graph_combos("more_than_42t_", [c for c in supported_combos if c["derailleur"]["maxTooth"] > 42])




plt.clf()
plt.bar(prefixes, motion_multiplier_avgs, color="purple")
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
          horizontalalignment="center", verticalalignment="top")
plt.ylim(min(motion_multiplier_avgs) - 0.01, max(motion_multiplier_avgs) + 0.01)
plt.tight_layout()
plt.savefig(f"combo_analysis/category_motion_multiplier_avg.png")

plt.clf()
plt.bar(prefixes, max_chain_angle_avgs, color="purple")
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
          horizontalalignment="center", verticalalignment="top")
plt.tight_layout()
plt.savefig(f"combo_analysis/category_max_chain_angle_avg.png")

plt.clf()
plt.bar(prefixes, motion_multiplier_stdevs, color="purple")
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
          horizontalalignment="center", verticalalignment="top")
plt.tight_layout()
plt.savefig(f"combo_analysis/category_motion_multiplier_stdev.png")

plt.clf()
plt.bar(prefixes, max_chain_angle_stdevs, color="purple")
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
          horizontalalignment="center", verticalalignment="top")
plt.tight_layout()
plt.savefig(f"combo_analysis/category_max_chain_angle_stdev.png")

plt.clf()
plt.bar(prefixes, counts, color="purple")
plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
          horizontalalignment="center", verticalalignment="top")
plt.tight_layout()
plt.savefig(f"combo_analysis/category_counts.png")