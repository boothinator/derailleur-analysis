
import json


with open(f"combinations.json") as f:
  combos = json.load(f)

with open(f"supported_combinations.json") as f:
  supported_combos = json.load(f)

lowest_max_tooth = 35
lowest_chain_wrap = 40

lowest_gearing_with_drop_bar_shifters_combos = []
widest_range_with_drop_bar_shifters_combos = []

for combo in combos:
  if ((combo["shifterType"] == "drop-bar"
        or any([s for s in combo["equivalentShifters"] if s["type"] == "drop-bar"]))
      and (combo["brand"] == "Mixed"
           or combo["sameGroup"] 
           or combo["derailleurName"] != combo["shifterName"]
           or (not combo["sameGroup"]
               and any([
                sc for sc in supported_combos
                if combo["shifterPartNumber"] == sc["shifterPartNumber"]
                  and combo["derailleurPartNumber"] == sc["derailleurPartNumber"]
    #sc["cassettePartNumber"]
            ])))
      and combo["moreCogsThanShifts"] == False):

    if combo["maxToothAvailableAndCompatible"] >= lowest_max_tooth:
      lowest_gearing_with_drop_bar_shifters_combos.append(combo)
    if combo["chainWrap"] >= lowest_chain_wrap:
      widest_range_with_drop_bar_shifters_combos.append(combo)

lowest_gearing_with_drop_bar_shifters_combos.sort(key=lambda combo: combo["maxToothAvailableAndCompatible"], reverse=True)
widest_range_with_drop_bar_shifters_combos.sort(key=lambda combo: combo["chainWrap"], reverse=True)

with open(f"lowest_gearing_with_drop_bar_shifters_combos.json", "w") as info_file:
  json.dump(lowest_gearing_with_drop_bar_shifters_combos, info_file, indent=2)

with open(f"widest_range_with_drop_bar_shifters_combos.json", "w") as info_file:
  json.dump(widest_range_with_drop_bar_shifters_combos, info_file, indent=2)