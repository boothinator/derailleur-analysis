import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math


with open(f"other_shifters.json") as f:
  shifters = json.load(f)
with open(f"other_derailleurs.json") as f:
  derailleurs = json.load(f)
with open(f"cassettes.json") as f:
  cassettes = json.load(f)
with open(f"supported_combinations.json") as f:
  supported_combos = json.load(f)

names = []
motion_multipliers = []

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

  # TODO: calculate jockey positions and compare to cog positions, taking into account roller size
  # Also, figure out the angles generated from jockey to cog

motion_multiplier_avg = np.mean(motion_multipliers)
motion_multiplier_stdev = np.std(motion_multipliers)
motion_multiplier_min = motion_multiplier_avg - 2*motion_multiplier_stdev
motion_multiplier_max = motion_multiplier_avg + 2*motion_multiplier_stdev

# Validate that all supported combos are in range
out_of_range = [supported_combos[i]["name"] for (i, mm) in enumerate(motion_multipliers)
                if mm < motion_multiplier_min or motion_multiplier_max < mm]

if len(out_of_range) > 0:
  print("out of range: ", out_of_range)
else:
  print("All supported combos are in range")

print(motion_multiplier_avg)
print(motion_multiplier_min)
print(motion_multiplier_max)
print(motion_multiplier_stdev)

compatibility_ranges = {
  "motionMultiplierAvg": motion_multiplier_avg,
  "motionMultiplierStdev": motion_multiplier_stdev,
  "motionMultiplierMin": motion_multiplier_min,
  "motionMultiplierMax": motion_multiplier_max
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


plt.clf()
plt.hist(motion_multipliers)
plt.savefig(f"motion_multiplier_histogram.png")