from typing import Iterable
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import math
# TODO:
# Calculate yaw stats, combined yaw curve, pull ratio from yaw, and pull and pull ratio curve for yaw and put in yaw folder

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

# TODO: create get_jockey_offset_speed_curve(), differentiating using chain rule

def process_der_yaw(dir):
  
  coefs = []
  number_of_measurements = 0

  with open(f"derailleurs/{dir}/pullratio/base_pull_ratio_info.json") as f:
    base_pull_ratio_info = json.load(f)

  max_pull = base_pull_ratio_info["maxPull"]

  if os.path.exists(f"derailleurs/{dir}/yaw"):
    for datafile in os.listdir(f"derailleurs/{dir}/yaw"):
      if datafile.endswith('.csv'):
        print(f"Processing {datafile}")

        datafile_json = datafile.replace(".csv", ".json")

        with open(f"derailleurs/{dir}/yaw/{datafile_json}") as f:
          result = json.load(f)
        
        coefs.append(result["coef"])
        number_of_measurements = number_of_measurements + result["number_of_measurements"]

  coefs = np.array(coefs)
  
  avg_coefs = np.mean(coefs.T, 1)

  curve = np.polynomial.polynomial.Polynomial(avg_coefs)

  x_new = np.linspace(0, max_pull, 50)
  y_new = curve(x_new)
  
  plt.clf()
  plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([curve(0) - 1, curve(max_pull) + 1])
  plt.savefig(f"derailleurs/{dir}/yaw_curve.png")
  plt.close()
  
  jockey_offset_curve = get_jockey_offset_curve(curve)
  
  plt.clf()
  plt.plot(x_new, [jockey_offset_curve(x) for x in x_new])
  plt.xlim([0, max_pull])
  plt.ylim([jockey_offset_curve(0) - 0.2, jockey_offset_curve(max_pull) + 0.2])
  plt.savefig(f"derailleurs/{dir}/effective_jockey_offset_from_yaw_curve.png")
  plt.close()

  info_out = {
    "yawCoefficients": [*avg_coefs],
    "yawNumberOfMeasurements": number_of_measurements
  }

  with open(f"derailleurs/{dir}/yaw/yaw_info.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)


for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "Shimano Deore M6100":
  #  continue
  if dir != "Campagnolo Ekar":
    continue

  print(dir)

  process_der_yaw(dir)

