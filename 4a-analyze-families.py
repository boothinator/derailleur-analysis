import csv
import matplotlib.pyplot as plt
import json

with open(f"compatibility_ranges.json") as f:
  compatibility_ranges = json.load(f)

def tryConvert(str):
  try:
    return float(str)
  except:
    if str == "True":
      return True
    elif str == "False":
      return False
    else:
      return str

with open("all_combos.csv") as f:
  reader = csv.DictReader(f)

  combos = [dict([(i[0], tryConvert(i[1])) for i in c.items()]) for c in reader]

def plot(prefix, combos):
  
  data = [
    ([c for c in combos if c["failedAnyCriteria"] and c['supported']], "Supported but not in compatibility ranges", "orange"),
    ([c for c in combos if c["failedAnyCriteria"] and not c['supported']], "Not in compatibility ranges", "red"),
    ([c for c in combos if not c["failedAnyCriteria"] and c['supported']], "Supported", "green"),
    ([c for c in combos if not c["failedAnyCriteria"] and not c['supported']], "In compatibilty ranges", "yellow")
  ]

  data = [d for d in data if len(d[0]) > 0]

  plt.clf()
  plt.pie([len(d[0]) for d in data], labels = [d[1] for d in data])
  plt.savefig(f"group_analysis/{prefix}_criteria.png")

  # plt.clf()
  # names = [c["name"] for d in data for c in d[0]]
  # motion_multipliers = [c["motionMultiplier"] for d in data for c in d[0]]
  # colors = [d[2] for d in data for _ in d[0]]
  # plt.bar(names, motion_multipliers, color=colors)
  # plt.ylim(0.9)
  # plt.plot(names,[compatibility_ranges["motionMultiplierAvg"]]*len(names),
  #         names,[compatibility_ranges["motionMultiplierMin"]]*len(names),
  #         names,[compatibility_ranges["motionMultiplierMax"]]*len(names))
  
  # plt.xticks(wrap=False, rotation="vertical", rotation_mode="anchor",
  #           horizontalalignment="center", verticalalignment="top")
  # plt.savefig(f"group_analysis/{prefix}_motion_multiplier.png")


  #plt.clf()
  #plt.hist(motion_multipliers)
  #plt.plot(x, curve.pdf(x)/10)
  #plt.savefig(f"group_analysis/{prefix}_motion_multiplier_histogram.png")


plot("dynasys_10_speed", [c for c in combos if c["shifterSpeeds"] == 10 and c["shifterCablePull"] > 3.35 and c["derailleurPullRatio"] < 1.16 and c["numberOfShiftsMatchesCogs"]])
plot("dynasys_11_speed", [c for c in combos if c["shifterSpeeds"] == 11 and c["shifterCablePull"] > 3.35 and c["derailleurPullRatio"] < 1.16 and c["numberOfShiftsMatchesCogs"]])
plot("dynasys_12_speed", [c for c in combos if c["shifterSpeeds"] == 12 and c["shifterCablePull"] > 3.1 and c["derailleurPullRatio"] < 1.16 and c["numberOfShiftsMatchesCogs"]])
plot("shimano_10_speed_road", [c for c in combos if c["shifterSpeeds"] == 10 and c["shifterCablePull"] > 2.5 and c["shifterCablePull"] < 2.7
                               and c["derailleurPullRatio"] > 1.4 and c["derailleurPullRatio"] < 1.6 and c["numberOfShiftsMatchesCogs"]
                               and c["cassettePitch"] < 4 and c["cassettePitch"] > 3.9])