import os
import time
import threading
from ROOT import *
import ROOT
import numpy as np
import pandas as pd
from array import array
import argparse

# function to get the result of the limit extraction -> it also waits for the result to be created if it has not been yet
# the function is deliberately inefficient so that we lower the probability of reading the result in the exact same moment of its creation
def get_result(file_path):
    # check that the limits were calculated
    dir_to_check = file_path.split("/ggHH")[0]
    if not os.path.exists(dir_to_check):
        return 0

    while not os.path.exists(file_path):
        time.sleep(10) # sleep for 10 seconds -> only 10 because generally the file is produced rapidely

    found = False
    os.system('chmod 777 '+file_path)
    while os.path.exists(file_path):
        limits_file = open(file_path,'r')
        lines = limits_file.readlines()
        if "Done" in lines[-1]:
            if "50.0" in lines[-5]:
                try:
                    result = float(lines[-5].split('< ')[1].replace('\n',''))
                except ValueError:
                    limits_file.close()
                else:
                    limits_file.close()
                    break
        time.sleep(30) # sleep for 30 seconds -> only 30 because it is generally pretty fast (like 3/4 minutes max)
    return result

# function to write lines at the beginning of file
def prepend_line(file_name, line):
    # define name of temporary dummy file
    dummy_file = file_name + '.bak'
    # open original file in read mode and dummy file in write mode
    with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Write given line to the dummy file
        write_obj.write(line + '\n')
        # Read lines from original file one by one and append them to the dummy file
        for line in read_obj:
            write_obj.write(line)
    # remove original file
    os.remove(file_name)
    # Rename dummy file as the original file
    os.rename(dummy_file, file_name)

# function to add the overflow bin to the historam
def addOverFlow (histo):
    dummy = TH1F ("tempo",histo.GetTitle (),histo.GetNbinsX () + 1, histo.GetXaxis ().GetXmin (),histo.GetXaxis ().GetXmax () + histo.GetBinWidth (1))

    for iBin in range(1,histo.GetNbinsX () + 2):
        dummy.SetBinContent (iBin, histo.GetBinContent (iBin))
        dummy.SetBinError (iBin, histo.GetBinError (iBin))

    if(histo.GetDefaultSumw2()):
        dummy.Sumw2 ()

    name = histo.GetName ()
    histo.SetName ("trash")
    if variable == "BDToutSM_kl_1": dummy.GetXaxis().SetTitle("HH vs t#bar{t} BDT score")
    elif variable == "DNNoutSM_kl_1": dummy.GetXaxis().SetTitle("HH vs t#bar{t} DNN score")
    dummy.SetName (name)
    histo, dummy = dummy, histo
    return histo

# function to get the list of histos
def retrieveHistos (rootFile, namelist, var, sel, reg):
    res = {}
    for name in namelist:
        fullName = name + "_" + sel + "_" + reg + "_" + var
        if not rootFile.GetListOfKeys().Contains(fullName):
            print "*** WARNING: histo " , fullName , " not available"
            continue
        h = rootFile.Get(fullName)
        res[name] = h
    return res

# function to get the single histos
def getHisto (histoName,inputList,doOverflow):
    for idx, name in enumerate(inputList):
        if (name.startswith(histoName) and name.endswith(histoName)):
            h = inputList[name].Clone (histoName)
            if doOverflow: h = addOverFlow(h)
            break
    return h

# remove negative bins and reset yield accordingly
def makeNonNegativeHistos(h):
    integral = h.Integral()
    for b in range (1, h.GetNbinsX()+1):
        if (h.GetBinContent(b) < 0):
            h.SetBinContent (b, 0)
    integralNew = h.Integral()
    if (integralNew != integral):
        print "** INFO: removed neg bins from histo " , h.GetName()

    if integralNew == 0:
        h.Scale(0)
    else:
        h.Scale(integral/integralNew)

# fct to sum histograms
def makeSum(sumName, histoList):
    for i,h in enumerate(histoList):
        if i == 0: hsum = h.Clone(sumName)
        else: hsum.Add(h)
    return hsum

# fct to adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
def adjust_new_bins(new_bins_edges):
    i = 0
    j = 0
    for new_edge in new_bins_edges:
        if new_edge == variable_min:
            i += 1
            j += 1
            continue
        if new_edge == variable_max:
            break
        while abs(new_edge - old_bins_edges[i]) > abs(new_edge - old_bins_edges[i+1]):
            i += 1
        new_bins_edges[j] = old_bins_edges[i]
        j += 1

