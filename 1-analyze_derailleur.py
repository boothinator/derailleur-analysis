import csv
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import datetime
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = environment.get_template("derailleur_analysis.htm")

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
        row[key] = np.nan
      else:
        try:
          row[key] = float(row[key])
        except:
          # Ignore failed conversion attempts
          pass
    
  # Get run values
  extrusion_to_carriage_slack = data[0]["Distance from outside of extrusion to carriage when cable is slack (mm)"]
  extrusion_to_carriage_max_pull = data[0]["Distance from outside of extrusion to carriage at max pull (mm)"]

  jockey_wheel_center_at_full_slack=extrusion_to_carriage_slack - carriage_to_jockey_wheel - extrusion_thickness - jockey_wheel_thickness/2


  # Calculate additional columns

  # I didn't used to record the exact puller location. If there's no puller data,
  # calculate it as the row number / 3
  calculate_puller_meas = len([1 for row in data
                               if "Puller Meas. (neg) (mm)" in row
                                  and not np.isnan(row["Puller Meas. (neg) (mm)"])
                                  and "Puller Meas. (mm)" not in row]) == 0

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
      if "pulling" in input_file.lower():
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
  
  plt.plot(cable_pull_meas,jockey_position_meas)
  plt.xlim([cable_pull_meas[0]-1, cable_pull_meas[-1] + 1 ])
  graph_file = input_file.replace('.csv', '_meas.png')
  plt.savefig(graph_file)
  plt.close()

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

  info = {
    "coef": [x for x in result.convert().coef],
    "extrusion_to_carriage_slack": extrusion_to_carriage_slack,
    "extrusion_to_carriage_max_pull": extrusion_to_carriage_max_pull,
    "max_pull": cable_pull_raw.max(),
    "number_of_measurements": len(data)
  }

  plt.plot(cable_pull_raw,jockey_position_raw,'o', x_new, y_new)
  plt.xlim([cable_pull_raw[0]-1, cable_pull_raw[-1] + 1 ])

  graph_file = input_file.replace('.csv', '.png')

  plt.savefig(graph_file)
  plt.close()

  with open(input_file.replace('.csv', '.json'), "w") as infofile:
    json.dump(info, infofile, indent=2)
  
  return info

class PullRatioInfo(BaseModel):
  dropout_width: float
  small_cog_offset: float
  small_cog_position: float
  smallest_cog_pull: float
  second_smallest_cog_pull: float
  second_biggest_cog_pull: float
  biggest_cog_pull: float
  biggest_cog_position: float
  total_pitch_inner_cogs: float
  pull_ratio: float
  coefficients: list[float]


