import numpy as np
import matplotlib.pyplot as plt
import os
import json
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from util import get_jockey_offset_curve, get_jockey_offset_rate_curve, PullRatioInfo

# TODO:
# Combine yaw pull ratio with regular pull ratio, and yaw pull ratio curve with base pull ratio curve to get overall pull ratio curve
# Can I combine both curves into a single curve using just a 3rd order polynomial? Or would that kink from the yaw curve be too much to model well

# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape())
template = environment.get_template("derailleur_analysis.htm")

with open("overall_stats.json") as f:
  overall_stats = json.load(f)

def process_der(dir):
  
  with open(f"derailleurs/{dir}/info.json") as info_file:
    info = json.load(info_file)
  
  with open(f"derailleurs/{dir}/pullratio/base_pull_ratio_info.json") as info_file:
    base_pull_ratio_info = json.load(info_file)
  
  if os.path.exists(f"derailleurs/{dir}/yaw/yaw_info.json"):
    with open(f"derailleurs/{dir}/yaw/yaw_info.json") as info_file:
      yaw_info = json.load(info_file)
  else:
    yaw_info = {}

  # Get curves
  pull_curve = np.polynomial.polynomial.Polynomial(base_pull_ratio_info["coefficients"])

  if "yawCoefficients" in yaw_info:
    yaw_angle_curve = np.polynomial.polynomial.Polynomial(yaw_info["yawCoefficients"])
    jockey_offset_curve = get_jockey_offset_curve(yaw_angle_curve)

    # Calc combined pull ratio
    # FIXME: doesn't take into account how pull ratio affects position of cogs affected by yaw
    total_pitch_inner_cogs = base_pull_ratio_info["pullRatioCalc"]["total_pitch_inner_cogs"]
    second_biggest_cog_pull = base_pull_ratio_info["pullRatioCalc"]["second_biggest_cog_pull"]
    second_smallest_cog_pull = base_pull_ratio_info["pullRatioCalc"]["second_smallest_cog_pull"]
    jockey_adjustment_from_yaw = jockey_offset_curve(second_biggest_cog_pull) - jockey_offset_curve(second_smallest_cog_pull)
    pull_ratio = (total_pitch_inner_cogs + jockey_adjustment_from_yaw)/(second_biggest_cog_pull - second_smallest_cog_pull)

    biggest_cog_pull = base_pull_ratio_info["pullRatioCalc"]["biggest_cog_pull"]
    smallest_cog_pull = base_pull_ratio_info["pullRatioCalc"]["smallest_cog_pull"]
    yaw_info["yawAtSmallestCog"] = yaw_angle_curve(smallest_cog_pull)
    yaw_info["yawAtSecondSmallestCog"] = yaw_angle_curve(second_smallest_cog_pull)
    yaw_info["yawAtSecondBiggestCog"] = yaw_angle_curve(second_biggest_cog_pull)
    yaw_info["yawAtBiggestCog"] = yaw_angle_curve(biggest_cog_pull)
  else:
    pull_ratio = base_pull_ratio_info["basePullRatio"]
  
  # Info Output
  info_out = {
    **info,
    'pullRatio': pull_ratio,
    **base_pull_ratio_info,
    **yaw_info,
    "analysisUrl": f"https://boothinator.github.io/derailleur-analysis/derailleurs/{dir}/default.htm"
  }
  
  with open(f"derailleurs/{dir}/info_out.json", "w") as info_file:
    json.dump(info_out, info_file, indent=2)
  
  max_pull = info_out["maxPull"]
  x_new = np.linspace(0, max_pull, 100)

  # Combined pull curve
  if "yawCoefficients" in yaw_info:
    y_new = pull_curve(x_new) + jockey_offset_curve(x_new)
  else:
    y_new = pull_curve(x_new)
  
  plt.clf()
  if "yawCoefficients" in yaw_info:
    plt.plot(x_new, [jockey_offset_curve(x) for x in x_new], label="Motion from Yaw")
    plt.plot(x_new, [pull_curve(x) for x in x_new], label="Jockey Motion")
    plt.plot(x_new, y_new, label="Effective Jockey Motion")
    plt.legend()
  else:
    plt.plot(x_new, y_new)
  plt.xlim([0, max_pull])
  plt.ylim([ -2, y_new.max() + 0.2])
  plt.savefig(f"derailleurs/{dir}/pull_curve.png")
  plt.close()

  # Pull ratio component curves

  pull_ratio_curve = pull_curve.deriv()
  if "yawCoefficients" in yaw_info:
    jockey_offset_rate_curve = get_jockey_offset_rate_curve(yaw_angle_curve)

    y_new = pull_ratio_curve(x_new) + jockey_offset_rate_curve(x_new)
  else:
    y_new = pull_ratio_curve(x_new)
  
  if "yawCoefficients" in yaw_info and yaw_info["yawAffectsPullRatio"]:
    plt.clf()
    plt.plot(x_new, [jockey_offset_rate_curve(x) for x in x_new], label="Pull Ratio from Yaw")
    plt.plot(x_new, [pull_ratio_curve(x) for x in x_new], label="Base Pull Ratio")
    plt.plot(x_new, y_new, label="Effective Pull Ratio")
    plt.legend()
    plt.xlim([0, max_pull])
    plt.ylim([-0.2, y_new.max() + 0.2])
    plt.savefig(f"derailleurs/{dir}/pull_ratio_component_curves.png")
    plt.close()

  # Overall Pull Ratio Curve
  pr_calc = PullRatioInfo.model_validate(info_out["pullRatioCalc"])

  x_pr = [pr_calc.smallest_cog_pull, pr_calc.biggest_cog_pull]
  y_pr = [pull_ratio, pull_ratio]

  x_cogs = [pr_calc.second_smallest_cog_pull, pr_calc.second_biggest_cog_pull]
  y_cogs = [pull_ratio, pull_ratio]

  pull_ratio_curve_prime = pull_ratio_curve.deriv(1)
  
  plt.clf()
  plt.plot(x_new, y_new, x_pr, y_pr, x_cogs, y_cogs, "o")
  plt.xlim([0, max_pull])
  plt.ylim([0, pull_ratio*1.4])
  plt.xlabel("Cable Pull (mm)")
  plt.ylabel("Pull Ratio")
  plt.title(f"{info['brand']} {info['name']} {info['designSpeeds']}-speed Derailleur Pull Ratio")
  avg_pull_ratio_annotation_x = np.max([pr_calc.second_smallest_cog_pull, *[r for r in pull_ratio_curve_prime.roots() if r > 0]])
  plt.annotate(f"Avg. Pull Ratio {round(pull_ratio, 2)}",
                 (avg_pull_ratio_annotation_x, pull_ratio),
                 xytext=(-35, -12), textcoords="offset points")
  plt.savefig(f"derailleurs/{dir}/pull_ratio_curve.png")
  plt.close()

  # Render info page
  # TODO: update pages to show yaw info
  today = datetime.date.today()

  run_files = [datafile for datafile in os.listdir(f"derailleurs/{dir}/pullratio") if datafile.endswith('.csv')]

  runs = [{
    'name': r.replace('.csv', ''),
    'chart': 'pullratio/'+r.replace('.csv', '.png'),
    'csvFile': 'pullratio/' + r
  } for r in run_files]

  coefficients_str = f"{info_out['coefficients'][0]:.2f}, {info_out['coefficients'][1]:.3f}, {info_out['coefficients'][2]:.5f}, {info_out['coefficients'][3]:.6f}"

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

meas_method_percent_diffs = []

for dir in os.listdir('derailleurs'):
  if dir == "template":
    continue

  # TESTING
  #if dir != "Shimano Deore M6100":
  #  continue
  #if dir != "Campagnolo Ekar":
  #  continue

  print(dir)

  info_out = process_der(dir)
  all_info.append(info_out)
  meas_method_percent_diffs = meas_method_percent_diffs + info_out["meas_method_percent_diffs"]


avg_meas_method_percent_diff = np.mean(meas_method_percent_diffs)
stdev_meas_method_percent_diff = np.std(meas_method_percent_diffs)

with open("overall_stats.json", "w") as f:
  json.dump({
    "avg_meas_method_percent_diff": avg_meas_method_percent_diff,
    "stdev_meas_method_percent_diff": stdev_meas_method_percent_diff,
    "Caliper vs Indicator percent difference": f"Caliper vs Indicator percent difference: {avg_meas_method_percent_diff} +/- {stdev_meas_method_percent_diff * 2}"
  }, f, indent=2)

with open(f"all_derailleurs.json", "w") as info_file:
  json.dump(all_info, info_file, indent=2)