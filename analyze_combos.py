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

  motion_multipliers.append(motion_multiplier)

motion_multiplier_avg = np.mean(motion_multipliers)
motion_multiplier_stdev = np.std(motion_multipliers)

print(motion_multiplier_avg)
print(motion_multiplier_stdev)

