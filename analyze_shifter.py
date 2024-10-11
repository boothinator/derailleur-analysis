import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math

def analyze(input_file):
  data = []

  with open(input_file, newline='') as csvfile: 
    reader = csv.reader(csvfile)
    for row in reader:
      data.append(row)
  
  # Extract just the measurements and convert to numbers
  measurement_data = np.array([
    [(float(c) if len(c) > 0 else float('nan')) for c in row[1:]]
    for row in data[4:]
  ])

  # TODO: normalize data between runs
  # todo: graph, diff between pulling and relaxing, average pulling, average relaxing

  # Calculate differences
  diffs = np.array([column[:-1] - column[1:] for column in measurement_data.T])

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
  with open(f"shifters/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  result = analyze(f"shifters/{dir}/measurements.csv")

  info_out = {
    **info,
    **result
  }
  
  with open(f"shifters/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)
