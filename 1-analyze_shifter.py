import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math
import re
import pandas as pd

def convert_to_float(c):
  return float(c) if len(c) > 0 else float('nan')

def analyze(input_file, out_folder):
  data = []
  row_headers = []

  with open(input_file, newline='') as csvfile: 
    reader = csv.reader(csvfile)
    for row in reader:
      data.append(row)
      row_headers.append(row[0])
  
  # Find where measurements start
  gear_headers = [(i, h, m[1]) for i, h, m in 
    [(i,h,re.match(r'^(\d{1,2}).*', h)) for i,h in enumerate(row_headers)]
    if m
  ]
  first_gear_row_index = min([i for i,_,_ in gear_headers])
  last_gear_row_index = max([i for i,_,_ in gear_headers])

  # Create DataFrame
  d = [dict([(row_header, data[row_index][col_index])
             for row_index,row_header in enumerate(row_headers[0:first_gear_row_index])]
             + [('Gear', int(re.match(r'^(\d{1,2}).*', data[gear_row_index][0])[1])),
                ('Gear Label', data[gear_row_index][0]),
                ('Measurement', convert_to_float(data[gear_row_index][col_index]))
                ])
       for col_index in range(1, len(data[0]))
       for gear_row_index in range(first_gear_row_index, last_gear_row_index + 1)]
  df = pd.DataFrame(d)

  sets = sorted(list(set(df["Set"])))

  # Get set averages and normalize data
  set_gear_data = df.groupby(["Set", "Gear"])["Measurement"]
  set_gear_averages = set_gear_data.mean()

  set_gear_average_diffs = [(set, set_gear_averages[set] - set_gear_averages[sets[0]])
                            for set in sets[1:]]

  set_average_diffs = dict([(sets[0], 0)] + [(set, d.mean()) for set, d in set_gear_average_diffs])

  normalized_measurements = df.apply(lambda row: row["Measurement"] - set_average_diffs[row["Set"]], axis=1)

  df["NormalizedMeasurement"] = normalized_measurements.max() - normalized_measurements

  # Plot Averages

  gear_averages = df.groupby(["Gear"], sort=False)["NormalizedMeasurement"].mean().rename("Average")
  pulling_gear_averages = df[df["Direction"] == 'Pulling'].groupby(["Gear"], sort=False)["NormalizedMeasurement"].mean().rename("Average Pulling")
  relaxing_gear_averages = df[df["Direction"] == 'Relaxing'].groupby(["Gear"], sort=False)["NormalizedMeasurement"].mean().rename("Average Relaxing")

  avgs = pd.DataFrame([gear_averages, pulling_gear_averages, relaxing_gear_averages]).T

  avgs.plot.bar()
  plt.ylim(bottom=-1)
  plt.savefig(f"{out_folder}/meas_avgs.png")
  plt.close()

  # Plot Stdev

  gear_stdev = df.groupby(["Gear"], sort=False)["NormalizedMeasurement"].std().rename("Std Dev")
  pulling_gear_stdev = df[df["Direction"] == 'Pulling'].groupby(["Gear"], sort=False)["NormalizedMeasurement"].std().rename("Std Dev Pulling")
  relaxing_gear_stdev = df[df["Direction"] == 'Relaxing'].groupby(["Gear"], sort=False)["NormalizedMeasurement"].std().rename("Std Dev Relaxing")

  avgs = pd.DataFrame([gear_stdev, pulling_gear_stdev, relaxing_gear_stdev]).T

  avgs.plot.bar()
  plt.savefig(f"{out_folder}/meas_stdev.png")
  plt.close()

  # Diff between relaxing and pulling averages
  relaxing_pulling_diffs = pulling_gear_averages - relaxing_gear_averages

  relaxing_pulling_diffs.plot.bar()
  plt.savefig(f"{out_folder}/meas_diffs.png")
  plt.close()

  # Calculate shift amounts by calculating differences between subsequent positions
  # Use MeasurementData to ensure that we wouldn't be affected by problems from normalization
  # Besides, here we only care about differences, not absolute values
  md = df.groupby(["Run"], sort=False)

  shifts_df = md.apply(lambda d: pd.DataFrame(dict(
    [(header, d[header].iloc[:-1])
     for header in row_headers[:first_gear_row_index]
     if header != "Run"]+
    [
      ("GearStep", [f"{d["Gear"].iloc[i]}-{d["Gear"].iloc[i + 1]}" for i in range(d.shape[0] - 1)]),
      ("Shift", d["Measurement"].iloc[:-1].to_numpy()-d["Measurement"].iloc[1:].to_numpy())
    ])), include_groups=False).reset_index()


  # Plot Shift Averages

  shift_averages = shifts_df.groupby(["GearStep"], sort=False)["Shift"].mean()
  pulling_shift_averages = shifts_df[shifts_df["Direction"] == 'Pulling'].groupby(["GearStep"], sort=False)["Shift"].mean().rename("Average Pulling")
  relaxing_shift_averages = shifts_df[shifts_df["Direction"] == 'Relaxing'].groupby(["GearStep"], sort=False)["Shift"].mean().rename("Average Relaxing")

  shift_avgs_df = pd.DataFrame([shift_averages, pulling_shift_averages, relaxing_shift_averages]).T

  shift_avgs_df.plot.bar()
  plt.savefig(f"{out_folder}/shift_avgs.png")
  plt.close()

  # Cable Pull chart

  cable_pull = np.mean(shift_averages[1:-1])

  shift_averages.plot.bar()
  # TODO: plot average line
  plt.savefig(f"{out_folder}/cable_pull.png")
  plt.close()

  # Plot Shift Std Dev

  shift_stdev = shifts_df.groupby(["GearStep"], sort=False)["Shift"].std()
  pulling_shift_stdev = shifts_df[shifts_df["Direction"] == 'Pulling'].groupby(["GearStep"], sort=False)["Shift"].std().rename("Average Pulling")
  relaxing_shift_stdev = shifts_df[shifts_df["Direction"] == 'Relaxing'].groupby(["GearStep"], sort=False)["Shift"].std().rename("Average Relaxing")

  shift_stdevs_df = pd.DataFrame([shift_stdev, pulling_shift_stdev, relaxing_shift_stdev]).T

  plt.clf()
  shift_stdevs_df.plot.bar()
  plt.savefig(f"{out_folder}/shift_stdev.png")
  plt.close()

  # Plot Shift Differences

  shift_relaxing_pulling_diffs = pulling_shift_averages - relaxing_shift_averages

  shift_relaxing_pulling_diffs.plot.bar()
  plt.savefig(f"{out_folder}/shift_diffs.png")
  plt.close()


  return {
    "shiftSpacings": shift_averages.to_list(),
    "cablePull": cable_pull
  }
  

  


for dir in os.listdir('shifters'):
  if dir == "template":
    continue
  
  #FIXME:TESTING
  #if dir != "Shimano Ultegra 6600":
  #  continue

  with open(f"shifters/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  result = analyze(f"shifters/{dir}/measurements.csv", f"shifters/{dir}")

  print(f"{dir}: {result['cablePull']}")

  info_out = {
    **info,
    **result
  }
  
  with open(f"shifters/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)