# SINGLE FUNCTION CONTAINING ALL THE STEPS FOR A COMPLETE ANALYSIS
# -> WORKS ONLY FOR THE 2D BIN-DISTRIBUTION SCAN (because of the specific names that we give to files and folders
def HPlimit_extraction(nBins,new_bins_edges,mode_str,selection):
    # in the following sel is the name of the directory
    # in the following other_sel are used for the rebinning (so it needs to be the entire selection name)
    # PLUS
    # if the three configurations before the one we are testing were all unsuccesful then we do not test the next one
    # this is just to speed up the scan ov the hyperparameters space
    if selection == "s2b0jresolvedMcut":
        if nBins >= 16:
            if df_results_2b0j [nBins-2][mode_str] == -993:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.993
                return result
            if df_results_2b0j[nBins-6][mode_str] == -995 or df_results_2b0j[nBins-6][mode_str] == -997 or df_results_2b0j[nBins-6][mode_str] == -999:
                if df_results_2b0j[nBins-4][mode_str] == -995 or df_results_2b0j[nBins-4][mode_str] == -997 or df_results_2b0j[nBins-4][mode_str] == -999:
                    if df_results_2b0j[nBins-2][mode_str] == -995 or df_results_2b0j[nBins-2][mode_str] == -997 or df_results_2b0j[nBins-2][mode_str] == -999:
                        print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                        result = -0.993
                        return result
        sel = "2b0j"
        other_sel1 = "sboostedLLMcut"
        other_sel2 = "s1b1jresolvedMcut"
        other_sel3 = "VBFloose"
        other_sel4 = "VBFtight"
    elif selection == "sboostedLLMcut":
        if nBins >= 16:
            if df_results_boosted[nBins-2][mode_str] == -993:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.993
                return result
            if df_results_boosted[nBins-6][mode_str] == -995 or df_results_boosted[nBins-6][mode_str] == -997 or df_results_boosted[nBins-6][mode_str] == -999:
                if df_results_boosted[nBins-4][mode_str] == -995 or df_results_boosted[nBins-4][mode_str] == -997 or df_results_boosted[nBins-4][mode_str] == -999:
                    if df_results_boosted[nBins-2][mode_str] == -995 or df_results_boosted[nBins-2][mode_str] == -997 or df_results_boosted[nBins-2][mode_str] == -999:
                        print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                        result = -0.993
                        return result
        sel = "boosted"
        other_sel1 = "s2b0jresolvedMcut"
        other_sel2 = "s1b1jresolvedMcut"
        other_sel3 = "VBFloose"
        other_sel4 = "VBFtight"
    elif selection == "s1b1jresolvedMcut":
        if nBins >= 16:
            if df_results_1b1j[nBins-2][mode_str] == -993:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.993
                return result
            if df_results_1b1j[nBins-6][mode_str] == -995 or df_results_1b1j[nBins-6][mode_str] == -997 or df_results_1b1j[nBins-6][mode_str] == -999:
                if df_results_1b1j[nBins-4][mode_str] == -995 or df_results_1b1j[nBins-4][mode_str] == -997 or df_results_1b1j[nBins-4][mode_str] == -999:
                    if df_results_1b1j[nBins-2][mode_str] == -995 or df_results_1b1j[nBins-2][mode_str] == -997 or df_results_1b1j[nBins-2][mode_str] == -999:
                        print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                        result = -0.993
                        return result
        sel = "1b1j"
        other_sel1 = "s2b0jresolvedMcut"
        other_sel2 = "sboostedLLMcut"
        other_sel3 = "VBFloose"
        other_sel4 = "VBFtight"
    elif selection == "VBFloose":
        if nBins >= 16:
            if df_results_VBFloose[nBins-2][mode_str] == -993:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.993
                return result
            if df_results_VBFloose[nBins-6][mode_str] == -995 or df_results_VBFloose[nBins-6][mode_str] == -997 or df_results_VBFloose[nBins-6][mode_str] == -999:
                if df_results_VBFloose[nBins-4][mode_str] == -995 or df_results_VBFloose[nBins-4][mode_str] == -997 or df_results_VBFloose[nBins-4][mode_str] == -999:
                    if df_results_VBFloose[nBins-2][mode_str] == -995 or df_results_VBFloose[nBins-2][mode_str] == -997 or df_results_VBFloose[nBins-2][mode_str] == -999:
                        print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                        result = -0.993
                        return result
        sel = "VBFloose"
        other_sel1 = "s2b0jresolvedMcut"
        other_sel2 = "sboostedLLMcut"
        other_sel3 = "s1b1jresolvedMcut"
        other_sel4 = "VBFtight"
    elif selection == "VBFtight":
        if nBins >= 16:
            if df_results_VBFtight[nBins-2][mode_str] == -993:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.993
                return result
            if df_results_VBFtight[nBins-6][mode_str] == -995 or df_results_VBFtight[nBins-6][mode_str] == -997 or df_results_VBFtight[nBins-6][mode_str] == -999:
                if df_results_VBFtight[nBins-4][mode_str] == -995 or df_results_VBFtight[nBins-4][mode_str] == -997 or df_results_VBFtight[nBins-4][mode_str] == -999:
                    if df_results_VBFtight[nBins-2][mode_str] == -995 or df_results_VBFtight[nBins-2][mode_str] == -997 or df_results_VBFtight[nBins-2][mode_str] == -999:
                        print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,selection,nBins))
                        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                        result = -0.993
                        return result
        sel = "VBFtight"
        other_sel1 = "s2b0jresolvedMcut"
        other_sel2 = "sboostedLLMcut"
        other_sel3 = "s1b1jresolvedMcut"
        other_sel4 = "VBFloose"
    else:
        print("** WRONG SELECTION NAME ENTERED. SELECTIONS ARE: s2b0jresolvedMcut, s1b1jresolvedMcut, sboostedLLMcut, VBFloose and VBFtight **")
        print("** EXITING PROGRAM **")
        sys.exit()

    # if the calculation of the bins edges goes wrong it returns the result [-1,1]
    # when this happens we skip the calculation of the limit
    # we return a specific value to know what happened at the end
    if len(new_bins_edges) == 2:
        print("\n** THE {0} {1} {2}bins CONFIGURATION WAS NOT CALCULATED DUE TO PRECISION LIMITATION IN THE QUANTILE CALCULATION **".format(mode_str,selection,nBins))
        print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
        result = -0.995
        return result

    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    adjust_new_bins(new_bins_edges)

    # protection against super scattered distributions -> it goes toward the continuous limit calculation and we don't want it
    # if the binning we get is to thin we reject it -> 0.009 is somewhat arbitrary and correspond to 222 same width bins
    # we return a specific value to know what happened at the end
    if mode_str != "ConstSize":
        for index in range(0,len(new_bins_edges)-1):
            if new_bins_edges[index] <= variable_min+abs(variable_max-variable_min)/4: continue # we do not apply this protection for the first 4th of the score
            if abs(new_bins_edges[index] - new_bins_edges[index+1]) <= 0.009:
                print("\n** THE {0} {1} {2}bins CONFIGURATION IS TOO SCATTERED **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.999
                return result

    # create folder of the specific mode and number of bins we are testing and copy cfgs in it
    mkdir_cmd = "mkdir NumbAndDistribScanSteps_{3}{4}{5}/{0}/{2}/bins_{1}; mkdir NumbAndDistribScanSteps_{3}{4}{5}/{0}/{2}/bins_{1}/NONweighted".format(mode_str,str(nBins),sel,channel,year,variable)
    os.system(mkdir_cmd)
    tag = "{0}_Legacy{1}_binOptimization.cfg".format(channel,year)
    if variable == "BDToutSM_kl_1":
        inDir = "{1}/{0}/BDT_dataNonRebinned1M".format(channel,datasets_dir)
    elif variable == "DNNoutSM_kl_1":
        inDir = "{1}/{0}/DNN500k".format(channel,datasets_dir)
    copy_cmd = "cp -a {2}/mainCfg_{0} NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/; cp -a {2}/selectionCfg_{0} NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/; cp -a {2}/sampleCfg_Legacy{6}.cfg NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/; cp -a {2}/outPlotter.root NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/".format(tag,str(nBins),inDir,mode_str,sel,channel,year,variable)
    os.system(copy_cmd)
    inDir_NONweighted = inDir+"_NONweighted"
    tag1 = "{0}_Legacy{1}_NONweighted.cfg".format(channel,year)
    copy_cmd = "cp -a {2}/mainCfg_{0} NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/NONweighted; cp -a {2}/selectionCfg_{8} NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/NONweighted; cp -a {2}/sampleCfg_Legacy{6}.cfg NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/NONweighted; cp -a {2}/outPlotter.root NumbAndDistribScanSteps_{5}{6}{7}/{3}/{4}/bins_{1}/NONweighted".format(tag,str(nBins),inDir_NONweighted,mode_str,sel,channel,year,variable,tag1)
    os.system(copy_cmd)

    # append rebinning section in the mainCfg
    mainCfg = open("NumbAndDistribScanSteps_{4}{5}{6}/{2}/{3}/bins_{0}/mainCfg_{1}".format(str(nBins),tag,mode_str,sel,channel,year,variable), "a")
    mainCfg.write("[pp_rebin]\n")
    # convert new binning edges to string and write them in the mainCfg
    edges_string = np.array2string(np.array(new_bins_edges), separator=',', max_line_width=None, precision=20).replace('\n','')
    mainCfg.write("r1 = {0}, {1}, %s \n".format(variable,selection) % edges_string.replace('[','').replace(']',''))
    mainCfg.write("r2 = {0}, {1}, {2}, {3} \n".format(variable,other_sel1,variable_min,variable_max)) # we rebin also the ones we are not using in this moment otherwise the wrapper will take a lifetime to give the results -> we use a sinlge bin to be as fast as possible
    mainCfg.write("r3 = {0}, {1}, {2}, {3} \n".format(variable,other_sel2,variable_min,variable_max))
    mainCfg.write("r4 = {0}, {1}, {2}, {3} \n".format(variable,other_sel3,variable_min,variable_max))
    mainCfg.write("r5 = {0}, {1}, {2}, {3} \n".format(variable,other_sel4,variable_min,variable_max))
    mainCfg.close()

    # call combineFillerOutputs.py
    comb_cmd = "python ../scripts/combineFillerOutputs.py --dir NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/".format(str(nBins),mode_str,sel,channel,year,variable)
    os.system(comb_cmd)
    comb_cmd = "python ../scripts/combineFillerOutputs.py --dir NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/NONweighted".format(str(nBins),mode_str,sel,channel,year,variable)
    os.system(comb_cmd)

    # protection against almost empty bins -> can create bias in the final result
    RootToCheck = TFile.Open("NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/analyzedOutPlotter.root".format(str(nBins),mode_str,sel,channel,year,variable))
    bkgList = ['QCD', 'TT', 'DYtot', 'others']
    hBkgs = retrieveHistos(RootToCheck,bkgList,variable,selection,"SR")
    doOverflow = False
    hQCD = getHisto("QCD",hBkgs,doOverflow)
    hTT = getHisto("TT",hBkgs,doOverflow)
    hDY = getHisto("DYtot",hBkgs,doOverflow)
    hOthers = getHisto("others",hBkgs,doOverflow)
    # protection against negative bins
    makeNonNegativeHistos(hQCD)
    makeNonNegativeHistos(hTT)
    makeNonNegativeHistos(hDY)
    makeNonNegativeHistos(hOthers)
    hBkgList = [hQCD, hTT, hDY, hOthers]
    hBackground = makeSum("background",hBkgList)
    #
    RootToCheck_NONweighted = TFile.Open("NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/NONweighted/analyzedOutPlotter.root".format(str(nBins),mode_str,sel,channel,year,variable))
    hBkgs_NONweighted = retrieveHistos(RootToCheck,bkgList,variable,selection,"SR")
    doOverflow = False
    hQCD_NONweighted = getHisto("QCD",hBkgs,doOverflow)
    hTT_NONweighted = getHisto("TT",hBkgs,doOverflow)
    hDY_NONweighted = getHisto("DYtot",hBkgs,doOverflow)
    hOthers_NONweighted = getHisto("others",hBkgs,doOverflow)
    # protection against negative bins
    makeNonNegativeHistos(hQCD_NONweighted)
    makeNonNegativeHistos(hTT_NONweighted)
    makeNonNegativeHistos(hDY_NONweighted)
    makeNonNegativeHistos(hOthers_NONweighted)
    for i in range(2,nBins+1):
        if hBackground.GetBinContent(i-1) > 0.15:
            if hBackground.GetBinContent(i) < 0.15 or hTT_NONweighted < 1 or hDY_NONweighted < 1: # we choose 0.15 cause then 1 is at the edge of 2sigma
                print("\n** "+str(hBackground.GetBinContent(i-1))+" @ bin "+str(i-1)+" **")
                print("** "+str(hBackground.GetBinContent(i))+" @ bin "+str(i)+" **")
                print("** THE {0} {1} {2}bin CONFIGURATION CAN CAUSE BIAS IN THE LIMIT EXTRACTION **".format(mode_str,selection,nBins))
                print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
                result = -0.997 # we return a specific value to know what happened at the end
                return result
    # delete the variables to avoid strange things happening the next time we call the limit calculation
    del RootToCheck, hBkgs, doOverflow, hQCD, hTT, hDY, hOthers, hBkgList, hBackground

    # call wrapperHistos.py
    wrapper_cmd = "python wrapperHistos.py -f NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/analyzedOutPlotter.root -c {3} -o bins_{0} -d NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0} -a 'GGF' -y {4}".format(str(nBins),mode_str,sel,channel,year,variable)
    os.system(wrapper_cmd)

    # delete the first lines in makeCategories_NandD.sh with the old exports (by wrong we mean 'of the old iteration')
    # and re-write them in makeCategories_NandD.sh with the correct exports
    file = open("makeCategories_NandD{0}.sh".format(year),"r")
    lines = file.readlines()
    file.close()
    rm_cmd = "rm makeCategories_NandD{0}.sh".format(year)
    os.system(rm_cmd)
    file = open("makeCategories_NandD{0}.sh".format(year),"w")
    file.writelines(lines[7:])
    file.close()
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export VAR="{0}"'.format(variable))
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export YEAR="{0}"'.format(year))
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export SELECTIONS="{0}"'.format(selection))
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export LEPTONS="{0}"'.format(channel))
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/NumbAndDistribScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/"'.format(str(nBins),mode_str,sel,channel,year,variable))
    prepend_line("makeCategories_NandD{0}.sh".format(year),'export TAG="bins_{0}"'.format(str(nBins)))
    prepend_line("makeCategories_NandD{0}.sh".format(year),"#!/bin/bash")

    # call makeCategories_NandD.sh
    limits_cmd = "./makeCategories_NandD{0}.sh".format(year)
    os.system('chmod 777 makeCategories_NandD{0}.sh'.format(year))
    os.system(limits_cmd)

    print("\n** {0} {1} {2}bins DONE **\n".format(mode_str,selection,nBins))

    return 0


###############################################################################
################################# MAIN PROGRAM ################################
###############################################################################

parser = argparse.ArgumentParser(description='Command line parser of hyperparameters scan options')
parser.add_argument('--ch', dest='ch', help='channel', default=None)
parser.add_argument('--year', dest='year', help='channel', default=None)
parser.add_argument('--var', dest='var', help='channel', default=None)
args = parser.parse_args()

global year
year = args.year

global variable
variable = args.var

global channel
channel = args.ch

global datasets_dir
datasets_dir = "/data_CMS/cms/motta/PhDwork/HHanalysis/binOptDataset/Legacy{0}/".format(year)

print("** VARIABLE: {0} **".format(variable))
print("** CHANNEL: {0} **".format(channel))
print("** YEAR: {0} **\n".format(year))

# start clock
start = time.time()

# take a histogram as template
if variable == "BDToutSM_kl_1":
    inRoot = TFile.Open("{1}/{0}/BDT_dataNonRebinned1M/analyzedOutPlotter.root".format(channel,datasets_dir))
elif variable == "DNNoutSM_kl_1":
    inRoot = TFile.Open("{1}/{0}/DNN500k/analyzedOutPlotter.root".format(channel,datasets_dir))
else:
    print("** ERROR IN THE NAME OF THE VARIABLE **")
    print("** EXITING PROGRAM **")
    sys.exit()
templateName = "GGHHSM_s2b0jresolvedMcut_SR_{0}".format(variable)
template = inRoot.Get(templateName)
# old_bins_edges contains the edges of the bins of the 100k/1M/3M histograms -> they are used for the rebinning through combineFillerOutputs.py
nPoints  = template.GetNbinsX()
global old_bins_edges
old_bins_edges = [template.GetBinLowEdge(0)]
for ibin in range (1, nPoints+1):
    old_bins_edges.append(template.GetBinLowEdge(ibin+1))

# get the range in which the variable is defined; e.g. BDT = [-1,1] and DNN = [0,1]
global variable_min
variable_min = round(old_bins_edges[0],0)
global variable_max
variable_max = round(old_bins_edges[-1],0)

# here we choose the correct selections depending on the year and channel we are considering
if year != "2016" and channel == "TauTau":
    # TauTau (only 2017/2018) selections
    selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFloose", "VBFtight"]
else:
    # ETau/MuTau (all years) + TauTau (2016) selections
    selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFloose"]

bins_window = range(10,12,2)

# CREATE ALL THE DATAFRAMES OF THE DIFFERENT DISTRIBUTIONS -> THEY WILL CONTAIN THE NEW BINNINGS
# ConstSize
df_ConstSize = pd.DataFrame(index=selections, columns=bins_window)
for index in df_ConstSize.index.values:
    for column in df_ConstSize.columns.values:
        df_ConstSize[column][index] = []
# FlatS
df_flatS = pd.DataFrame(index=selections, columns=bins_window)
for index in df_flatS.index.values:
    for column in df_flatS.columns.values:
        df_flatS[column][index] = []
# FlatB
df_flatB = pd.DataFrame(index=selections, columns=bins_window)
for index in df_flatB.index.values:
    for column in df_flatB.columns.values:
        df_flatB[column][index] = []
# FlatSB
df_flatSB = pd.DataFrame(index=selections, columns=bins_window)
for index in df_flatSB.index.values:
    for column in df_flatSB.columns.values:
        df_flatSB[column][index] = []


#########################################################################
# INSIDE THIS LOOP WE FILL THE DFs FOR ConstSize, FlatS, FlatB, FlatSB
bkgList = ['QCD', 'TT', 'DYtot', 'others']
sigList = ['GGHHSM']
doOverflow = False
for select in selections:
    # there is no iterative way of accessing these histos becase python does not know how to use += for the TH1Fs
    hBkgs = retrieveHistos(inRoot,bkgList,variable,select,"SR")
    hSigs = retrieveHistos(inRoot,sigList,variable,select,"SR")
    hSgn = getHisto("GGHHSM",hSigs,doOverflow)
    hQCD = getHisto("QCD",hBkgs,doOverflow)
    hTT = getHisto("TT",hBkgs,doOverflow)
    hDY = getHisto("DYtot",hBkgs,doOverflow)
    hOthers = getHisto("others",hBkgs,doOverflow)
    # protection against negative bins
    makeNonNegativeHistos(hSgn)
    makeNonNegativeHistos(hQCD)
    makeNonNegativeHistos(hTT)
    makeNonNegativeHistos(hDY)
    makeNonNegativeHistos(hOthers)
    hBkgList = [hQCD, hTT, hDY, hOthers]
    hBkg = makeSum("background",hBkgList)

    ###################################################
    # ConstSize (BDToutSM_kl_1/DNNoutSM_kl_1 bins of constant width)
    k = 0
    for column in df_ConstSize.columns.values:
        # define array of the new bins edges based on the number of bins to be tested
        df_ConstSize[column][select].append(variable_min)
        step = (variable_max-variable_min)/float(bins_window[k])
        i = 0
        # the loop looks a bit redundant with the if inside the while, but it is to protect against having both 0.99999999 and 1 at the end of the array
        while df_ConstSize[column][select][i] < variable_max:
            df_ConstSize[column][select].append(df_ConstSize[column][select][i]+step)
            if df_ConstSize[column][select][i+1]+step > variable_max+0.00001:
                df_ConstSize[column][select].remove(df_ConstSize[column][select][i+1])
                df_ConstSize[column][select].append(variable_max)
                break
            i += 1
        k += 1

    ####################################
    # FlatS (BDToutSM_kl_1/DNNoutSM_kl_1 flat in sgn)
    template = hSgn
    integral = float(template.Integral())
    axis = template.GetXaxis()
    k = 0
    for column in df_flatS.columns.values:
        y = 0
        df_flatS[column][select].append(variable_min)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatS[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatS[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatS[column][select].append(variable_max)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatS[column][select]) - (bins_window[k]+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,(df_flatS[column][select][0]+df_flatS[column][select][1])/2)
        elif len(df_flatS[column][select]) - (bins_window[k]+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/3.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 2BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_window[k]+1) == -3: # if three bins are missing split the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/4.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+3*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 3BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_window[k]+1) <= -4:
            print("** THE FlatS "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatS[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** SUBSTITUTING WITH SINGLE BIN **")
            df_flatS[column][select] = [variable_min,variable_max]
        k += 1
    # delete the variables to allow next step
    del template

    ####################################
    # FlatB (BDToutSM_kl_1/DNNoutSM_kl_1 flat in bkg)
    template = hBkg
    integral = float(template.Integral())
    axis = template.GetXaxis()
    k = 0
    for column in df_flatB.columns.values:
        y = 0
        df_flatB[column][select].append(variable_min)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatB[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatB[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatB[column][select].append(variable_max)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatB[column][select]) - (bins_window[k]+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,(df_flatB[column][select][0]+df_flatB[column][select][1])/2)
        elif len(df_flatB[column][select]) - (bins_window[k]+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatB[column][select][0]-df_flatB[column][select][1])/3.
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,df_flatB[column][select][0]+2*step)
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,df_flatB[column][select][0]+step)
            print("** FlatB "+select+" 2BIN CORRECTION **")
        elif len(df_flatB[column][select]) - (bins_window[k]+1) == -3: # if three bins are missing spit the first in three equal size bins
            step = abs(df_flatB[column][select][0]-df_flatB[column][select][1])/4.
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,df_flatB[column][select][0]+3*step)
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,df_flatB[column][select][0]+2*step)
            df_flatB[column][select] = np.insert(df_flatB[column][select],1,df_flatB[column][select][0]+step)
            print("** FlatB "+select+" 3BIN CORRECTION DONE **")
        elif len(df_flatB[column][select]) - (bins_window[k]+1) <= -4:
            print("** THE FlatB "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatB[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** SUBSTITUTING WITH SINGLE BIN **")
            df_flatB[column][select] = [variable_min,variable_max]
        k += 1
    # delete the variables to allow next step
    del template

    ###########################################
    # FlatSB (BDToutSM_kl_1/DNNoutSM_kl_1 flat in sgn+bkg)
    template = hSgn + hBkg
    integral = float(template.Integral())
    axis = template.GetXaxis()
    k = 0
    for column in df_flatSB.columns.values:
        y = 0
        df_flatSB[column][select].append(variable_min)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatSB[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatSB[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatSB[column][select].append(variable_max)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatSB[column][select]) - (bins_window[k]+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,(df_flatSB[column][select][0]+df_flatSB[column][select][1])/2)
        elif len(df_flatSB[column][select]) - (bins_window[k]+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatSB[column][select][0]-df_flatSB[column][select][1])/3.
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,df_flatSB[column][select][0]+2*step)
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,df_flatSB[column][select][0]+step)
            print("** FlatSB "+select+" 2BIN CORRECTION DONE **")
        elif len(df_flatSB[column][select]) - (bins_window[k]+1) == -3: # if three bins are missing spit the first in three equal size bins
            step = abs(df_flatSB[column][select][0]-df_flatSB[column][select][1])/4.
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,df_flatSB[column][select][0]+3*step)
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,df_flatSB[column][select][0]+2*step)
            df_flatSB[column][select] = np.insert(df_flatSB[column][select],1,df_flatSB[column][select][0]+step)
            print("** FlatSB "+select+" 3BIN CORRECTION DONE **")
        elif len(df_flatSB[column][select]) - (bins_window[k]+1) <= -4:
            print("** THE FlatSB "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatSB[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** SUBSTITUTING WITH SINGLE BIN **")
            df_flatSB[column][select] = [variable_min,variable_max]
        k += 1
    # delete the variables to avoid strange things happening at the next round of the select loop
    del template
    del hBkgs, hSigs, hSgn, hQCD, hTT, hDY, hOthers, hBkgList, hBkg

##################################
# DO THE ACTUAL DISTRIBUTION SCAN
# mode_str STRINGS FOR THE HPlimit_extraction FUNCTION ARE:
# FlatS
# FlatB
# FlatSB
# ConstSize

# create the folders that will contain all the results
mkdir_cmd = "mkdir NumbAndDistribScanSteps_{0}{1}{2}".format(channel,year,variable)
os.system(mkdir_cmd)
cp_prog_cmd = "cp binNumberAndDistributionOptimizer.py NumbAndDistribScanSteps_{0}{1}{2}/".format(channel,year,variable)
os.system(cp_prog_cmd)
mkdir_cmd1 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize".format(channel,year,variable)
os.system(mkdir_cmd1)
mkdir_cmd2 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS/2b0j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB/2b0j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB/2b0j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize/2b0j".format(channel,year,variable)
os.system(mkdir_cmd2)
mkdir_cmd3 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS/1b1j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB/1b1j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB/1b1j; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize/1b1j".format(channel,year,variable)
os.system(mkdir_cmd3)
mkdir_cmd4 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS/boosted; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB/boosted; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB/boosted; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize/boosted".format(channel,year,variable)
os.system(mkdir_cmd4)
mkdir_cmd5 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS/VBFloose; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB/VBFloose; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB/VBFloose; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize/VBFloose".format(channel,year,variable)
os.system(mkdir_cmd5)
if year != "2016" and channel == "TauTau":
    mkdir_cmd6 = "mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatS/VBFtight; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatB/VBFtight; mkdir NumbAndDistribScanSteps_{0}{1}{2}/FlatSB/VBFtight; mkdir NumbAndDistribScanSteps_{0}{1}{2}/ConstSize/VBFtight".format(channel,year,variable)
    os.system(mkdir_cmd6)

# create a two dataframes that will contain all the results of the distribution scan
global df_results_2b0j, df_results_boosted, df_results_1b1j, df_results_VBFloose
if year != "2016" and channel == "TauTau": global df_results_VBFtight
df_results_2b0j = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)
df_results_boosted = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)
df_results_1b1j = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)
df_results_VBFloose = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)
if year != "2016" and channel == "TauTau": df_results_VBFtight = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)

