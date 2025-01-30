
import json
import numpy as np
from util import calc_pull_ratio

cassette_types = [{
  'name': '10-speed',
  'speeds': 10,
  'design_cog_pitch': 3.95
},{
  'name': '11-speed',
  'speeds': 10,
  'design_cog_pitch': 3.75
},{
  'name': '12-speed',
  'speeds': 10,
  'design_cog_pitch': 3.6
},{
  'name': 'LinkGlide 9-speed',
  'speeds': 9,
  'design_cog_pitch': 4.05
},{
  'name': 'LinkGlide 10-speed',
  'speeds': 10,
  'design_cog_pitch': 4.05
},{
  'name': 'LinkGlide 11-speed',
  'speeds': 11,
  'design_cog_pitch': 4.05
}]

# TODO: analyze each derailleur according to the cassette type they support
# This is especially important for classic Shimano cable pull

def generate_family_info(derailleurs):
  avg_coefficients = np.average([d["coefficients"] for d in derailleurs], axis=0)

  per_der_pull_ratios = {
    ct['name']: {
      "pull_ratios": [calc_pull_ratio(d, d["coefficients"],
                                      design_cog_pitch=ct['design_cog_pitch'],
                                      design_speeds=ct['speeds']
                                      ).pull_ratio
                                      for d in derailleurs]
    }
    for ct in cassette_types
  }

  per_speed_pull_ratios = {key: {
    "avg": float(np.average(pr["pull_ratios"])),
    "stdev": float(np.std(pr["pull_ratios"])),
  } for key,pr in per_der_pull_ratios.items()}

  for pr in per_speed_pull_ratios.values():
    pull_ratio_avg = pr['avg']
    pull_ratio_stdev = pr['stdev']
    pr["Pull Ratio 95% Confidence Interval"] = f"{round(pull_ratio_avg - 2 * pull_ratio_stdev, 3):.3f} to {round(pull_ratio_avg + 2 * pull_ratio_stdev, 3):.3f}",
  
  all_pull_ratios = [pr2 for pr in per_der_pull_ratios.values() for pr2 in pr["pull_ratios"]]

  pull_ratio_avg =  float(np.average(all_pull_ratios))
  pull_ratio_stdev =  float(np.std(all_pull_ratios))

  return {
    "averageCoefficients": [float(c) for c in avg_coefficients],
    "averagePullRatio": pull_ratio_avg,
    "pullRatioStdev": pull_ratio_stdev,
    "Pull Ratio 95% Confidence Interval": f"{round(pull_ratio_avg - 2 * pull_ratio_stdev, 3):.3f} to {round(pull_ratio_avg + 2 * pull_ratio_stdev, 3):.3f}",
    "derailleurs": [{key: value for key, value in d.items()
                      if key in {'brand', 'name', 'partNumber'}
                     } for d in derailleurs],
    "perSpeedPullRatios": per_speed_pull_ratios
  }


with open(f"all_derailleurs.json") as f:
  derailleurs = json.load(f)

families_info = {
  "dynasys": generate_family_info([d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] < 1.2
                                   and d['partNumber'].startswith('RD-M')]),
  "CUES": generate_family_info([d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] < 1.2
                                   and d['partNumber'].startswith('RD-U')]),
  "Shimano New Road": generate_family_info([d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] > 1.4
                                   and d["pullRatio"] < 1.6]),
  "Classic Shimano": generate_family_info([d for d in derailleurs
                                   if d["pullRatio"] > 1.6]),
  "dynasys-like": generate_family_info([d for d in derailleurs
                                   if d["pullRatio"] < 1.2]),
}


with open(f"families_info.json", "w") as info_file:
  json.dump(families_info, info_file, indent=2)
