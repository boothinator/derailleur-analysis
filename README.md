# Derailleur and Shifter Data Analysis

## Data Analysis Process

1. analyze each derailleur, produce info_out.json in each folder
2. analyze each shifter, produce info_out.json in each folder
3. build JSONs of derailleur and shifter info
4. use list of supported combos and derailleur and shifter and cassette info lists to create motion multiplier ranges and chain angle ranges, and validate the ranges
5. use motion multiplier ranges to figure out list of other compatible components
6. Combine list of supported combos, list of unsupported combos, list of reviewed combinations, list of exact matches (like SRAM shifters) to produce list of combinations and whether they're supported or unsupported, info about how far off the averages are, info about how far off each gear is, including the angle
7. Provide list of derailleurs, shifters, cassettes, and combos

## Derailleurs

[Campagnolo Ekar 13-Speed (RD21-EK13)](https://boothinator.github.io/derailleur-analysis/derailleurs/Campagnolo%20Ekar/default.htm) - Pull Ratio: 1.28

[Shimano 105 11-Speed (RD-5800)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20105%2011-speed/default.htm) - Pull Ratio: 1.45

[Shimano CUES 10-Speed (RD-U6020-10)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20CUES%2010-Speed/default.htm) - Pull Ratio: 1.06

[Shimano CUES 9-Speed (RD-U4020)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20CUES%209-Speed/default.htm) - Pull Ratio: 1.11

[Shimano Deore 11-Speed (RD-M4120)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Deore%2011-Speed/default.htm) - Pull Ratio: 1.07

[Shimano Deore 11-Speed (RD-M5120)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Deore%20M5120/default.htm) - Pull Ratio: 1.10

[Shimano Deore 12-Speed (RD-M6100)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Deore%20M6100/default.htm) - Pull Ratio: 1.07

[Shimano GRX 10-Speed (RD-RX400)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20GRX%2010-Speed/default.htm) - Pull Ratio: 1.45

[Shimano Tiagra 4600 10-Speed (RD-4601-SS)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Tiagra%204600%2010-Speed/default.htm) - Pull Ratio: 1.67

[Shimano Ultegra 9-Speed (RD-6500)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Ultegra%206500%209-Speed/default.htm) - Pull Ratio: 1.64

[Shimano Ultegra RX 11-Speed (RD-RX800)](https://boothinator.github.io/derailleur-analysis/derailleurs/Shimano%20Ultegra%20RX%2011-Speed/default.htm) - Pull Ratio: 1.51

[SRAM Apex 1 11-Speed (RD-APX-1-A1)](https://boothinator.github.io/derailleur-analysis/derailleurs/SRAM%20Apex%2011-Speed/default.htm) - Pull Ratio: 1.22

[SRAM GX 10-Speed (RD-GX-T21-A1)](https://boothinator.github.io/derailleur-analysis/derailleurs/SRAM%20GX%2010-Speed/default.htm) - Pull Ratio: 1.33

[SRAM SX 12-Speed (RD-SX-1-B1)](https://boothinator.github.io/derailleur-analysis/derailleurs/SRAM%20SX%2012-Speed/default.htm) - Pull Ratio: 1.08


## Shifters

[Campagnolo Ekar 13-Speed (EP21-EKD13-R4)](https://boothinator.github.io/derailleur-analysis/shifters/Campagnolo%20Ekar/default.htm) - Cable Pull: 2.42 mm/shift

[Microshift Advent X 10-Speed (SB-M100A)](https://boothinator.github.io/derailleur-analysis/shifters/Microshift%20Advent%20X/default.htm) - Cable Pull: 3.41 mm/shift

[Sensah Team Pro 11-Speed (sensah-team-pro-11)](https://boothinator.github.io/derailleur-analysis/shifters/Sensah%20Team%20Pro/default.htm) - Cable Pull: 2.51 mm/shift

[Shimano CUES 10-Speed (SL-U6000-10R)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20CUES%2010-Speed/default.htm) - Cable Pull: 3.58 mm/shift

[Shimano CUES 9-Speed (SL-U4000)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20CUES%209-Speed/default.htm) - Cable Pull: 3.56 mm/shift

[Shimano Deore 10-Speed (SL-M4100)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Deore%2010-Speed/default.htm) - Cable Pull: 3.48 mm/shift

[Shimano Deore 11-Speed (SL-M5100)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Deore%2011-Speed/default.htm) - Cable Pull: 3.40 mm/shift

[Shimano SLX 12-Speed (SL-M7100)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20SLX/default.htm) - Cable Pull: 3.19 mm/shift

[Shimano Tiagra 4700 10-Speed (ST-4700)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Tiagra%204700/default.htm) - Cable Pull: 2.65 mm/shift

[Shimano Ultegra 11-Speed (ST-R8020)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Ultegra%2011-Speed/default.htm) - Cable Pull: 2.50 mm/shift

[Shimano Ultegra 10-Speed (ST-6600)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Ultegra%206600/default.htm) - Cable Pull: 2.28 mm/shift

[Shimano Ultegra 10-Speed (ST-6700)](https://boothinator.github.io/derailleur-analysis/shifters/Shimano%20Ultegra%206700/default.htm) - Cable Pull: 2.28 mm/shift

[SRAM Apex 1 11-Speed (SB-APX-B1)](https://boothinator.github.io/derailleur-analysis/shifters/SRAM%20Apex%201/default.htm) - Cable Pull: 2.88 mm/shift

[SRAM GX 10-Speed (SL-GX-A1)](https://boothinator.github.io/derailleur-analysis/shifters/SRAM%20GX%2010-Speed/default.htm) - Cable Pull: 3.00 mm/shift

[SRAM SX 12-Speed (SL-SX-1-A1)](https://boothinator.github.io/derailleur-analysis/shifters/SRAM%20SX/default.htm) - Cable Pull: 3.25 mm/shift


