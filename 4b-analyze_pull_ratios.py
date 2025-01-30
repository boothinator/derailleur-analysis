
import json
import numpy as np

# TODO: analyze each derailleur according to the cassette type they support
# This is especially important for classic Shimano cable pull

def generate_family_info(derailleurs):
  avg_coefficients = np.average([d["coefficients"] for d in derailleurs], axis=0)

  per_der_pull_ratios = [d["pullRatio"] for d in derailleurs]

  pull_ratio_avg =  float(np.average(per_der_pull_ratios))
  pull_ratio_stdev =  float(np.std(per_der_pull_ratios))

  return {
    "averageCoefficients": [float(c) for c in avg_coefficients],
    "averagePullRatio": pull_ratio_avg,
    "pullRatioStdev": pull_ratio_stdev,
    "Pull Ratio 95% Confidence Interval": f"{round(pull_ratio_avg - 2 * pull_ratio_stdev, 3):.3f} to {round(pull_ratio_avg + 2 * pull_ratio_stdev, 3):.3f}",
    "derailleurs": [{key: value for key, value in d.items()
                      if key in {'brand', 'name', 'partNumber', 'pullRatio'}
                     } for d in derailleurs]
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
