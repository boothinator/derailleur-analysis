import csv

input_file = 'Campagnolo Ekar 13-Speed Derailleur Ratio - 10_6 11_05 AM Pulling.csv'

data = []

with open(input_file, newline='') as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    data.append(row)

