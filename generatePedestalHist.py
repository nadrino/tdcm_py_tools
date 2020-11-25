#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, getopt
from array import array
import numpy
from ROOT import TH1D
from ROOT import TH2D
from ROOT import TFile
from ROOT import TNtupleD

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
chipLines = list()

cardList = list()
chipList = list()
channelList = list()

print("Parsing pedestals...")
lastChannel = -1
for logLine in fileLines:
    splitedStr = logLine.split(' ')
    if len(splitedStr) != 11 or splitedStr[0] != "Card":
        continue
    newEntry = dict()
    newEntry["Card"] = int(splitedStr[1])
    newEntry["Chip"] = int(splitedStr[3])
    newEntry["Channel"] = int(splitedStr[5])
    if newEntry not in entriesList: # only read the first pass, the second is renormalized data

        if newEntry["Card"] not in cardList:
            cardList.append(newEntry["Card"])

        if newEntry["Chip"] not in chipList:
            chipList.append(newEntry["Chip"])

        if newEntry["Channel"] not in channelList:
            channelList.append(newEntry["Channel"])

        entriesList.append(newEntry)
        newValues = dict()
        newValues["Mean"] = float(splitedStr[8])
        newValues["StdDev"] = float(splitedStr[10])
        valuesList.append(newValues)
        if lastChannel > newEntry["Channel"]:
            chipLines.append(len(entriesList)-0.5)

    lastChannel = newEntry["Channel"]

if len(entriesList) == 0:
    print("No entry have been found.")
    exit(1)

outFilePath = "outFile_"+"_".join(filePath.replace("/","_").split('.')[0:-1])+".root"

print("Output file will be writen as: " + outFilePath)
outFile = TFile.Open(outFilePath, "RECREATE")

varNameList = list()
varNameList.append("Card")
varNameList.append("Chip")
varNameList.append("Channel")
varNameList.append("Mean")
varNameList.append("StdDev")

# all variables are stored in this event container array. This will prevent python to reallocate doubles at each loop
pedestalTree = TNtupleD("pedestalTree", "pedestalTree", (":".join(varNameList[0:len(varNameList)])))
event_container = array("d", numpy.zeros((len(varNameList),), dtype=float))

for iEntry in range(len(entriesList)):
    event_container[0] = entriesList[iEntry]["Card"]
    event_container[1] = entriesList[iEntry]["Chip"]
    event_container[2] = entriesList[iEntry]["Channel"]
    event_container[3] = valuesList [iEntry]["Mean"]
    event_container[4] = valuesList [iEntry]["StdDev"]
    pedestalTree.Fill(event_container[0:len(varNameList)])

pedestalTree.GetTree().Write()

print("Putting data in histograms...")

for card in cardList:

    hist2dMean = TH2D("hist2dMean", "hist2dMean", len(channelList), 0, len(channelList), len(chipList), 0, len(chipList))
    pedestalTree.Draw("Chip:Channel>>hist2dMean", "Mean", "goff")
    hist2dMean.SetTitle("Mean value")
    hist2dMean.GetXaxis().SetTitle("Channel #")
    hist2dMean.GetYaxis().SetTitle("Chip #")
    hist2dMean.Write("hist2dMean" + str(card))

    hist2dStdDev = TH2D("hist2dStdDev", "hist2dStdDev", len(channelList), 0, len(channelList), len(chipList), 0, len(chipList))
    pedestalTree.Draw("Chip:Channel>>hist2dStdDev", "StdDev", "goff")
    hist2dMean.SetTitle("StdDev value")
    hist2dMean.GetXaxis().SetTitle("Channel #")
    hist2dMean.GetYaxis().SetTitle("Chip #")
    hist2dMean.Write("hist2dStdDev" + str(card))

    histMean = TH1D("histMean", "histMean", len(channelList)*len(chipList), 0, len(channelList)*len(chipList))
    pedestalTree.Draw(str(len(channelList))+"*Chip + Channel>>histMean", "Mean", "goff")
    histMean.Write("histMean" + str(card))

    histMean = TH1D("histStdDev", "histStdDev", len(channelList)*len(chipList), 0, len(channelList)*len(chipList))
    pedestalTree.Draw(str(len(channelList))+"*Chip + Channel>>histStdDev", "StdDev", "goff")
    histMean.Write("histStdDev" + str(card))

outFile.Close()