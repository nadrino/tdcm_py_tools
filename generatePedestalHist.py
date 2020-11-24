#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, getopt
from ROOT import TH1D
from ROOT import TFile

filePath = ""

for arg_id in range(len(sys.argv)):
    if sys.argv[arg_id] == "-f":
        filePath = sys.argv[arg_id+1]

print("Reading file: " + filePath)
fileLines = list()
with open(filePath, 'r') as f:
    for line in f:
        fileLines.append(line)


entriesList = list()
valuesList = list()

print("Parsing pedestals...")
for logLine in fileLines:
    splitedStr = logLine.split(' ')
    if len(splitedStr) != 11 or splitedStr[0] != "Card":
        continue
    newEntry = dict()
    newEntry["Card"] = int(splitedStr[1])
    newEntry["Chip"] = int(splitedStr[3])
    newEntry["Channel"] = int(splitedStr[5])
    if newEntry not in entriesList: # only read the first pass, the second is renormalized data
        entriesList.append(newEntry)
        newValues = dict()
        newValues["Mean"] = int(splitedStr[8])
        newValues["StdDev"] = int(splitedStr[10])
        valuesList.append(newValues)

histMean = TH1D("histMean", "histMean", len(newEntry), -0.5, len(newEntry)-0.5)

print("Putting data in histograms...")
for iEntry in range(len(entriesList)):
    histMean.Fill(iEntry, newValues["Mean"])

print("Writing hist to file...")
outFile = TFile("outFile_"+filePath.replace("/","_")+".root", "RECREATE")
histMean.Write("histMean")
outFile.Close()