# fill them
for column in df_results_2b0j.columns.values:
    df_results_2b0j[column]['ConstSize'] = HPlimit_extraction(int(column),df_ConstSize[column]['s2b0jresolvedMcut'],'ConstSize','s2b0jresolvedMcut')*1000.
    df_results_2b0j[column]['FlatS'] = HPlimit_extraction(int(column),df_flatS[column]['s2b0jresolvedMcut'],'FlatS','s2b0jresolvedMcut')*1000.
    df_results_2b0j[column]['FlatB'] = HPlimit_extraction(int(column),df_flatB[column]['s2b0jresolvedMcut'],'FlatB','s2b0jresolvedMcut')*1000.
    df_results_2b0j[column]['FlatSB'] = HPlimit_extraction(int(column),df_flatSB[column]['s2b0jresolvedMcut'],'FlatSB','s2b0jresolvedMcut')*1000.
    #------
    df_results_boosted[column]['ConstSize'] = HPlimit_extraction(int(column),df_ConstSize[column]['sboostedLLMcut'],'ConstSize','sboostedLLMcut')*1000.
    df_results_boosted[column]['FlatS'] = HPlimit_extraction(int(column),df_flatS[column]['sboostedLLMcut'],'FlatS','sboostedLLMcut')*1000.
    df_results_boosted[column]['FlatB'] = HPlimit_extraction(int(column),df_flatB[column]['sboostedLLMcut'],'FlatB','sboostedLLMcut')*1000.
    df_results_boosted[column]['FlatSB'] = HPlimit_extraction(int(column),df_flatSB[column]['sboostedLLMcut'],'FlatSB','sboostedLLMcut')*1000.
    #------
    df_results_1b1j[column]['ConstSize'] = HPlimit_extraction(int(column),df_ConstSize[column]['s1b1jresolvedMcut'],'ConstSize','s1b1jresolvedMcut')*1000.
    df_results_1b1j[column]['FlatS'] = HPlimit_extraction(int(column),df_flatS[column]['s1b1jresolvedMcut'],'FlatS','s1b1jresolvedMcut')*1000.
    df_results_1b1j[column]['FlatB'] = HPlimit_extraction(int(column),df_flatB[column]['s1b1jresolvedMcut'],'FlatB','s1b1jresolvedMcut')*1000.
    df_results_1b1j[column]['FlatSB'] = HPlimit_extraction(int(column),df_flatSB[column]['s1b1jresolvedMcut'],'FlatSB','s1b1jresolvedMcut')*1000.
    #------
    df_results_VBFloose[column]['ConstSize'] = HPlimit_extraction(int(column),df_ConstSize[column]['VBFloose'],'ConstSize','VBFloose')*1000.
    df_results_VBFloose[column]['FlatS'] = HPlimit_extraction(int(column),df_flatS[column]['VBFloose'],'FlatS','VBFloose')*1000.
    df_results_VBFloose[column]['FlatB'] = HPlimit_extraction(int(column),df_flatB[column]['VBFloose'],'FlatB','VBFloose')*1000.
    df_results_VBFloose[column]['FlatSB'] = HPlimit_extraction(int(column),df_flatSB[column]['VBFloose'],'FlatSB','VBFloose')*1000.
    #------
    if year != "2016" and channel == "TauTau":
        df_results_VBFtight[column]['ConstSize'] = HPlimit_extraction(int(column),df_ConstSize[column]['VBFtight'],'ConstSize','VBFtight')*1000.
        df_results_VBFtight[column]['FlatS'] = HPlimit_extraction(int(column),df_flatS[column]['VBFtight'],'FlatS','VBFtight')*1000.
        df_results_VBFtight[column]['FlatB'] = HPlimit_extraction(int(column),df_flatB[column]['VBFtight'],'FlatB','VBFtight')*1000.
        df_results_VBFtight[column]['FlatSB'] = HPlimit_extraction(int(column),df_flatSB[column]['VBFtight'],'FlatSB','VBFtight')*1000.

