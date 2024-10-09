import csv
import numpy as np
import matplotlib.pyplot as plt

input_file = 'Campagnolo Ekar 13-Speed Derailleur Ratio - 10_6 11_05 AM Pulling.csv'
#input_file = 'Campagnolo Ekar 13-Speed Derailleur Ratio - 10_6 3_38 pm Relaxing.csv'

data = []

extrusion_to_carriage_slack=67.4
extrusion_to_carriage_max_pull=111.79
jockey_wheel_thickness=1.75
carriage_to_jockey_wheel=36.52

extrusion_thickness=19.93

jockey_wheel_center_at_full_slack=extrusion_to_carriage_slack - carriage_to_jockey_wheel - extrusion_thickness - jockey_wheel_thickness/2

with open(input_file, newline='') as csvfile: 
  reader = csv.DictReader(csvfile)
  for row in reader:
    data.append(row)

header = data[0]
data = data[1:]

# Convert to numbers
for row in data:
  for key in row.keys():
    if len(row[key]) == 0:
      row[key] = 0
    else:
      row[key] = float(row[key])

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
cable_pull = np.sort(np.array([d["Cable Pull (mm)"] for d in data]))
jockey_position = np.sort(np.array([d["Jockey Position (mm)"] for d in data]))

jockey_position = jockey_position - jockey_position.min() + jockey_wheel_center_at_full_slack

# Outliers
jockey_position_diffs = jockey_position[1:] - jockey_position[:-1]

average_jockey_position_diff = np.mean(jockey_position_diffs)

low_outlier_cutoff = average_jockey_position_diff * 0.8
high_outlier_cutoff = average_jockey_position_diff * 0.4

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
cable_pull = cable_pull - cable_pull.min()

result = np.polynomial.Polynomial.fit(cable_pull, jockey_position, 3)
x_new = np.linspace(cable_pull[0], cable_pull[-1], 50)
y_new = result(x_new)

print(result.convert().coef)

starting_pull = 4
ending_pull = 32

pull_ratio = (result(ending_pull) - result(starting_pull))/(ending_pull - starting_pull)

print(pull_ratio)

plt.plot(cable_pull,jockey_position,'o', x_new, y_new)
plt.xlim([cable_pull[0]-1, cable_pull[-1] + 1 ])
plt.show()

print("done")