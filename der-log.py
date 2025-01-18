import os
import csv
import datetime
import shutil
import json

dirs = sorted([dir for dir in os.listdir("derailleurs") if dir != "template"])

for i, dir in enumerate(dirs):
  print(i, dir)
dirIndexStr = input("Please select directory [number]: ")
dirIndex = int(dirIndexStr)

dir = dirs[dirIndex]

print("Selected", dir)

with open(f"derailleurs/{dir}/info.json") as info_file:
  info = json.load(info_file)

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

cog_pitch=info["designCogPitch"]

tmp_filename = "der.csv"

cols = [
  "Puller Meas. (mm)",
  "Carriage Meas. (mm)",
  f"Num rollers {directionVerbInPast}",
  f"Measurement after rollers {directionVerbInPast} (mm)",
  "Puller Indicator After Move (mm)",
  "Carriage Indicator After Move (mm)",
  "Distance from outside of extrusion to carriage when cable is slack (mm)",
  "Distance from outside of extrusion to carriage at max pull (mm)",
  "Exclude Cable Pull Greater Than (mm)"
]  

if direction == "Pulling":
  slack_meas = input(f"{cols[6]}: ")
else:
  taut_meas = input(f"{cols[7]}: ")

chain_move_pattern = []
last_chain_move_carriage_meas = None

def input_ensure_str(*args, **kwargs):
  str = input(*args, **kwargs)
  while len(str) == 0:
    str = input(*args, **kwargs)
  return str

with open(tmp_filename, "x", newline='') as f:
  writer = csv.DictWriter(f, cols)
  writer.writeheader()

  prev_data_row = None
  data_row = None
  actionStr = None
  while True:

    # Puller Meas.
    puller_meas = input(f"{cols[0]}: ")

    # User wanted to do an action
    show_menu = len(puller_meas) == 0

    if not show_menu:
      try:
        float(puller_meas)
      except:
        show_menu = True
    
    # User is done with the previous row of data
    if data_row and not show_menu and actionStr != "r":
      writer.writerow(data_row)
      f.flush()
      prev_data_row = data_row
      data_row = {}
    
    if not data_row or actionStr == 'r':
      actionStr = None
      data_row = {}
    
    # Validate data
    if prev_data_row:
      try:
        bad_data = abs(float(prev_data_row[cols[0]]) - float(puller_meas)) > 1
        if bad_data:
          print("\aBad data")
      except:
        pass

    if not show_menu:
      # Save Puller Meas.
      data_row[cols[0]] = puller_meas
      
      # Carriage Meas.
      data_row[cols[1]] = input_ensure_str(f"{cols[1]}: ")
      if not last_chain_move_carriage_meas:
        last_chain_move_carriage_meas = float(data_row[cols[1]])
      
      # Validate data
      if prev_data_row and data_row[cols[1]]:
        try:
          bad_data = abs(float(prev_data_row[cols[1]]) - float(data_row[cols[1]])) > 1
          if bad_data:
            print("\aBad data")
        except:
          pass
    
    if show_menu:
      actionStr = input_ensure_str("Pull/relax (c)hain, (m)ove indicators, (r)edo measurements, e(x)it, con(t)inue: ")

      if actionStr == "c":
        if cols[2] in data_row:
          print("Clearing previous pull/relax values")
          chain_move_pattern.pop()
        
        print(chain_move_pattern)
        data_row[cols[2]] = input_ensure_str(f"{cols[2]}: ")
        data_row[cols[3]] = input_ensure_str(f"{cols[3]}: ")
        chain_move_pattern.append(data_row[cols[2]])
        last_chain_move_carriage_meas = float(data_row[cols[3]])

        actionStr = None
      elif actionStr == "m":
        data_row[cols[4]] = input_ensure_str(f"{cols[4]}: ")
        data_row[cols[5]] = input_ensure_str(f"{cols[5]}: ")

        # Adjust using new indicator value
        if last_chain_move_carriage_meas != None:
          last_chain_move_carriage_meas = last_chain_move_carriage_meas - float(data_row[cols[1]]) + float(data_row[cols[5]])

        actionStr = None
      elif actionStr == "x":
        break
      elif actionStr == "r":
        pass
      else:
        actionStr = None
      
    try:
      if cols[4] not in data_row:
        if last_chain_move_carriage_meas != None and \
            abs(float(data_row[cols[1]]) - float(last_chain_move_carriage_meas)) > cog_pitch:
          print(f"Move chain: {abs(float(data_row[cols[1]]) - float(last_chain_move_carriage_meas))}")
        if direction == "Pulling" and float(data_row[cols[1]]) > 22.0:
          print("Move indicators")
        if direction == "Relaxing" and float(data_row[cols[1]]) < 0.4:
          print("Move indicators")
    except KeyError:
      pass
    except Exception as ex:
      print(ex)

  if direction == "Relaxing":
    slack_meas = input(f"{cols[6]}: ")
  else:
    taut_meas = input(f"{cols[7]}: ")
  
  data_row[cols[6]] = slack_meas
  data_row[cols[7]] = taut_meas
  writer.writerow(data_row)
  f.flush()

end_time = datetime.datetime.now()

filename=f"{end_time:%Y-%m-%d %H-%M %p} {direction}.csv"

print("Writing to", filename)
shutil.move(tmp_filename, f"derailleurs/{dir}/pullratio/{filename}")