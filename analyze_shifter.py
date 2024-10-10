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

  # TODO: normalize data and graph

  # Calculate differences
  diffs = np.array([column[:-1] - column[1:] for column in measurement_data.T])

  # Calculate averages
  clean_data = [[c for c in row if not math.isnan(c)] for row in diffs.T]
  averages = [np.mean(row) for row in clean_data]
  stdev = [np.std(row) for row in clean_data]
  print(averages)
  
  


for dir in os.listdir('shifters'):
  with open(f"shifters/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  result = analyze(f"shifters/{dir}/measurements.csv")
