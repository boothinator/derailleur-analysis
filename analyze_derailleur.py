import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import json

extrusion_thickness=19.93

def analyze(input_file, jockey_wheel_thickness, carriage_to_jockey_wheel):

  data = []

  with open(input_file, newline='') as csvfile: 
    reader = csv.DictReader(csvfile)
    for row in reader:
      data.append(row)

  # Convert to numbers
  for row in data:
    for key in row.keys():
      if len(row[key]) == 0:
        row[key] = 0
      else:
        row[key] = float(row[key])
    
  # Get run values
  extrusion_to_carriage_slack = data[0]["Distance from outside of extrusion to carriage when cable is slack (mm)"]
  extrusion_to_carriage_max_pull = data[0]["Distance from outside of extrusion to carriage at max pull (mm)"]

  jockey_wheel_center_at_full_slack=extrusion_to_carriage_slack - carriage_to_jockey_wheel - extrusion_thickness - jockey_wheel_thickness/2


  # Calculate additional columns

  prev_row = {
    "Puller Indicator After Move (neg) (mm)": 0,
    "Puller Meas. (neg) (mm)": 0,
    "Puller Indicator Offset (mm)": 0,
    "Carriage Indicator After Move (mm)": 0,
    "Carriage Meas. (mm)": 0,
    "Carriage Indicator Offset (mm)": 0
  }
  for row in data:
    if prev_row["Puller Indicator After Move (neg) (mm)"] == 0:
      row["Puller Indicator Offset (mm)"] = prev_row["Puller Indicator Offset (mm)"]
    else:    
      row["Puller Indicator Offset (mm)"] = prev_row["Puller Meas. (neg) (mm)"] \
                                            - prev_row["Puller Indicator After Move (neg) (mm)"]
    
    if prev_row["Carriage Indicator After Move (mm)"] == 0:
      row["Carriage Indicator Offset (mm)"] = prev_row["Carriage Indicator Offset (mm)"]
    else:
      row["Carriage Indicator Offset (mm)"] = prev_row["Carriage Meas. (mm)"]\
                                              - prev_row["Carriage Indicator After Move (mm)"]
    
    row["Cable Pull (mm)"] = row["Puller Meas. (neg) (mm)"] + row["Puller Indicator Offset (mm)"]
    row["Jockey Position (mm)"] = row["Carriage Meas. (mm)"] + row["Carriage Indicator Offset (mm)"] \
                                  + jockey_wheel_center_at_full_slack
    
    prev_row = row

  # Get cable pull and jockey position data
  cable_pull_raw = cable_pull = np.sort(np.array([d["Cable Pull (mm)"] for d in data]))
  jockey_position = np.sort(np.array([d["Jockey Position (mm)"] for d in data]))

  jockey_position_raw = jockey_position = jockey_position - jockey_position.min() + jockey_wheel_center_at_full_slack

  # Outliers
  jockey_position_diffs = jockey_position[1:] - jockey_position[:-1]

  average_jockey_position_diff = np.mean(jockey_position_diffs)

  low_outlier_cutoff = average_jockey_position_diff * 0.8
  high_outlier_cutoff = average_jockey_position_diff * 0.6

  low_cutoff_index = 0

  for (i,d) in enumerate(jockey_position_diffs):
    if d < low_outlier_cutoff:
      low_cutoff_index = i
    else:
      break

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

  print(result.convert().coef)

  # TODO: make this automatic, and make it work across different runs
  # In fact, I really need to write the code for combining runs
  starting_pull = 4
  ending_pull = 32

  pull_ratio = (result(ending_pull) - result(starting_pull))/(ending_pull - starting_pull)

  print(pull_ratio)

  info = {
    "coef": [x for x in result.convert().coef],
    "extrusion_to_carriage_slack": extrusion_to_carriage_slack,
    "extrusion_to_carriage_max_pull": extrusion_to_carriage_max_pull,
    "max_pull": cable_pull_raw.max()
  }

  plt.clf()
  plt.plot(cable_pull_raw,jockey_position_raw,'o', x_new, y_new)
  plt.xlim([cable_pull_raw[0]-1, cable_pull_raw[-1] + 1 ])

  graph_file = input_file.replace('.csv', '.png')

  plt.savefig(graph_file)

  with open(input_file.replace('.csv', '.json'), "w") as infofile:
    json.dump(info, infofile)
  
  return info

for dir in os.listdir('derailleurs'):
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  coefs = []
  max_pulls = []

  for datafile in os.listdir(f"derailleurs/{dir}/pullratio"):
    if datafile.endswith('.csv'):
      print(datafile)
      result = analyze(f"derailleurs/{dir}/pullratio/{datafile}", info["jockeyWheelThickness"], info["distanceFromCarriageToJockeyWheel"])
      coefs.append(result["coef"])
      max_pulls.append(result["max_pull"])
    
  coefs = np.array(coefs)
  max_pull = np.mean(max_pulls)

  avg_coefs = np.mean(coefs.T, 1)

  # Calculate pull ratio

  dropout_width = (info["minDropoutWidth"] + info["maxDropoutWidth"])/2
  small_cog_offset = info["smallCogOffset"]
  small_cog_position = dropout_width + small_cog_offset
  second_smallest_cog_position = info["designCogPitch"] + small_cog_position

  total_pitch_inner_cogs = info["designCogPitch"] * (info["designSpeeds"] - 3)

  second_biggest_cog_position = second_smallest_cog_position + total_pitch_inner_cogs

  curve = np.polynomial.polynomial.Polynomial(avg_coefs)

  second_smallest_cog_pull = [r for r in (curve - second_smallest_cog_position).roots()
                              if r >= 0 and r < max_pull][0]
  
  second_biggest_cog_pull = [r for r in (curve - second_biggest_cog_position).roots()
                              if r >= 0 and r < max_pull][0]

  pull_ratio = total_pitch_inner_cogs/(second_biggest_cog_pull - second_smallest_cog_pull)
  print(pull_ratio)

  x_new = np.linspace(0, max_pull, 50)
  y_new = curve(x_new)

  info_out = {**info,
              "pullRatio": pull_ratio,
              "coef": [c for c in avg_coefs],
              "minPosition": curve(0),
              "maxPosition": curve(max_pull)
              }
  
  with open(f"derailleurs/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)
  
  plt.clf()
  plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([0, curve(max_pull) + 10])
  plt.savefig(f"derailleurs/{dir}/pull_ratio_curve.png")
