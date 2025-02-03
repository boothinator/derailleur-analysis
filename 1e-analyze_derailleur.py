import numpy as np
import matplotlib.pyplot as plt
import os
import json
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

# TODO:
# Combine yaw pull ratio with regular pull ratio, and yaw pull ratio curve with base pull ratio curve to get overall pull ratio curve
# Can I combine both curves into a single curve using just a 3rd order polynomial? Or would that kink from the yaw curve be too much to model well

# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = environment.get_template("derailleur_analysis.htm")

extrusion_thickness=19.93

with open("overall_stats.json") as f:
  overall_stats = json.load(f)

def process_der(dir):
  
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  with open(f"derailleurs/{dir}/pullratio/base_pull_ratio_info.json") as info_file:
    base_pull_ratio_info = json.load(info_file)
  
  with open(f"derailleurs/{dir}/yaw/yaw_info.json") as info_file:
    yaw_info = json.load(info_file)
  
  # Info Output
  info_out = {
    **info,
    'pullRatio': base_pull_ratio_info['basePullRatio'], # For now
    "Pull Ratio Averaged Across Pulling Runs": base_pull_ratio_info["Base Pull Ratio Averaged Across Pulling Runs"],
    "Pull Ratio Averaged Across Relaxing Runs": base_pull_ratio_info["Base Pull Ratio Averaged Across Relaxing Runs"],
    "Pull Ratio Averaged Across All Runs": base_pull_ratio_info["Base Pull Ratio Averaged Across All Runs"],
    "Pull Ratio 95% Confidence Interval": base_pull_ratio_info["Base Pull Ratio 95% Confidence Interval"],
    **base_pull_ratio_info,
    **yaw_info,
    "analysisUrl": f"https://boothinator.github.io/derailleur-analysis/derailleurs/{dir}/default.htm"
  }
  
  with open(f"derailleurs/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)

  today = datetime.date.today()

  run_files = [datafile for datafile in os.listdir(f"derailleurs/{dir}/pullratio") if datafile.endswith('.csv')]

  runs = [{
    'name': r.replace('.csv', ''),
    'chart': 'pullratio/'+r.replace('.csv', '.png'),
    'csvFile': 'pullratio/' + r
  } for r in run_files]

  coefficients_str = f"{info_out['coefficients'][0]:.2f}, {info_out['coefficients'][1]:.3f}, {info_out['coefficients'][2]:.5f}, {info_out['coefficients'][3]:.6f}"

  info_render = {
    **info_out,
    "coefficients": coefficients_str
  }

  output = template.render(year=str(today.year), generation_date=str(today),
                           info=info_render, runs=runs)
  
  with open(f"derailleurs/{dir}/default.htm", 'w') as f:
    print(output, file = f)

  return info_out


with open(f"other_derailleurs.json") as f:
  all_info = json.load(f)

meas_method_percent_diffs = []

for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "Shimano Deore M6100":
  #  continue
  if dir != "Campagnolo Ekar":
    continue

  print(dir)

  info_out = process_der(dir)
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