# get the results of the limit extractions (-> the loop above only saves aeb, tsd and qcl)
for dist in ["ConstSize", "FlatB", "FlatS", "FlatSB"]:
    for bin in bins_window:
        df_results_2b0j[bin][dist] += get_result("NumbAndDistribScanSteps_{2}{4}{3}/{0}/2b0j/bins_{1}/cards_{2}_bins_{1}/ggHH_bbtt11s2b0jresolvedMcut{3}/out_Asym_ggHH_bbtt11_blind.log".format(dist,bin,channel,variable,year))*1000.
        df_results_boosted[bin][dist] += get_result("NumbAndDistribScanSteps_{2}{4}{3}/{0}/boosted/bins_{1}/cards_{2}_bins_{1}/ggHH_bbtt11sboostedLLMcut{3}/out_Asym_ggHH_bbtt11_blind.log".format(dist,bin,channel,variable,year))*1000.
        df_results_1b1j[bin][dist] += get_result("NumbAndDistribScanSteps_{2}{4}{3}/{0}/1b1j/bins_{1}/cards_{2}_bins_{1}/ggHH_bbtt11s1b1jresolvedMcut{3}/out_Asym_ggHH_bbtt11_blind.log".format(dist,bin,channel,variable,year))*1000.
        df_results_VBFloose[bin][dist] += get_result("NumbAndDistribScanSteps_{2}{4}{3}/{0}/VBFloose/bins_{1}/cards_{2}_bins_{1}/ggHH_bbtt11VBFloose{3}/out_Asym_ggHH_bbtt11_blind.log".format(dist,bin,channel,variable,year))*1000.
        if year != "2016" and channel == "TauTau":
            df_results_VBFtight[bin][dist] += get_result("NumbAndDistribScanSteps_{2}{4}{3}/{0}/VBFtight/bins_{1}/cards_{2}_bins_{1}/ggHH_bbtt11VBFtightMcut{3}/out_Asym_ggHH_bbtt11_blind.log".format(dist,bin,channel,variable,year))*1000.

