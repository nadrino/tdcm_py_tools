#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, getopt
from array import array
import numpy
import os
from ROOT import TH1D
from ROOT import TH2D
from ROOT import TFile
from ROOT import TNtupleD

nbIterations = -1
currentIteration = 0
filePath = ""

histMeanList = list()

cardList = list()
chipList = list()
channelList = list()
varNameList = list()
varNameList.append("Card")
varNameList.append("Chip")
varNameList.append("Channel")
varNameList.append("Mean")
varNameList.append("StdDev")
varNameList.append("Iteration")

pedestalTree = TNtupleD("pedestalTree", "pedestalTree", (":".join(varNameList[0:len(varNameList)])))

def parseFile():

    global pedestalTree, filePath, currentIteration

    print("Reading file: " + filePath)
    fileLines = list()
    with open(filePath, 'r') as f:
        for line in f:
            fileLines.append(line)

    entriesList = list()
    valuesList = list()
    chipLines = list()

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

    # all variables are stored in this event container array. This will prevent python to reallocate doubles at each loop
    event_container = array("d", numpy.zeros((len(varNameList),), dtype=float))

    for iEntry in range(len(entriesList)):
        event_container[0] = entriesList[iEntry]["Card"]
        event_container[1] = entriesList[iEntry]["Chip"]
        event_container[2] = entriesList[iEntry]["Channel"]
        event_container[3] = valuesList [iEntry]["Mean"]
        event_container[4] = valuesList [iEntry]["StdDev"]
        event_container[5] = currentIteration
        pedestalTree.Fill(event_container[0:len(varNameList)])

    print("Putting data in histograms...")

    outFile.mkdir("Iteration-" + str(currentIteration))
    outFile.cd("Iteration-" + str(currentIteration))

    for card in cardList:

        hist2dMean = TH2D("hist2dMean", "hist2dMean", len(channelList), 0, len(channelList), len(chipList), 0, len(chipList))
        pedestalTree.Draw("Chip:Channel>>hist2dMean", "Mean * (Iteration == " + str(currentIteration) + " && Mean < 511)", "goff")
        hist2dMean.SetTitle("Mean value")
        hist2dMean.GetXaxis().SetTitle("Channel #")
        hist2dMean.GetYaxis().SetTitle("Chip #")
        hist2dMean.Write("hist2dMean" + str(card))

        hist2dStdDev = TH2D("hist2dStdDev", "hist2dStdDev", len(channelList), 0, len(channelList), len(chipList), 0, len(chipList))
        pedestalTree.Draw("Chip:Channel>>hist2dStdDev", "StdDev * (Iteration == " + str(currentIteration) + " && Mean < 511)", "goff")
        hist2dStdDev.SetTitle("StdDev value")
        hist2dStdDev.GetXaxis().SetTitle("Channel #")
        hist2dStdDev.GetYaxis().SetTitle("Chip #")
        hist2dStdDev.Write("hist2dStdDev" + str(card))

        histMean = TH1D("histMean", "histMean", len(channelList)*len(chipList), 0, len(channelList)*len(chipList))
        pedestalTree.Draw(str(len(channelList))+"*Chip + Channel>>histMean", "Mean * (Iteration == " + str(currentIteration) + " && Mean < 511)", "goff")
        histMean.GetXaxis().SetTitle(str(len(channelList))+"*Chip# + Channel#")
        histMean.Write("histMean" + str(card))
        histMeanList.append(histMean)

        histDev = TH1D("histStdDev", "histStdDev", len(channelList)*len(chipList), 0, len(channelList)*len(chipList))
        pedestalTree.Draw(str(len(channelList))+"*Chip + Channel>>histStdDev", "StdDev * (Iteration == " + str(currentIteration) + " && Mean < 511)", "goff")
        histDev.GetXaxis().SetTitle(str(len(channelList)) + "*Chip# + Channel#")
        histDev.Write("histStdDev" + str(card))

    outFile.cd()


