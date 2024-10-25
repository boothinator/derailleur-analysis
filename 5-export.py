import os
import shutil
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

shutil.rmtree('export')
os.mkdir('export')

shutil.copy("all_shifters.json", "export")
shutil.copy("all_derailleurs.json", "export")
shutil.copy("all_cassettes.json", "export")
shutil.copy("combinations.json", "export")
shutil.copy("lowest_gearing_with_drop_bar_shifters_combos.json", "export")
shutil.copy("widest_range_with_drop_bar_shifters_combos.json", "export")
shutil.copy("compatibility_ranges.json", "export")
shutil.copy("equivalent_derailleurs.json", "export")
shutil.copy("equivalent_shifters.json", "export")


# Template environment
environment = Environment(loader=FileSystemLoader("."), autoescape=select_autoescape(),
                          trim_blocks=True, lstrip_blocks=True)
template = environment.get_template("README.md.jinja")

with open("all_shifters.json") as f:
  shifters = json.load(f)
with open("all_derailleurs.json") as f:
  derailleurs = json.load(f)

output = template.render(shifters=shifters, derailleurs=derailleurs)

with open(f"README.md", 'w') as f:
  print(output, file = f)