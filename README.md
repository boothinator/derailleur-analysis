General process

1. analyze each derailleur, produce info_out.json in each folder
2. analyze each shifter, produce info_out.json in each folder
3. build JSONs of derailleur and shifter info
4. use list of supported combos and derailleur and shifter and cassette info lists to create motion multiplier ranges and chain angle ranges, and validate the ranges
5. use motion multiplier ranges to figure out list of other compatible components
6. Combine list of supported combos, list of unsupported combos, list of reviewed combinations, list of exact matches (like SRAM shifters) to produce list of combinations and whether they're supported or unsupported, info about how far off the averages are, info about how far off each gear is, including the angle
7. Provide list of derailleurs, shifters, cassettes, and combos