def generateCovMatrix():

    global nbIterations, histMeanList

    print("Computing average values...")
    histMeanSampleCounts = histMeanList[0].Clone()
    histMeanAverage = histMeanList[0].Clone()

    for iBin in range(histMeanAverage.GetNbinsX()):
        histMeanAverage.SetBinContent(iBin+1,0)
        histMeanSampleCounts.SetBinContent(iBin+1,0)

    for iBin in range(histMeanAverage.GetNbinsX()):
        for iIteration in range(nbIterations):
            if histMeanList[iIteration].GetBinContent(iBin+1) != 0:
                histMeanAverage.SetBinContent(iBin+1, histMeanAverage.GetBinContent(iBin+1) + histMeanList[iIteration].GetBinContent(iBin+1))
                histMeanSampleCounts.SetBinContent(iBin+1, histMeanSampleCounts.GetBinContent(iBin+1) + 1)

    for iBin in range(histMeanAverage.GetNbinsX()):
        if histMeanSampleCounts.GetBinContent(iBin+1) != 0:
            histMeanAverage.SetBinContent(iBin + 1, histMeanAverage.GetBinContent(iBin + 1)/histMeanSampleCounts.GetBinContent(iBin+1))

    print("Computing covariance...")
    hist2dCov = TH2D("hist2dCov", "hist2dCov",
                     len(channelList) * len(chipList), 0, len(channelList) * len(chipList),
                     len(channelList) * len(chipList), 0, len(channelList) * len(chipList))
    hist2dCovCounts = hist2dCov.Clone()
    for iBin in range(histMeanAverage.GetNbinsX()):
        for jBin in range(histMeanAverage.GetNbinsX()):
            for iIteration in range(nbIterations):
                if histMeanList[iIteration].GetBinContent(iBin+1) == 0 or histMeanList[iIteration].GetBinContent(jBin+1) == 0:
                    continue # skip if one of the 2 samples is not valid
                hist2dCov.SetBinContent(iBin+1, jBin+1,
                                         (histMeanList[iIteration].GetBinContent(iBin+1) - histMeanAverage.GetBinContent(iBin+1))
                                        *(histMeanList[iIteration].GetBinContent(jBin+1) - histMeanAverage.GetBinContent(jBin+1))
                                        )

                hist2dCovCounts.SetBinContent(iBin+1, jBin+1, hist2dCovCounts.GetBinContent(iBin+1, jBin+1)+1)

    for iBin in range(histMeanAverage.GetNbinsX()):
        for jBin in range(histMeanAverage.GetNbinsX()):
            if hist2dCovCounts.GetBinContent(iBin+1, jBin+1) != 0:
                hist2dCov.SetBinContent(iBin+1, jBin+1, hist2dCov.GetBinContent(iBin+1, jBin+1)/hist2dCovCounts.GetBinContent(iBin+1, jBin+1))

    print("Computing correlation matrix...")
    hist2dCor = hist2dCov.Clone()
    hist2dCor.SetTitle("hist2dCor")
    hist2dCor.SetName ("hist2dCor")
    for iBin in range(histMeanAverage.GetNbinsX()):
        for jBin in range(histMeanAverage.GetNbinsX()):
            if hist2dCov.GetBinContent(jBin+1, jBin+1) == 0 or hist2dCov.GetBinContent(iBin+1, iBin+1) == 0:
                continue
            hist2dCor.SetBinContent(iBin+1, jBin+1,
                                    hist2dCov.GetBinContent(iBin+1, jBin+1)
                                    /hist2dCov.GetBinContent(iBin+1, iBin+1)
                                    /hist2dCov.GetBinContent(jBin+1, jBin+1)
                                    )
    hist2dCov.Write()
    hist2dCor.Write()


pedScriptPath = ""

for arg_id in range(len(sys.argv)):
    if sys.argv[arg_id] == "-f":
        filePath = sys.argv[arg_id+1]
    if sys.argv[arg_id] == "-s":
        pedScriptPath = sys.argv[arg_id+1]
    elif sys.argv[arg_id] == "-it":
        nbIterations = int(sys.argv[arg_id+1])

outFilePath = "outFile_"+"_".join(filePath.replace("/","_").split('.')[0:-1])+".root"
print("Output file will be writen as: " + outFilePath)
outFile = TFile.Open(outFilePath, "RECREATE")

if nbIterations == -1:
    parseFile()
else:
    if pedScriptPath is "":
        print("pedScriptPath is not set (-s)")
        exit()
    for iIteration in range(nbIterations):
        currentIteration = iIteration
        print("-> Next iteration:", currentIteration)
        print("Power cycle the TDCM...")
        print("Power OFF...")
        os.system("sudo /home/lpnhe/powtdcm.py 0")
        print("Waiting 5 sec...")
        os.system("sleep 5")
        print("Power ON...")
        os.system("sudo /home/lpnhe/powtdcm.py 1")
        print("Waiting 20 sec...")
        os.system("sleep 20")

        print("Taking pedestals...")
        os.system("pclient -s 192.168.0.44 -f " + pedScriptPath + " > " + filePath)

        parseFile()
    generateCovMatrix()

pedestalTree.GetTree().Write()
outFile.Close()
