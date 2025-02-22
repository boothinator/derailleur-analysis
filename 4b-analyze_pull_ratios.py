
import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats

# TODO: analyze each derailleur according to the cassette type they support
# This is especially important for classic Shimano cable pull

def generate_family_info(name, derailleurs):
  avg_coefficients = np.average([d["coefficients"] for d in derailleurs], axis=0)

  per_der_pull_ratios = [d["pullRatio"] for d in derailleurs]

  pull_ratio_avg =  float(np.average(per_der_pull_ratios))
  pull_ratio_stdev =  float(np.std(per_der_pull_ratios))

  
  avg_curve = np.polynomial.polynomial.Polynomial(avg_coefficients)

  max_pull = 40

  x = np.linspace(0, max_pull, 50)

  plt.clf()
  for d in derailleurs:
    curve = np.polynomial.polynomial.Polynomial(d["coefficients"])
    y = curve(x)
    plt.plot(x, y, "blue")
  
  y = avg_curve(x)
  plt.plot(x, y, "red")
  plt.tight_layout()
  plt.savefig(f"pull_ratio_analysis/{name}_pull_curve.png")

  plt.clf()
  for d in derailleurs:
    curve = np.polynomial.polynomial.Polynomial(d["coefficients"])
    y = curve.deriv()(x)
    plt.plot(x, y, "blue")
  
  y = avg_curve.deriv()(x)
  plt.plot(x, y, "red")
  plt.tight_layout()
  plt.savefig(f"pull_ratio_analysis/{name}_pull_ratio_curve.png")

  curve = scipy.stats.norm(pull_ratio_avg, pull_ratio_stdev)
  x = np.linspace(pull_ratio_avg - 2*pull_ratio_stdev, pull_ratio_avg + 2*pull_ratio_stdev)
  
  plt.clf()
  hist_counts,bins,_ = plt.hist(per_der_pull_ratios)
  plt.plot(x, curve.pdf(x)/10)
  plt.xticks(ticks=np.round(bins, 3), wrap=False, rotation=45, rotation_mode="anchor",
            horizontalalignment="right", verticalalignment="center")
  plt.yticks(range(round(np.max(hist_counts) + 1)))
  #plt.xlabel("Motion Multiplier\n(Cog Pitch / Avg. Guide Pulley Movement Per Shift)")
  #plt.ylabel("Number of Supported Groupsets")
  plt.tight_layout()
  plt.savefig(f"pull_ratio_analysis/{name}_pull_ratio_histogram.png")

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
  "dynasys": generate_family_info("dynasys", [d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] < 1.2
                                   and d['partNumber'].startswith('RD-M')]),
  "CUES": generate_family_info("CUES", [d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] < 1.2
                                   and d['partNumber'].startswith('RD-U')]),
  "Shimano New Road": generate_family_info("Shimano New Road", [d for d in derailleurs
                                   if d["brand"] == 'Shimano'
                                   and d["pullRatio"] > 1.4
                                   and d["pullRatio"] < 1.6]),
  "Classic Shimano": generate_family_info("Classic Shimano", [d for d in derailleurs
                                   if d["pullRatio"] > 1.6]),
  "dynasys-like": generate_family_info("dynasys-like", [d for d in derailleurs
                                   if d["pullRatio"] < 1.2]),
}


with open(f"families_info.json", "w") as info_file:
  json.dump(families_info, info_file, indent=2)