# a little bit of cosmetics for the DataFrames
df_results_2b0j = df_results_2b0j.rename(index={'FlatSB':'FlatS+B'})
df_results_boosted = df_results_boosted.rename(index={'FlatSB':'FlatS+B'})
df_results_1b1j = df_results_1b1j.rename(index={'FlatSB':'FlatS+B'})
df_results_VBFloose = df_results_VBFloose.rename(index={'FlatSB':'FlatS+B'})
if year != "2016" and channel == "TauTau": df_results_VBFtight = df_results_VBFtight.rename(index={'FlatSB':'FlatS+B'})
for column in df_results_2b0j.columns.values:
    for index in df_results_2b0j.index.values:
        if df_results_2b0j[column][index] == -995: df_results_2b0j[column][index] = "q.c.l." # Quantile Calculation Limit (-> not able to produce enough bins)
        if df_results_boosted[column][index] == -995: df_results_boosted[column][index] = "q.c.l."
        if df_results_1b1j[column][index] == -995: df_results_1b1j[column][index] = "q.c.l."
        if df_results_VBFloose[column][index] == -995: df_results_VBFloose[column][index] = "q.c.l."
        if year != "2016" and channel == "TauTau" and df_results_VBFtight[column][index] == -995: df_results_VBFtight[column][index] = "q.c.l."
        #------
        if df_results_2b0j[column][index] == -997: df_results_2b0j[column][index] = "a.e.b." # Almost Empty Bin (the bin contains to few events of bkg -> can create bias)
        if df_results_boosted[column][index] == -997: df_results_boosted[column][index] = "a.e.b."
        if df_results_1b1j[column][index] == -997: df_results_1b1j[column][index] = "a.e.b."
        if df_results_VBFloose[column][index] == -997: df_results_VBFloose[column][index] = "a.e.b."
        if year != "2016" and channel == "TauTau" and df_results_VBFtight[column][index] == -997: df_results_VBFtight[column][index] = "a.e.b."
        #------
        if df_results_2b0j[column][index] == -999: df_results_2b0j[column][index] = "t.s.d." # Too Scattered Plot (the binning is too fine -> don't want almost continuous extraction)
        if df_results_boosted[column][index] == -999: df_results_boosted[column][index] = "t.s.d."
        if df_results_1b1j[column][index] == -999: df_results_1b1j[column][index] = "t.s.d."
        if df_results_VBFloose[column][index] == -999: df_results_VBFloose[column][index] = "t.s.d."
        if year != "2016" and channel == "TauTau" and df_results_VBFtight[column][index] == -999: df_results_VBFtight[column][index] = "t.s.d."
        #------
        if df_results_2b0j[column][index] == -993: df_results_2b0j[column][index] = "---" # non tested combination due to unlikeliness of good result (make the scan faster)
        if df_results_boosted[column][index] == -993: df_results_boosted[column][index] = "---"
        if df_results_1b1j[column][index] == -993: df_results_1b1j[column][index] = "---"
        if df_results_VBFloose[column][index] == -993: df_results_VBFloose[column][index] = "---"
        if year != "2016" and channel == "TauTau" and df_results_VBFtight[column][index] == -993: df_results_VBFtight[column][index] = "---"
    df_results_2b0j = df_results_2b0j.rename(columns={column:str(column)+' bins'})
    df_results_boosted = df_results_boosted.rename(columns={column:str(column)+' bins'})
    df_results_1b1j = df_results_1b1j.rename(columns={column:str(column)+' bins'})
    df_results_VBFloose = df_results_VBFloose.rename(columns={column:str(column)+' bins'})
    if year != "2016" and channel == "TauTau": df_results_VBFtight = df_results_VBFtight.rename(columns={column:str(column)+' bins'})

