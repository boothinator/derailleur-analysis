import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math
from util import convert_to_floats, calc_pull_ratio

extrusion_thickness=19.93

with open("overall_stats.json") as f:
  overall_stats = json.load(f)

def analyze(info, input_file):
  
  jockey_wheel_thickness=info["jockeyWheelThickness"]
  carriage_to_jockey_wheel=info["distanceFromCarriageToJockeyWheel"]
  direction = "pulling" if "pulling" in input_file.lower() else "relaxing"

  data = []

  with open(input_file, newline='') as csvfile: 
    reader = csv.DictReader(csvfile)
    for row in reader:
      data.append(row)

  convert_to_floats(data)
    
  # Get run values
  extrusion_to_carriage_slack = ([d["Distance from outside of extrusion to carriage when cable is slack (mm)"] for d in data
                                 if not np.isnan(d["Distance from outside of extrusion to carriage when cable is slack (mm)"])] or [np.nan])[0]
  extrusion_to_carriage_max_pull = ([d["Distance from outside of extrusion to carriage at max pull (mm)"] for d in data
                                 if not np.isnan(d["Distance from outside of extrusion to carriage at max pull (mm)"])] or [np.nan])[0]

  jockey_wheel_center_at_full_slack=extrusion_to_carriage_slack - carriage_to_jockey_wheel - extrusion_thickness - jockey_wheel_thickness/2


  # Calculate additional columns

  # I didn't used to record the exact puller location. If there's no puller data,
  # calculate it as the row number / 3
  calculate_puller_meas = len([1 for row in data
                               if (
                                    "Puller Meas. (neg) (mm)" in row
                                    and not np.isnan(row["Puller Meas. (neg) (mm)"])
                                  )
                                  or 
                                  (
                                    "Puller Meas. (mm)" in row
                                    and not np.isnan(row["Puller Meas. (mm)"]))
                                  ]) == 0

  prev_row = {
    "Puller Indicator After Move (neg) (mm)": np.nan,
    "Puller Meas. (neg) (mm)": 0,
    "Puller Indicator Offset (mm)": 0,
    "Carriage Indicator After Move (mm)": np.nan,
    "Carriage Meas. (mm)": 0,
    "Carriage Indicator Offset (mm)": 0
  }
  for i, row in enumerate(data):
    # Negate values if needed
    if "Puller Meas. (mm)" in row:
      row["Puller Meas. (neg) (mm)"] = -row["Puller Meas. (mm)"]
    
    if "Puller Indicator After Move (mm)" in row:
      row["Puller Indicator After Move (neg) (mm)"] = -row["Puller Indicator After Move (mm)"]

    if np.isnan(prev_row["Puller Indicator After Move (neg) (mm)"]):
      row["Puller Indicator Offset (mm)"] = prev_row["Puller Indicator Offset (mm)"]
    else:    
      row["Puller Indicator Offset (mm)"] = prev_row["Puller Meas. (neg) (mm)"] \
                                            - prev_row["Puller Indicator After Move (neg) (mm)"]
    
    if np.isnan(prev_row["Carriage Indicator After Move (mm)"]):
      row["Carriage Indicator Offset (mm)"] = prev_row["Carriage Indicator Offset (mm)"]
    else:
      row["Carriage Indicator Offset (mm)"] = prev_row["Carriage Meas. (mm)"]\
                                              - prev_row["Carriage Indicator After Move (mm)"]
    
    if calculate_puller_meas:
      # Pulling
      if direction == "pulling":
        row["Cable Pull (mm)"] = i / 3
      else:
        # Relaxing
        row["Cable Pull (mm)"] = -i / 3
    else:
      row["Cable Pull (mm)"] = row["Puller Meas. (neg) (mm)"] + row["Puller Indicator Offset (mm)"]
    row["Jockey Position (mm)"] = row["Carriage Meas. (mm)"] + row["Carriage Indicator Offset (mm)"] \
                                  + jockey_wheel_center_at_full_slack
    
    prev_row = row

  data_sorted = sorted(data, key=lambda row: row["Cable Pull (mm)"])
  
  cable_pull_meas = [d["Cable Pull (mm)"] for d in data_sorted]
  jockey_position_meas = [d["Jockey Position (mm)"] for d in data_sorted]
  
  plt.clf()
  plt.plot(cable_pull_meas,jockey_position_meas)
  plt.xlim([cable_pull_meas[0]-1, cable_pull_meas[-1] + 1 ])
  graph_file = input_file.replace('.csv', '_meas.png')
  plt.savefig(graph_file)
  plt.close()

  # Double check jockey position range
  jockey_caliper_meas_range = extrusion_to_carriage_max_pull - extrusion_to_carriage_slack
  jockey_indicator_meas_range = max(jockey_position_meas) - min(jockey_position_meas)
  if math.isnan(jockey_caliper_meas_range):
    meas_method_percent_diff = math.nan
  else:
    meas_method_percent_diff = 100 * (jockey_caliper_meas_range - jockey_indicator_meas_range) / jockey_indicator_meas_range
    if meas_method_percent_diff > overall_stats["avg_meas_method_percent_diff"] + 2 * overall_stats["stdev_meas_method_percent_diff"] \
        or meas_method_percent_diff < overall_stats["avg_meas_method_percent_diff"] - 2 * overall_stats["stdev_meas_method_percent_diff"]:
      print(f"Warning: Caliper vs Indicator range mismatch: {meas_method_percent_diff}. caliper range: {jockey_caliper_meas_range}, indicator range: {jockey_indicator_meas_range}")

  # Get cable pull and jockey position data
  cable_pull_raw = cable_pull = np.array([d["Cable Pull (mm)"] for d in data_sorted])
  jockey_position = np.array([d["Jockey Position (mm)"] for d in data_sorted])

  jockey_position_raw = jockey_position = jockey_position - jockey_position.min() + jockey_wheel_center_at_full_slack

  # Calculate point-by-point differences for outliers calculation
  jockey_position_diffs = jockey_position[1:] - jockey_position[:-1]

  average_jockey_position_diff = np.mean(jockey_position_diffs)

  # Find end of low outliers
  low_outlier_cutoff = average_jockey_position_diff * 0.8

  low_cutoff_index = 0

  for (i,d) in enumerate(jockey_position_diffs):
    if d < low_outlier_cutoff:
      low_cutoff_index = i
    else:
      break

  # Find end of high outliers
  high_outlier_cutoff = average_jockey_position_diff * 0.6

  if "Exclude Cable Pull Greater Than (mm)" in data[0] \
        and not np.isnan(data[0]["Exclude Cable Pull Greater Than (mm)"]):
    exclude_cable_pull_greater_than = data[0]["Exclude Cable Pull Greater Than (mm)"] \
                                        + cable_pull[low_cutoff_index]
    high_cutoff_index = low_cutoff_index + np.min([i for i,p in enumerate(cable_pull[low_cutoff_index:])
                                if p > exclude_cable_pull_greater_than])
  else:
    high_cutoff_index = len(jockey_position)

    for (i,d) in reversed([e for e in enumerate(jockey_position_diffs)]):
      if d < high_outlier_cutoff:
        high_cutoff_index = i + 2
      else:
        break

  cable_pull = cable_pull[low_cutoff_index:high_cutoff_index]
  jockey_position = jockey_position[low_cutoff_index:high_cutoff_index]

  # Adjust cable pull start
  cable_pull_raw = cable_pull_raw - cable_pull.min()
  cable_pull = cable_pull - cable_pull.min()

  result = np.polynomial.Polynomial.fit(cable_pull, jockey_position, 3)
  x_new = np.linspace(cable_pull[0], cable_pull[-1], 50)
  y_new = result(x_new)

  coef = [x for x in result.convert().coef]
  max_pull = cable_pull_raw.max()

  pull_ratio_calc = calc_pull_ratio(info, coef, max_pull)

  result_info = {
    "coef": coef,
    "extrusion_to_carriage_slack": extrusion_to_carriage_slack,
    "extrusion_to_carriage_max_pull": extrusion_to_carriage_max_pull,
    "max_pull": max_pull,
    "direction": direction,
    "pull_ratio": pull_ratio_calc.pull_ratio,
    "pull_ratio_calc": pull_ratio_calc.model_dump(),
    "number_of_measurements": len(data),
    "meas_method_percent_diff": meas_method_percent_diff,
    
  }

  plt.clf()
  plt.plot(cable_pull_raw,jockey_position_raw,'o', x_new, y_new)
  plt.xlim([cable_pull_raw[0]-1, cable_pull_raw[-1] + 1 ])

  graph_file = input_file.replace('.csv', '.png')

  plt.savefig(graph_file)
  plt.close()

  with open(input_file.replace('.csv', '.json'), "w") as infofile:
    json.dump(result_info, infofile, indent=2)



for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "Shimano Deore M6100":
  #  continue
  if dir != "Campagnolo Ekar":
    continue

  print(dir)

  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)

  for datafile in os.listdir(f"derailleurs/{dir}/pullratio"):
    if datafile.endswith('.csv'):
      print(f"Processing {datafile}")
      analyze(info, f"derailleurs/{dir}/pullratio/{datafile}")
