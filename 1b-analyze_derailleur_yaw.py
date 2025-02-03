import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math
from util import convert_to_floats
from typing import Iterable

def analyze_yaw(input_file):

  with open(input_file, newline='') as csvfile: 
    reader = csv.DictReader(csvfile)
    data = [*reader]

  convert_to_floats(data)

  # Remove outliers
  data = [row for row in data if not isinstance(row["Is Outlier"], str)]

  for row in data:
    if math.isnan(row["Cable Pull (mm)"]):
      row["Cable Pull (mm)"] = row["180 Deg. Turns"]

  cable_pull = [row["Cable Pull (mm)"] - data[0]["Cable Pull (mm)"] for row in data]
  yaw_angle = [row["Measurement (deg)"] for row in data]

  result = np.polynomial.Polynomial.fit(cable_pull, yaw_angle, 2)
  x_new = np.linspace(cable_pull[0], cable_pull[-1], 50)
  y_new = result(x_new)

  result_info = {
    "coef": [x for x in result.convert().coef],
    "number_of_measurements": len(data)
  }

  plt.clf()
  plt.plot(cable_pull,yaw_angle,'o', x_new, y_new)
  plt.xlim([cable_pull[0]-1, cable_pull[-1] + 1 ])

  graph_file = input_file.replace('.csv', '.png')

  plt.savefig(graph_file)
  plt.close()

  with open(input_file.replace('.csv', '.json'), "w") as infofile:
    json.dump(result_info, infofile, indent=2)

def get_jockey_offset_curve(yaw_angle_curve):
  chain_max_free_yaw = 1.3
  link_length = 12.7

  def calc_yaw_offset_curve(x):
    y = yaw_angle_curve(x)

    if y < -chain_max_free_yaw:
      return math.sin((y + chain_max_free_yaw)/180*math.pi) * link_length
    elif y > chain_max_free_yaw:
      return math.sin((y - chain_max_free_yaw)/180*math.pi) * link_length
    else:
      return 0
  
  def yaw_offset_curve(x):
    if isinstance(x, Iterable):
      return [calc_yaw_offset_curve(_x) for _x in x]
    else:
      return calc_yaw_offset_curve(x)

  return yaw_offset_curve

for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "Shimano Deore M6100":
  #  continue
  if dir != "Campagnolo Ekar":
    continue

  print(dir)

  if os.path.exists(f"derailleurs/{dir}/yaw"):
    for datafile in os.listdir(f"derailleurs/{dir}/yaw"):
      if datafile.endswith('.csv'):
        print(f"Processing {datafile}")

        analyze_yaw(f"derailleurs/{dir}/yaw/{datafile}")