# save the results
df_results_2b0j.to_html('NumbAndDistribScanSteps_{0}{1}{2}/NumbAndDistribScanResults_2b0j.html'.format(channel,year,variable))
df_results_boosted.to_html('NumbAndDistribScanSteps_{0}{1}{2}/NumbAndDistribScanResults_boosted.html'.format(channel,year,variable))
df_results_1b1j.to_html('NumbAndDistribScanSteps_{0}{1}{2}/NumbAndDistribScanResults_1b1j.html'.format(channel,year,variable))
df_results_VBFloose.to_html('NumbAndDistribScanSteps_{0}{1}{2}/NumbAndDistribScanResults_VBFloose.html'.format(channel,year,variable))
if year != "2016" and channel == "TauTau": df_results_VBFtight.to_html('NumbAndDistribScanSteps_{0}{1}{2}/NumbAndDistribScanResults_VBFtight.html'.format(channel,year,variable))


# stop clock and print time of running
end = time.time()
print('\n\nNumber of Bins and Distribution Scan running time = {0}h {1}m {2}s'.format(int((end-start)/3600.),int(((end-start)/3600.)%1*60),int((((end-start)/3600.)%1*60)%1*60)))









##########################################################################################################################
# SOME PRINTS TO CHECK IF THE BINNINGS WE ARE PRODUCING ARE CORRECT IN LEGTH OR IF WE ARE PRODUCING LESS BINS THAN NEEDED
# print("\n----------------------------------")
# print('\nFLAT S')
# print("2b0j")
# ok = True
# for column in df_flatS.columns.values:
#    if len(df_flatS[column]['s2b0jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['s2b0jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("boosted")
# ok = True
# for column in df_flatS.columns.values:
#    if len(df_flatS[column]['sboostedLLMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['sboostedLLMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("1b1j")
# ok = True
# for column in df_flatS.columns.values:
#    if len(df_flatS[column]['s1b1jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['s1b1jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFloose")
# ok = True
# for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFloose']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFloose']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFtight")
# ok = True
# for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFtight']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFtight']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
#
# print("\n----------------------------------")
# print('\nFLAT SB')
# print("2b0j")
# ok = True
# for column in df_flatSB.columns.values:
#    if len(df_flatSB[column]['s2b0jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatSB[column]['s2b0jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("boosted")
# ok = True
# for column in df_flatSB.columns.values:
#    if len(df_flatSB[column]['sboostedLLMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatSB[column]['sboostedLLMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("1b1j")
# ok = True
# for column in df_flatSB.columns.values:
#    if len(df_flatSB[column]['s1b1jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatSB[column]['s1b1jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFloose")
# ok = True
# for column in df_flatSB.columns.values:
#    if len(df_flatSB[column]['VBFloose']) != int(column)+1:
#        print("-> "+str(len(df_flatSB[column]['VBFloose']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFtight")
# ok = True
# for column in df_flatSB.columns.values:
#    if len(df_flatSB[column]['VBFtight']) != int(column)+1:
#        print("-> "+str(len(df_flatSB[column]['VBFtight']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
#
# print("\n----------------------------------")
# print('\nFLAT B')
# print("2b0j")
# ok = True
# for column in df_flatB.columns.values:
#    if len(df_flatB[column]['s2b0jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatB[column]['s2b0jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("boosted")
# ok = True
# for column in df_flatB.columns.values:
#    if len(df_flatB[column]['sboostedLLMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatB[column]['sboostedLLMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("1b1j")
# ok = True
# for column in df_flatB.columns.values:
#    if len(df_flatB[column]['s1b1jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatB[column]['s1b1jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFloose")
# ok = True
# for column in df_flatB.columns.values:
#    if len(df_flatB[column]['VBFloose']) != int(column)+1:
#        print("-> "+str(len(df_flatB[column]['VBFloose']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFtight")
# ok = True
# for column in df_flatB.columns.values:
#    if len(df_flatB[column]['VBFtight']) != int(column)+1:
#        print("-> "+str(len(df_flatB[column]['VBFtight']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
#
# print("\n----------------------------------")
# print('\nFLAT B')
# print("2b0j")
# ok = True
# for column in df_ConstSize.columns.values:
#    if len(df_ConstSize[column]['s2b0jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_ConstSize[column]['s2b0jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("boosted")
# ok = True
# for column in df_ConstSize.columns.values:
#    if len(df_ConstSize[column]['sboostedLLMcut']) != int(column)+1:
#        print("-> "+str(len(df_ConstSize[column]['sboostedLLMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("1b1j")
# ok = True
# for column in df_ConstSize.columns.values:
#    if len(df_ConstSize[column]['s1b1jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_ConstSize[column]['s1b1jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFloose")
# ok = True
# for column in df_ConstSize.columns.values:
#    if len(df_ConstSize[column]['VBFloose']) != int(column)+1:
#        print("-> "+str(len(df_ConstSize[column]['VBFloose']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
# print("VBFtight")
# ok = True
# for column in df_ConstSize.columns.values:
#    if len(df_ConstSize[column]['VBFtight']) != int(column)+1:
#        print("-> "+str(len(df_ConstSize[column]['VBFtight']))+" instead of "+str(int(column)+1))
#        ok = False
# if ok: print("-> all ok")
