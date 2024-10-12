import os
import shutil


shutil.rmtree('export')
os.mkdir('export')

shutil.copy("all_shifters.json", "export")
shutil.copy("all_derailleurs.json", "export")
shutil.copy("all_cassettes.json", "export")
shutil.copy("combinations.json", "export")
shutil.copy("lowest_gearing_with_drop_bar_shifters_combos.json", "export")
shutil.copy("widest_range_with_drop_bar_shifters_combos.json", "export")