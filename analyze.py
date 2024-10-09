import csv
import numpy as np
import matplotlib.pyplot as plt

input_file = 'Campagnolo Ekar 13-Speed Derailleur Ratio - 10_6 11_05 AM Pulling.csv'

data = []

extrusion_to_carriage_slack=67.4
extrusion_to_carriage_max_pull=111.79
jockey_wheel_thickness=1.75
carriage_to_jockey_wheel=36.52

extrusion_thickness=19.93

jockey_wheel_center_at_full_slack=extrusion_to_carriage_slack - carriage_to_jockey_wheel - extrusion_thickness - jockey_wheel_thickness/2

with open(input_file, newline='') as csvfile: 
  reader = csv.reader(csvfile)
  for row in reader:
    data.append(row)

header = data[0]
data = np.array(data[1:]).T

x = np.array([float(d) for d in data[0][7:50]])
y = np.array([float(d) for d in data[1][7:50]]) + jockey_wheel_center_at_full_slack

result = np.polynomial.Polynomial.fit(x, y, 3)
x_new = np.linspace(x[0], x[-1], 50)
y_new = result(x_new)

print(result.coef)

plt.plot(x,y,'o', x_new, y_new)
plt.xlim([x[0]-1, x[-1] + 1 ])
plt.show()

print("done")