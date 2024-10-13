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

def analyze(input_file):
  data = []
  row_headers = []

  with open(input_file, newline='') as csvfile: 
    reader = csv.reader(csvfile)
    for row in reader:
      data.append(row)
      row_headers.append(row[0])
  
  set_row_index = row_headers.index("Set")
  direction_row_index = row_headers.index("Direction")
  
  # Find where measurements start
  gear_headers = [(i, h, m[1]) for i, h, m in 
    [(i,h,re.match(r'^(\d{1,2}).*', h)) for i,h in enumerate(row_headers)]
    if m
  ]
  first_gear_row_index = min([i for i,_,_ in gear_headers])
  last_gear_row_index = max([i for i,_,_ in gear_headers])
  
  # Extract just the measurements and convert to numbers
  measurement_data = [
    [(float(c) if len(c) > 0 else float('nan')) for c in row[1:]]
    for row in data[first_gear_row_index:last_gear_row_index+1]
  ]

  # Create DataFrame
  d = [dict([(row_header, data[row_index][col_index])
             for row_index,row_header in enumerate(row_headers[0:first_gear_row_index])]
             + [('Gear', int(re.match(r'^(\d{1,2}).*', data[gear_row_index][0])[1])),
                ('Measurement', convert_to_float(data[gear_row_index][col_index]))
                ])
       for col_index in range(1, len(data[0]))
       for gear_row_index in range(first_gear_row_index, last_gear_row_index + 1)]
  df = pd.DataFrame(d)

  sets = sorted(list(set(df["Set"])))

  # Get set averages
  set_gear_averages = df.groupby(["Set", "Gear"])["Measurement"].mean()

  set_average_diffs = [set_gear_averages[set] - set_gear_averages[sets[0]] for set in sets[1:]]


  # TODO: graph, diff between pulling and relaxing, average pulling, average relaxing
  # TODO: normalize, make queryable
  set_row = data[set_row_index][1:]
  set_numbers = sorted(list(set(set_row)))

  set_col_indexes = [(set, [i for i,s in enumerate(set_row) if s == set]) for set in set_numbers]

  set_measurement_data = [
    (set, [[val for i,val in enumerate(row) if i in indexes] for row in measurement_data])
    for set,indexes in set_col_indexes
  ]

  set_row_averages = [(sd[0], np.array([np.mean([v for v in row if not np.isnan(v)]) for row in sd[1]]))
                  for sd in set_measurement_data]
  
  row_avg_diffs = [set_row_averages[set_index][1] - set_row_averages[0][1]
                   for set_index in range(1, len(set_row_averages))]
  
  avg_set_diffs = [0] + [np.mean([d for d in row_diffs if not np.isnan(d)])
                         for row_diffs in row_avg_diffs]
  
  normalized_set_data = [(set, np.array(data) - avg_set_diffs[i])
                                 for i,(set,data) in enumerate(set_measurement_data)]
  
  normalized_measurement_data = [
    np.array([ normalized_set_data[set_index][1][row_index] for set_index in range(len(set_numbers))]).flatten()
    for row_index in range(len(measurement_data))]
  
  clean_normalized_row_data = [[c for c in row if not math.isnan(c)] for row in normalized_measurement_data]

  min_clean_normalized_row_data = min([min(row) for row in clean_normalized_row_data])

  clean_normalized_row_data = [[c - min_clean_normalized_row_data for c in row] for row in clean_normalized_row_data]
  
  row_averages = [np.mean(row) for row in clean_normalized_row_data]
  row_stdevs = [np.std(row) for row in clean_normalized_row_data]

  plt.clf()
  plt.plot(row_stdevs, "o")
  plt.show()

  # Calculate differences
  diffs = np.array([column[:-1] - column[1:] for column in np.array(measurement_data).T])

  #TODO: diff between pulling and relaxing, average pulling, average relaxing, 95% confidence interval

  # Calculate averages
  clean_data = [[c for c in row if not math.isnan(c)] for row in diffs.T]
  averages = [np.mean(row) for row in clean_data]
  stdev = [np.std(row) for row in clean_data]
  print(len(averages[1:-1]))
  print(averages[1:-1])
  cable_pull = np.mean(averages[1:-1])

  print(cable_pull)

  # TODO: generate cable pull graph

  return {
    "shiftSpacings": averages,
    "cablePull": cable_pull
  }
  

  


for dir in os.listdir('shifters'):
  if dir == "template":
    continue
  
  #FIXME:TESTING
  if dir != "Microshift Advent X":
    continue

  with open(f"shifters/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  result = analyze(f"shifters/{dir}/measurements.csv")

  info_out = {
    **info,
    **result
  }
  
  with open(f"shifters/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)
