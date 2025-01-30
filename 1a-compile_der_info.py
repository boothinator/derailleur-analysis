import numpy as np
import os
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = environment.get_template("derailleur_analysis.htm")

extrusion_thickness=19.93

with open("overall_stats.json") as f:
  overall_stats = json.load(f)

with open(f"other_derailleurs.json") as f:
  all_info = json.load(f)

meas_method_percent_diffs = []

for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  print(dir)

  with open(f"derailleurs/{dir}/info_out.json", "r") as info_file:
    info_out = json.load(info_file)

  all_info.append(info_out)
  meas_method_percent_diffs = meas_method_percent_diffs + info_out["meas_method_percent_diffs"]


avg_meas_method_percent_diff = np.mean(meas_method_percent_diffs)
stdev_meas_method_percent_diff = np.std(meas_method_percent_diffs)

with open("overall_stats.json", "w") as f:
  json.dump({
    "avg_meas_method_percent_diff": avg_meas_method_percent_diff,
    "stdev_meas_method_percent_diff": stdev_meas_method_percent_diff,
    "Caliper vs Indicator percent difference": f"Caliper vs Indicator percent difference: {avg_meas_method_percent_diff} +/- {stdev_meas_method_percent_diff * 2}"
  }, f, indent=2)

with open(f"all_derailleurs.json", "w") as info_file:
  json.dump(all_info, info_file, indent=2)