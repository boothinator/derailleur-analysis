import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math
from util import calc_pull_ratio

def process_der(dir):
  
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  coefs = []
  max_pulls = []

  run_types = []
  run_files = []

  number_of_measurements = 0
  meas_method_percent_diffs = []

  for datafile in os.listdir(f"derailleurs/{dir}/pullratio"):
    if datafile.endswith('.csv'):
      datafile_json = datafile.replace(".csv", ".json")
      run_files.append(datafile_json)
      with open(f"derailleurs/{dir}/pullratio/{datafile_json}") as f:
        result = json.load(f)
      coefs.append(result["coef"])
      max_pulls.append(result["max_pull"])
      number_of_measurements = number_of_measurements + result["number_of_measurements"]
      
      if not math.isnan(result["meas_method_percent_diff"]):
        meas_method_percent_diffs.append(result["meas_method_percent_diff"])

      if datafile.lower().find("pulling") >= 0:
        run_types.append('pulling')
      elif datafile.lower().find("relaxing") >= 0:
        run_types.append('relaxing')
      else:
        raise Exception(f"File {datafile} not pulling or relaxing!")
    
  coefs = np.array(coefs)
  max_pull = np.mean(max_pulls)
  avg_meas_method_percent_diff = np.mean(meas_method_percent_diffs) if len(meas_method_percent_diffs) else math.nan
  stdev_meas_method_percent_diff = np.std(meas_method_percent_diffs) if len(meas_method_percent_diffs) else math.nan

  run_pr_calcs = []
  for c,file in zip(coefs, run_files):
    try:
      run_pr_calcs.append(calc_pull_ratio(info, c, max_pull))
    except Exception as ex:
      raise Exception(f"Error calculating pull ratio for {file}: {ex}")

  pulling_pr_calcs = [c for t, c in zip(run_types, run_pr_calcs) if t == 'pulling']
  relaxing_pr_calcs = [c for t, c in zip(run_types, run_pr_calcs) if t == 'relaxing']

  pulling_pull_ratio_avg = np.mean([c.pull_ratio for c in pulling_pr_calcs])
  pulling_pull_ratio_stdev = np.std([c.pull_ratio for c in pulling_pr_calcs])

  relaxing_pull_ratio_avg = np.mean([c.pull_ratio for c in relaxing_pr_calcs])
  relaxing_pull_ratio_stdev = np.std([c.pull_ratio for c in relaxing_pr_calcs])

  pull_ratio_avg = np.mean([c.pull_ratio for c in run_pr_calcs])
  pull_ratio_stdev = np.std([c.pull_ratio for c in run_pr_calcs])

  avg_coefs = np.mean(coefs.T, 1)

  # Calculate pull ratio
  pr_calc = calc_pull_ratio(info, avg_coefs, max_pull)

  curve = np.polynomial.polynomial.Polynomial(pr_calc.coefficients)
  
  coefficients_str = f"{pr_calc.coefficients[0]:.2f}, {pr_calc.coefficients[1]:.3f}, {pr_calc.coefficients[2]:.5f}, {pr_calc.coefficients[3]:.6f}"
  print(f"Best Fit Curve Coefficients: {coefficients_str}")

  print(f"Pull Ratio of Best Fit Curve: {round(pr_calc.pull_ratio, 3):.3f}")

  if round(pr_calc.pull_ratio/2, 2) != round(pull_ratio_avg/2, 2):
    raise Exception("Pull ratio of best fit curve not the same as the average over all runs!")
  
  x_new = np.linspace(0, max_pull, 50)
  y_new = curve(x_new)
  
  plt.clf()
  plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([0, curve(max_pull) + 10])
  plt.savefig(f"derailleurs/{dir}/base_pull_curve.png")
  plt.close()
  
  pull_ratio_curve = curve.deriv(1)
  pull_ratio_curve_prime = curve.deriv(1)
  x_new = np.linspace(0, max_pull, 50)
  y_new = pull_ratio_curve(x_new)

  x_pr = [pr_calc.smallest_cog_pull, pr_calc.biggest_cog_pull]
  y_pr = [pr_calc.pull_ratio, pr_calc.pull_ratio]

  x_cogs = [pr_calc.second_smallest_cog_pull, pr_calc.second_biggest_cog_pull]
  y_cogs = [pr_calc.pull_ratio, pr_calc.pull_ratio]
  
  plt.clf()
  plt.plot(x_new, y_new, x_pr, y_pr, x_cogs, y_cogs, "o")
  plt.xlim([0, max_pull])
  plt.ylim([0, pr_calc.pull_ratio*1.4])
  plt.xlabel("Cable Pull (mm)")
  plt.ylabel("Pull Ratio")
  plt.title(f"{info['brand']} {info['name']} {info['designSpeeds']}-speed Derailleur Pull Ratio")
  avg_pull_ratio_annotation_x = np.min([r for r in (pull_ratio_curve_prime - pr_calc.pull_ratio).roots() if r > 0])
  plt.annotate(f"Avg. Pull Ratio {round(pr_calc.pull_ratio, 2)}",
                 (avg_pull_ratio_annotation_x, pr_calc.pull_ratio),
                 xytext=(0, -12), textcoords="offset points")
  plt.savefig(f"derailleurs/{dir}/base_pull_ratio_curve.png")
  plt.close()

  # Info Output
  info_out = {
    "basePullRatio": pr_calc.pull_ratio,
    "maxPull": max_pull,
    "coefficients": [c for c in avg_coefs],
    "physicalLowLimit": curve(0),
    "physicalHighLimit": curve(max_pull),
    "numberOfMeasurements": number_of_measurements,
    "Base Pull Ratio Averaged Across Pulling Runs": f"{round(pulling_pull_ratio_avg, 3):.3f} +/- {round(2*pulling_pull_ratio_stdev, 3):.3f}",
    "Base Pull Ratio Averaged Across Relaxing Runs": f"{round(relaxing_pull_ratio_avg, 3):.3f} +/- {round(2*relaxing_pull_ratio_stdev, 3):.3f}",
    "Base Pull Ratio Averaged Across All Runs": f"{round(pull_ratio_avg, 3):.3f} +/- {round(2*pull_ratio_stdev, 3):.3f}",
    "Base Pull Ratio 95% Confidence Interval": f"{round(pull_ratio_avg - 2 * pull_ratio_stdev, 3):.3f} to {round(pull_ratio_avg + 2 * pull_ratio_stdev, 3):.3f}",
    "meas_method_percent_diffs": meas_method_percent_diffs,
    "Caliper vs Indicator percent difference": f"Caliper vs Indicator percent difference: {avg_meas_method_percent_diff} +/- {stdev_meas_method_percent_diff * 2}",
    "pullRatioCalc": pr_calc.model_dump()
  }
  
  with open(f"derailleurs/{dir}/pullratio/base_pull_ratio_info.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)


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
