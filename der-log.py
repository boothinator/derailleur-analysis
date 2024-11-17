import os
import csv
import datetime
import shutil

dirs = sorted([dir for dir in os.listdir("derailleurs") if dir != "template"])

for i, dir in enumerate(dirs):
  print(i, dir)
dirIndexStr = input("Please select directory [number]: ")
dirIndex = int(dirIndexStr)

dir = dirs[dirIndex]

print("Selected", dir)

directionStr=input("(P)ulling or (R)elaxing: ").lower()

if directionStr == "p":
  direction = "Pulling"
  directionVerbInPast = "pulled"
elif directionStr == "r":
  direction = "Relaxing"
  directionVerbInPast = "relaxed"
else:
  print("Invalid input", directionStr)
  exit()

tmp_filename = "der.csv"

cols = [
  "Puller Meas. (neg) (mm)",
  "Carriage Meas. (mm)",
  f"Num rollers {directionVerbInPast}",
  f"Measurement after rollers {directionVerbInPast} (mm)",
  "Puller Indicator After Move (neg) (mm)",
  "Carriage Indicator After Move (mm)",
  "Distance from outside of extrusion to carriage when cable is slack (mm)",
  "Distance from outside of extrusion to carriage at max pull (mm)"
]  

if direction == "Pulling":
  slack_meas = input(f"{cols[6]}: ")
else:
  taut_meas = input(f"{cols[7]}: ")

with open(tmp_filename, "x", newline='') as f:
  writer = csv.DictWriter(f, cols)
  writer.writeheader()

  while True:
    data_row = {}
    
    actionStr = None
    while actionStr != "" and actionStr != "x":
      if actionStr != None:
        actionStr = input("Continue (enter), pull/relax (c)hain, (m)ove indicators, (r)edo measurements, e(x)it: ")
      if actionStr == "r" or actionStr == None:
        data_row[cols[0]] = input(f"{cols[0]}: ")
        data_row[cols[1]] = input(f"{cols[1]}: ")
        actionStr = "r"
      elif actionStr == "c":
        data_row[cols[2]] = input(f"{cols[2]}: ")
        data_row[cols[3]] = input(f"{cols[3]}: ")
      elif actionStr == "m":
        data_row[cols[2]] = input(f"{cols[4]}: ")
        data_row[cols[3]] = input(f"{cols[5]}: ")
    
    writer.writerow(data_row)
    f.flush()
    if actionStr == "x":
      break
      

  if direction == "Relaxing":
    slack_meas = input(f"{cols[6]}: ")
  else:
    taut_meas = input(f"{cols[7]}: ")
  
  data_row = {}
  data_row[cols[6]] = slack_meas
  data_row[cols[7]] = taut_meas
  writer.writerow(data_row)
  f.flush()

end_time = datetime.datetime.now()

filename=f"{end_time:%Y-%m-%d %H-%m %p} {direction}.csv"

print("Writing to", filename)
shutil.move(tmp_filename, f"derailleurs/{dir}/pullratio/{filename}")