def calc_pull_ratio(info, coefficients, max_pull):
  if "minDropoutWidth" in info and info["minDropoutWidth"] != None \
    and "maxDropoutWidth" in info and info["maxDropoutWidth"] != None:
    dropout_width = (info["minDropoutWidth"] + info["maxDropoutWidth"])/2
  else:
    dropout_width = 8
  small_cog_offset = info["smallCogOffset"] if "smallCogOffset" in info and info["smallCogOffset"] != None else 3
  small_cog_position = dropout_width + small_cog_offset
  biggest_cog_position = small_cog_position + info["designCogPitch"] * (info["designSpeeds"] - 1)
  second_smallest_cog_position = info["designCogPitch"] + small_cog_position

  total_pitch_inner_cogs = info["designCogPitch"] * (info["designSpeeds"] - 3)

  second_biggest_cog_position = second_smallest_cog_position + total_pitch_inner_cogs

  curve = np.polynomial.polynomial.Polynomial(coefficients)

  smallest_cog_pull = [r for r in (curve - small_cog_position).roots() if r >= 0][0]
  if smallest_cog_pull > max_pull:
    print(f"Warning: smallest_cog_pull {smallest_cog_pull} > max_pull {max_pull}", (curve - small_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)

  second_smallest_cog_pull = [r for r in (curve - second_smallest_cog_position).roots() if r >= 0][0]
  if second_smallest_cog_pull > max_pull:
    print(f"Warning: second_smallest_cog_pull {second_smallest_cog_pull} > max_pull {max_pull}", (curve - second_smallest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)
  
  second_biggest_cog_pull = [r for r in (curve - second_biggest_cog_position).roots() if r >= 0][0]
  if second_biggest_cog_pull > max_pull:
    print(f"Warning: second_biggest_cog_pull {second_biggest_cog_pull} > max_pull {max_pull}",(curve - second_biggest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)

  biggest_cog_pull = [r for r in (curve - biggest_cog_position).roots() if r >= 0][0]
  if biggest_cog_pull > max_pull:
    print(f"Warning: biggest_cog_pull {biggest_cog_pull} > max_pull {max_pull}",(curve - biggest_cog_position).roots())
    print("dropout_width", dropout_width)
    print("small_cog_offset", small_cog_offset)
  

  pull_ratio = total_pitch_inner_cogs/(second_biggest_cog_pull - second_smallest_cog_pull)

  return PullRatioInfo(
    dropout_width=dropout_width,
    small_cog_offset=small_cog_offset,
    small_cog_position=small_cog_position,
    smallest_cog_pull=smallest_cog_pull,
    second_smallest_cog_pull=second_smallest_cog_pull,
    second_biggest_cog_pull=second_biggest_cog_pull,
    biggest_cog_pull=biggest_cog_pull,
    biggest_cog_position=biggest_cog_position,
    total_pitch_inner_cogs=total_pitch_inner_cogs,
    pull_ratio=pull_ratio,
    coefficients=curve.convert().coef
    )

def process_der(dir):
  
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  coefs = []
  max_pulls = []

  run_types = []
  run_files = []

  number_of_measurements = 0

  for datafile in os.listdir(f"derailleurs/{dir}/pullratio"):
    if datafile.endswith('.csv'):
      print(f"Processing {datafile}")
      run_files.append(datafile)
      result = analyze(f"derailleurs/{dir}/pullratio/{datafile}", info["jockeyWheelThickness"], info["distanceFromCarriageToJockeyWheel"])
      coefs.append(result["coef"])
      max_pulls.append(result["max_pull"])
      number_of_measurements = number_of_measurements + result["number_of_measurements"]

      if datafile.lower().find("pulling") >= 0:
        run_types.append('pulling')
      elif datafile.lower().find("relaxing") >= 0:
        run_types.append('relaxing')
      else:
        raise Exception(f"File {datafile} not pulling or relaxing!")
    
  coefs = np.array(coefs)
  max_pull = np.mean(max_pulls)

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
  plt.savefig(f"derailleurs/{dir}/pull_curve.png")
  
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
  avg_pull_ratio_annotation_x = np.min([r for r in (pull_ratio_curve_prime - pr_calc.pull_ratio).roots() if r > 0])
  plt.annotate(f"Avg. Pull Ratio {round(pr_calc.pull_ratio, 2)}",
                 (avg_pull_ratio_annotation_x, pr_calc.pull_ratio),
                 xytext=(0, -12), textcoords="offset points")
  plt.savefig(f"derailleurs/{dir}/pull_ratio_curve.png")


  info_out = {**info,
              "pullRatio": pr_calc.pull_ratio,
              "coefficients": [c for c in avg_coefs],
              "physicalLowLimit": curve(0),
              "physicalHighLimit": curve(max_pull),
              "numberOfMeasurements": number_of_measurements,
              "Pull Ratio Averaged Across Pulling Runs": f"{round(pulling_pull_ratio_avg, 3):.3f} +/- {round(2*pulling_pull_ratio_stdev, 3):.3f}",
              "Pull Ratio Averaged Across Relaxing Runs": f"{round(relaxing_pull_ratio_avg, 3):.3f} +/- {round(2*relaxing_pull_ratio_stdev, 3):.3f}",
              "Pull Ratio Averaged Across All Runs": f"{round(pull_ratio_avg, 3):.3f} +/- {round(2*pull_ratio_stdev, 3):.3f}",
              "Pull Ratio 95% Confidence Interval": f"{round(pull_ratio_avg - 2 * pull_ratio_stdev, 3):.3f} to {round(pull_ratio_avg + 2 * pull_ratio_stdev, 3):.3f}",
              "analysisUrl": f"https://boothinator.github.io/derailleur-analysis/derailleurs/{dir}/default.htm"
              }
  
  with open(f"derailleurs/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)

  today = datetime.date.today()

  runs = [{
    'name': r.replace('.csv', ''),
    'chart': 'pullratio/'+r.replace('.csv', '.png'),
    'csvFile': 'pullratio/' + r
  } for r in run_files]

  info_render = {
    **info_out,
    "coefficients": coefficients_str
  }

  output = template.render(year=str(today.year), generation_date=str(today),
                           info=info_render, runs=runs)
  
  with open(f"derailleurs/{dir}/default.htm", 'w') as f:
    print(output, file = f)

  return info_out


with open(f"other_derailleurs.json") as f:
  all_info = json.load(f)

for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "SRAM Apex 11-Speed":
  #  continue
  if dir != "Campagnolo Ekar":
    continue

  print(dir)

  info_out = process_der(dir)
  all_info.append(info_out)

with open(f"all_derailleurs.json", "w") as info_file:
  json.dump(all_info, info_file, indent=2)