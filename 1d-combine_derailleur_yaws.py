
import numpy as np
import matplotlib.pyplot as plt
import os
import json

from util import get_jockey_offset_curve, get_jockey_offset_rate_curve

def process_der_yaw(dir):
  
  coefs = []
  number_of_measurements = 0

  with open(f"derailleurs/{dir}/pullratio/pull_ratio_info.json") as f:
    pull_ratio_info = json.load(f)

  max_pull = pull_ratio_info["maxPull"]

  if not os.path.exists(f"derailleurs/{dir}/yaw"):
    return
  
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
  y_new = jockey_offset_curve(x_new)
  
  plt.clf()
  plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([jockey_offset_curve(0) - 0.2, jockey_offset_curve(max_pull) + 0.2])
  plt.savefig(f"derailleurs/{dir}/effective_jockey_offset_from_yaw_curve.png")
  plt.close()
  
  jockey_offset_rate_curve = get_jockey_offset_rate_curve(curve)

  y_new = jockey_offset_rate_curve(x_new)
  
  plt.clf()
  plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([jockey_offset_rate_curve(max_pull) - 0.2, jockey_offset_rate_curve(0) + 0.2])
  plt.savefig(f"derailleurs/{dir}/effective_jockey_offset_rate_from_yaw_curve.png")
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
  #if dir != "Campagnolo Ekar":
  #  continue

  print(dir)

  process_der_yaw(dir)

