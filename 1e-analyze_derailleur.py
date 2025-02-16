import numpy as np
import os
import json
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = environment.get_template("derailleur_analysis.htm")

with open("overall_stats.json") as f:
  overall_stats = json.load(f)

def process_der(dir):
  
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  with open(f"derailleurs/{dir}/pullratio/pull_ratio_info.json") as info_file:
    pull_ratio_info = json.load(info_file)
  
  if os.path.exists(f"derailleurs/{dir}/yaw/yaw_info.json"):
    with open(f"derailleurs/{dir}/yaw/yaw_info.json") as info_file:
      yaw_info = json.load(info_file)
  else:
    yaw_info = {}
  
  # Info Output
  info_out = {
    **info,
    **pull_ratio_info,
    **yaw_info,
    "analysisUrl": f"https://boothinator.github.io/derailleur-analysis/derailleurs/{dir}/default.htm"
  }
  
  with open(f"derailleurs/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)

  # Render info page
  # TODO: update pages to show yaw info
  today = datetime.date.today()

  run_files = [datafile for datafile in os.listdir(f"derailleurs/{dir}/pullratio") if datafile.endswith('.csv')]

  runs = [{
    'name': r.replace('.csv', ''),
    'chart': 'pullratio/'+r.replace('.csv', '.png'),
    'csvFile': 'pullratio/' + r
  } for r in run_files]

  if os.path.exists(f"derailleurs/{dir}/yaw"):
    yaw_run_files = [datafile for datafile in os.listdir(f"derailleurs/{dir}/yaw") if datafile.endswith('.csv')]
  else:
    yaw_run_files = []

  yaw_runs = [{
    'name': r.replace('.csv', ''),
    'chart': 'yaw/'+r.replace('.csv', '.png'),
    'csvFile': 'yaw/' + r
  } for r in yaw_run_files]

  coefficients_str = f"{info_out['coefficients'][0]:.2f}, {info_out['coefficients'][1]:.3f}, {info_out['coefficients'][2]:.5f}, {info_out['coefficients'][3]:.6f}"

  info_render = {
    **info_out,
    "coefficients": coefficients_str
  }

  output = template.render(year=str(today.year), generation_date=str(today),
                           info=info_render, runs=runs, yaw_runs=yaw_runs)
  
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
  #if dir != "Campagnolo Ekar":
  #  continue

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