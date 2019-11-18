#!/usr/bin/env python3

import json
import os

days = [ 'Friday', 'Saturday', 'Sunday', 'Monday']

resultsFile = "results/{}/{}/{}/results.json"
classNamesFile = "results/{}/classnames.json"
heatNamesFile = "results/{}/{}/heatnames.json"
allResultsFile = "results/allResults.json"
allResults = []

for d in days:
    if os.path.exists(classNamesFile.format(d)):
        with open(classNamesFile.format(d)) as cfile:
            classNames = json.load(cfile)
            # first item is day name
            for c in classNames[1:]:
                if os.path.exists(heatNamesFile.format(d, c)):
                    with open(heatNamesFile.format(d, c)) as hfile:
                        heats = json.load(hfile)
                        for h in heats:
                            with open(resultsFile.format(d,c,h)) as rfile:
                                result = json.load(rfile)
                                allResults.append(result)
with open(allResultsFile, 'w') as f:
    json.dump(allResults, f)
