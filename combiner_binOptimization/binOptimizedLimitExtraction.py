import os
import sys
import time
from ROOT import *
import ROOT
import numpy as np
import pandas as pd
from array import array

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
        if i == 0:
            hsum = h.Clone(sumName)
        else:
            hsum.Add(h)
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
# -> WORKS ONLY FOR THIS OPTIMIZATION (because of the specific names that we give to files and folders)
def limit_extraction(new_bins_edges_dataframe):
    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    for index in new_bins_edges_dataframe.index.values:
        for column in new_bins_edges_dataframe.columns.values:
            adjust_new_bins(new_bins_edges_dataframe[column][index])

    # create folder of the specific mode and number of bins we are testing and copy cfgs in it
    mkdirETau_cmd = "mkdir OptimizedLimit/ETau"
    os.system(mkdirETau_cmd)
    mkdirMuTau_cmd = "mkdir OptimizedLimit/MuTau"
    os.system(mkdirMuTau_cmd)
    mkdirTauTau_cmd = "mkdir OptimizedLimit/TauTau"
    os.system(mkdirTauTau_cmd)
    for ch in channels:
        tag = "{0}_Legacy{1}_binOptimization.cfg".format(ch,year)
        if variable == "BDToutSM_kl_1":
            inDir = "{0}/{1}/BDT_dataNonRebinned1M".format(datasets_dir,ch)
        elif variable == "DNNoutSM_kl_1":
            inDir = "{0}/{1}/DNN_dataNonRebinned500k".format(datasets_dir,ch)
        copy_cmd = "cp -a {2}/mainCfg_{0} OptimizedLimit/{1}/; cp -a {2}/selectionCfg_{0} OptimizedLimit/{1}/; cp -a {2}/sampleCfg_Legacy{3}.cfg OptimizedLimit/{1}/; cp -a {2}/outPlotter.root OptimizedLimit/{1}/".format(tag,ch,inDir,year)
        os.system(copy_cmd)

        # append rebinning section in the mainCfg
        mainCfg = open("OptimizedLimit/{0}/mainCfg_{1}".format(ch,tag), "a")
        mainCfg.write("[pp_rebin]\n")
        # convert new binning edges to string and write them in the mainCfg
        edges2b0j_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['s2b0jresolvedMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edgesboosted_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['sboostedLLMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edges1b1j_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['s1b1jresolvedMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edgesVBFloose_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['VBFlooseMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        if year != "2016" and ch == "TauTau": edgesVBFtight_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['VBFtightMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        mainCfg.write("r1 = {0}, sboostedLLMcut, %s \n".format(variable) % edgesboosted_string.replace('[','').replace(']',''))
        mainCfg.write("r2 = {0}, s2b0jresolvedMcut, %s \n".format(variable) % edges2b0j_string.replace('[','').replace(']',''))
        mainCfg.write("r3 = {0}, s1b1jresolvedMcut, %s \n".format(variable) % edges1b1j_string.replace('[','').replace(']',''))
        mainCfg.write("r4 = {0}, VBFlooseMcut, %s \n".format(variable) % edgesVBFloose_string.replace('[','').replace(']',''))
        if year != "2016" and ch == "TauTau": mainCfg.write("r5 = {0}, VBFtightMcut, %s \n".format(variable) % edgesVBFtight_string.replace('[','').replace(']',''))
        mainCfg.close()

        # call combineFillerOutputs.py
        comb_cmd = "python ../scripts/combineFillerOutputs.py --dir OptimizedLimit/{0}".format(ch)
        os.system(comb_cmd)

        # call wrapperHistos.py
        wrapper_cmd = "python wrapperHistos.py -f OptimizedLimit/{0}/analyzedOutPlotter.root -c {0} -o {0} -d OptimizedLimit -a 'GGF' -y {1}".format(ch,year)
        os.system(wrapper_cmd)

        copy_cmd = "cp -a OptimizedLimit/{1}/mainCfg_{0} OptimizedLimit/; cp -a OptimizedLimit/{1}/selectionCfg_{0} OptimizedLimit/".format(tag,ch)
        os.system(copy_cmd)
    print("** FINISHED WRAPPING **")

    # delete the first lines in makeCategories_optimized.sh with the old exports (by wrong we mean 'of the old iteration')
    # and re-write them in makeCategories_optimized.sh with the correct exports
    file = open("makeCategories_optimized.sh","r")
    lines = file.readlines()
    file.close()
    rm_cmd = "rm makeCategories_optimized.sh"
    os.system(rm_cmd)
    file = open("makeCategories_optimized.sh","w")
    file.writelines(lines[7:])
    file.close()
    prepend_line("makeCategories_optimized.sh",'export VAR="{0}"'.format(variable))
    prepend_line("makeCategories_optimized.sh",'export YEAR="{0}"'.format(year))
    if year != "2016": prepend_line("makeCategories_optimized.sh",'export SELECTIONS="s2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFlooseMcut VBFtightMcut"')
    else: prepend_line("makeCategories_optimized.sh",'export SELECTIONS="s2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFlooseMcut"')
    ch_string = ""
    for ch in channels:
        ch_string += ch+str(' ')
    prepend_line("makeCategories_optimized.sh",'export LEPTONS="{0}"'.format(ch_string))
    prepend_line("makeCategories_optimized.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/OptimizedLimit/"')
    prepend_line("makeCategories_optimized.sh",'export TAG="optimized"')
    prepend_line("makeCategories_optimized.sh","#!/bin/bash")

    # call makeCategories_optimized.sh
    limits_cmd = "./makeCategories_optimized.sh"
    os.system('chmod 777 makeCategories_optimized.sh')
    os.system(limits_cmd)

    print("\n\n THE ANSWER TO THE ULTIMATE QUESTION OF LIFE, THE UNIVERSE AND EVERYTHING IS 42...")
    print(" ...BUT IT IS NOT THE ANSWER TO THE LIMIT CALCULATION.")
    print(" SO WHILE YOU WAIT FOR THE JOBS TO BE COMPLETED GO AND READ SOMETHING; I SUGGEST 'THE HITCHHIKERS GUIDE TO THE GALAXY', IT'S A GREAT BOOK!\n")

    return


###############################################################################
############################# MAIN OF THE PROGRAM #############################
###############################################################################

global year
#year = "2016"
# year = "2017"
year = "2018"

global datasets_dir
datasets_dir = "/data_CMS/cms/motta/binOptDatasets/Legacy{0}/v2/".format(year)

global variable
#variable = "BDToutSM_kl_1"
variable = "DNNoutSM_kl_1"

global channels
channels = ["ETau", "MuTau", "TauTau"]

print("** VARIABLE: {0} **".format(variable))
print("** CHANNEL: {0} **".format(channels))
print("** YEAR: {0} **\n".format(year))

# take a histogram as template
if variable == "BDToutSM_kl_1":
    inRoot = TFile.Open("{0}/TauTau/BDT_dataNonRebinned1M/analyzedOutPlotter.root".format(datasets_dir))
elif variable == "DNNoutSM_kl_1":
    inRoot = TFile.Open("{0}/TauTau/DNN_dataNonRebinned500k/analyzedOutPlotter.root".format(datasets_dir))
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
if year != "2016":
    # TauTau (only 2017/2018) selections
    selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFlooseMcut", "VBFtightMcut"]
else:
    # ETau/MuTau (all years) + TauTau (2016) selections
    selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFlooseMcut"]


##############################################################################################################
# HERE WE FILL THE DATAFRAMES CONSTAINING THE INFORMATION ABOUT THE OPTIMIZED DISTRIBUTION AND NUMBER OF BINS
# BDT OPTIMIZED SPECIFICATIONS FOR THE BINNING
if variable == "BDToutSM_kl_1":
    # 2018 distributions
    df_opt_distribs2018 = pd.DataFrame(index=selections, columns=channels)
    df_opt_distribs2018['ETau']['s2b0jresolvedMcut'] = "FlatS"
    df_opt_distribs2018['ETau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['ETau']['s1b1jresolvedMcut'] = "FlatS"
    df_opt_distribs2018['ETau']['VBFlooseMcut'] = "FlatS"
    df_opt_distribs2018['ETau']['VBFtightMcut'] = "---"
    #----
    df_opt_distribs2018['MuTau']['s2b0jresolvedMcut'] = "FlatS"
    df_opt_distribs2018['MuTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['MuTau']['s1b1jresolvedMcut'] = "FlatS"
    df_opt_distribs2018['MuTau']['VBFlooseMcut'] = "FlatS"
    df_opt_distribs2018['MuTau']['VBFtightMcut'] = "---"
    #----
    df_opt_distribs2018['TauTau']['s2b0jresolvedMcut'] = "FlatSB"
    df_opt_distribs2018['TauTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['TauTau']['s1b1jresolvedMcut'] = "FlatSB"
    df_opt_distribs2018['TauTau']['VBFlooseMcut'] = "FlatB"
    df_opt_distribs2018['TauTau']['VBFtightMcut'] = "FlatB"
    # 2018 number of bins
    df_opt_nBins2018 = pd.DataFrame(index=selections, columns=channels)
    df_opt_nBins2018['ETau']['s2b0jresolvedMcut'] = 17
    df_opt_nBins2018['ETau']['sboostedLLMcut'] = 14
    df_opt_nBins2018['ETau']['s1b1jresolvedMcut'] = 29
    df_opt_nBins2018['ETau']['VBFlooseMcut'] = 10
    df_opt_nBins2018['ETau']['VBFtightMcut'] = "---"
    #----
    df_opt_nBins2018['MuTau']['s2b0jresolvedMcut'] = 18
    df_opt_nBins2018['MuTau']['sboostedLLMcut'] = 27
    df_opt_nBins2018['MuTau']['s1b1jresolvedMcut'] = 30
    df_opt_nBins2018['MuTau']['VBFlooseMcut'] = 17
    df_opt_nBins2018['MuTau']['VBFtightMcut'] = "---"
    #----
    df_opt_nBins2018['TauTau']['s2b0jresolvedMcut'] = 20
    df_opt_nBins2018['TauTau']['sboostedLLMcut'] = 10
    df_opt_nBins2018['TauTau']['s1b1jresolvedMcut'] = 48
    df_opt_nBins2018['TauTau']['VBFlooseMcut'] = 48
    df_opt_nBins2018['TauTau']['VBFtightMcut'] = 36
    # 2016 distributions
    df_opt_distribs2016 = pd.DataFrame(index=selections, columns=channels)
    # df_opt_distribs2016['ETau']['s2b0jresolvedMcut'] =
    # df_opt_distribs2016['ETau']['sboostedLLMcut'] =
    # df_opt_distribs2016['ETau']['s1b1jresolvedMcut'] =
    # df_opt_distribs2016['ETau']['VBFlooseMcut'] =
    #----
    df_opt_distribs2016['MuTau']['s2b0jresolvedMcut'] = "FlatS"
    df_opt_distribs2016['MuTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2016['MuTau']['s1b1jresolvedMcut'] = "FlatS"
    df_opt_distribs2016['MuTau']['VBFlooseMcut'] = "FlatS"
    #----
    df_opt_distribs2016['TauTau']['s2b0jresolvedMcut'] = "FlatSB"
    df_opt_distribs2016['TauTau']['sboostedLLMcut'] = "ConstSize"
    df_opt_distribs2016['TauTau']['s1b1jresolvedMcut'] = "FlatSB"
    df_opt_distribs2016['TauTau']['VBFlooseMcut'] = "FlatB"
    # 2016 number of bins
    df_opt_nBins2016 = pd.DataFrame(index=selections, columns=channels)
    # df_opt_nBins2016['ETau']['s2b0jresolvedMcut'] =
    # df_opt_nBins2016['ETau']['sboostedLLMcut'] =
    # df_opt_nBins2016['ETau']['s1b1jresolvedMcut'] =
    # df_opt_nBins2016['ETau']['VBFlooseMcut'] =
    #----
    df_opt_nBins2016['MuTau']['s2b0jresolvedMcut'] = 20
    df_opt_nBins2016['MuTau']['sboostedLLMcut'] = 21
    df_opt_nBins2016['MuTau']['s1b1jresolvedMcut'] = 26
    df_opt_nBins2016['MuTau']['VBFlooseMcut'] = 14
    #----
    df_opt_nBins2016['TauTau']['s2b0jresolvedMcut'] = 22
    df_opt_nBins2016['TauTau']['sboostedLLMcut'] = 36
    df_opt_nBins2016['TauTau']['s1b1jresolvedMcut'] = 36
    df_opt_nBins2016['TauTau']['VBFlooseMcut'] = 22

# DNN OPTIMIZED SPECIFICATIONS FOR THE BINNING
if variable == "DNNoutSM_kl_1":
    # 2018 distributions
    df_opt_distribs2018 = pd.DataFrame(index=selections, columns=channels)
    df_opt_distribs2018['ETau']['s2b0jresolvedMcut'] = "ConstSize"
    df_opt_distribs2018['ETau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['ETau']['s1b1jresolvedMcut'] = "ConstSize"
    df_opt_distribs2018['ETau']['VBFlooseMcut'] = "ConstSize"
    df_opt_distribs2018['ETau']['VBFtightMcut'] = "---"
    #----
    df_opt_distribs2018['MuTau']['s2b0jresolvedMcut'] = "FlatSB"
    df_opt_distribs2018['MuTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['MuTau']['s1b1jresolvedMcut'] = "FlatS"
    df_opt_distribs2018['MuTau']['VBFlooseMcut'] = "FlatSB"
    df_opt_distribs2018['MuTau']['VBFtightMcut'] = "---"
    #----
    df_opt_distribs2018['TauTau']['s2b0jresolvedMcut'] = "ConstSize"
    df_opt_distribs2018['TauTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2018['TauTau']['s1b1jresolvedMcut'] = "ConstSize"
    df_opt_distribs2018['TauTau']['VBFlooseMcut'] = "ConstSize"
    df_opt_distribs2018['TauTau']['VBFtightMcut'] = "FlatB"
    # 2018 number of bins
    df_opt_nBins2018 = pd.DataFrame(index=selections, columns=channels)
    df_opt_nBins2018['ETau']['s2b0jresolvedMcut'] = 45
    df_opt_nBins2018['ETau']['sboostedLLMcut'] = 13
    df_opt_nBins2018['ETau']['s1b1jresolvedMcut'] = 51
    df_opt_nBins2018['ETau']['VBFlooseMcut'] = 43
    df_opt_nBins2018['ETau']['VBFtightMcut'] = "---"
    #----
    df_opt_nBins2018['MuTau']['s2b0jresolvedMcut'] = 49
    df_opt_nBins2018['MuTau']['sboostedLLMcut'] = 18
    df_opt_nBins2018['MuTau']['s1b1jresolvedMcut'] = 16
    df_opt_nBins2018['MuTau']['VBFlooseMcut'] = 51
    df_opt_nBins2018['MuTau']['VBFtightMcut'] = "---"
    #----
    df_opt_nBins2018['TauTau']['s2b0jresolvedMcut'] = 49
    df_opt_nBins2018['TauTau']['sboostedLLMcut'] = 12
    df_opt_nBins2018['TauTau']['s1b1jresolvedMcut'] = 49
    df_opt_nBins2018['TauTau']['VBFlooseMcut'] = 32
    df_opt_nBins2018['TauTau']['VBFtightMcut'] = 25
    # 2016 distributions
    df_opt_distribs2016 = pd.DataFrame(index=selections, columns=channels)
    # df_opt_distribs2016['ETau']['s2b0jresolvedMcut'] =
    # df_opt_distribs2016['ETau']['sboostedLLMcut'] =
    # df_opt_distribs2016['ETau']['s1b1jresolvedMcut'] =
    # df_opt_distribs2016['ETau']['VBFlooseMcut'] =
    #----
    df_opt_distribs2016['MuTau']['s2b0jresolvedMcut'] = "FlatS"
    df_opt_distribs2016['MuTau']['sboostedLLMcut'] = "FlatB"
    df_opt_distribs2016['MuTau']['s1b1jresolvedMcut'] = "FlatS"
    df_opt_distribs2016['MuTau']['VBFlooseMcut'] = "FlatS"
    #----
    df_opt_distribs2016['TauTau']['s2b0jresolvedMcut'] = "FlatSB"
    df_opt_distribs2016['TauTau']['sboostedLLMcut'] = "ConstSize"
    df_opt_distribs2016['TauTau']['s1b1jresolvedMcut'] = "FlatSB"
    df_opt_distribs2016['TauTau']['VBFlooseMcut'] = "FlatB"
    # 2016 number of bins
    df_opt_nBins2016 = pd.DataFrame(index=selections, columns=channels)
    # df_opt_nBins2016['ETau']['s2b0jresolvedMcut'] =
    # df_opt_nBins2016['ETau']['sboostedLLMcut'] =
    # df_opt_nBins2016['ETau']['s1b1jresolvedMcut'] =
    # df_opt_nBins2016['ETau']['VBFlooseMcut'] =
    #----
    df_opt_nBins2016['MuTau']['s2b0jresolvedMcut'] = 20
    df_opt_nBins2016['MuTau']['sboostedLLMcut'] = 21
    df_opt_nBins2016['MuTau']['s1b1jresolvedMcut'] = 26
    df_opt_nBins2016['MuTau']['VBFlooseMcut'] = 14
    #----
    df_opt_nBins2016['TauTau']['s2b0jresolvedMcut'] = 22
    df_opt_nBins2016['TauTau']['sboostedLLMcut'] = 36
    df_opt_nBins2016['TauTau']['s1b1jresolvedMcut'] = 36
    df_opt_nBins2016['TauTau']['VBFlooseMcut'] = 22

# CREATE THE DATAFRAME OF THE DISTRIBUTIONS -> IT WILL CONTAIN THE NEW BINNINGS
df_opt_bins = pd.DataFrame(index=selections, columns=channels)
for index in df_opt_bins.index.values:
    for column in df_opt_bins.columns.values:
        df_opt_bins[column][index] = []

######################################################################
# INSIDE THE FOLLOWING LOOP WE FILL THE DF FOR THE OPTIMIZED BINNINGS

if year == "2016":
    df_distribs = df_opt_distribs2016
    df_numb_bins = df_opt_nBins2016
elif year == "2018":
    df_distribs = df_opt_distribs2018
    df_numb_bins = df_opt_nBins2018

print("INFO : Optimized distributions")
print(df_distribs)
print("\nINFO : Optimized number of bins")
print(df_numb_bins)
print("\n")

bkgList = ['QCD', 'TT', 'DYtot', 'others']
sigList = ['GGHHSM']
doOverflow = False
for select in selections:
    for ch in channels:
        # skyp the selections that do not exist
        if select == "VBFtightMcut":
            if ch == "ETau" or ch == "MuTau": continue

        # access the correct ROOT file and take the histograms
        # take a histogram as template
        if variable == "BDToutSM_kl_1":
            RootFile = TFile.Open("{0}/{1}/BDT_dataNonRebinned1M/analyzedOutPlotter.root".format(datasets_dir,ch))
        elif variable == "DNNoutSM_kl_1":
            RootFile = TFile.Open("{0}/{1}/DNN_dataNonRebinned500k/analyzedOutPlotter.root".format(datasets_dir,ch))
        # there is no iterative way of accessing these histos becase python does not know how to use += for the TH1Fs
        hBkgs = retrieveHistos(RootFile,bkgList,variable,select,"SR")
        hSigs = retrieveHistos(RootFile,sigList,variable,select,"SR")
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

        # read what the optimization has given us
        distrib_type = df_distribs[ch][select]
        numb_bins = df_numb_bins[ch][select]

        if distrib_type == "ConstSize":
            # define array of the new bins edges based on the number of bins to be tested
            df_opt_bins[ch][select].append(variable_min)
            step = (variable_max-variable_min)/float(numb_bins)
            i = 0
            # the loop looks a bit redundant with the if inside the while, but it is to protect against having both 0.99999999 and 1 at the end of the array
            while df_opt_bins[ch][select][i] < variable_max:
                df_opt_bins[ch][select].append(df_opt_bins[ch][select][i]+step)
                if df_opt_bins[ch][select][i+1]+step > variable_max + 0.00001:
                    df_opt_bins[ch][select].remove(df_opt_bins[ch][select][i+1])
                    df_opt_bins[ch][select].append(variable_max)
                    break
                i += 1

        if distrib_type == "FlatS":
            template = hSgn
            integral = float(template.Integral())
            axis = template.GetXaxis()
            y = 0
            df_opt_bins[ch][select].append(variable_min)
            for i in range(template.GetNbinsX()):
                y += float(template.GetBinContent(i))
                if y > integral/float(numb_bins):
                    if abs(y - integral/float(numb_bins)) < abs(y - float(template.GetBinContent(i)) - integral/float(numb_bins)):
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i+1))
                    else:
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i))
                    y = 0
            df_opt_bins[ch][select].append(variable_max)
            # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
            # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
            if len(df_opt_bins[ch][select]) - (numb_bins+1) == -1: # if only one bin is missing split the first in two equal size bins
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -2: # if two bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatS "+select+" 2BIN CORRECTION DONE **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -3: # if three bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatS "+select+" 3BIN CORRECTION DONE **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) <= -4:
                print("** THE FlatS "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_opt_bins[ch][select])-1)+" INSTEAD OF "+str(ch).replace('_',' ')+" **")
                print("** SUBSTITUTING WITH SINGLE BIN **")
                df_opt_bins[ch][select] = [variable_min,variable_max]
            # delete the variables to allow next step
            del template

        if distrib_type == "FlatB":
            template = hBkg
            integral = float(template.Integral())
            axis = template.GetXaxis()
            y = 0
            df_opt_bins[ch][select].append(variable_min)
            for i in range(template.GetNbinsX()):
                y += float(template.GetBinContent(i))
                if y > integral/float(numb_bins):
                    if abs(y - integral/float(numb_bins)) < abs(y - float(template.GetBinContent(i)) - integral/float(numb_bins)):
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i+1))
                    else:
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i))
                    y = 0
            df_opt_bins[ch][select].append(variable_max)
            # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
            # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
            if len(df_opt_bins[ch][select]) - (numb_bins+1) == -1: # if only one bin is missing split the first in two equal size bins
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -2: # if two bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatB "+select+" 2BIN CORRECTION **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -3: # if three bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatB "+select+" 3BIN CORRECTION DONE **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) <= -4:
                print("** THE FlatB "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_opt_bins[ch][select])-1)+" INSTEAD OF "+str(ch).replace('_',' ')+" **")
                print("** SUBSTITUTING WITH SINGLE BIN **")
                df_opt_bins[ch][select] = [variable_min,variable_max]
            # delete the variables to allow next step
            del template

        if distrib_type == "FlatSB":
            hList = [hBkg, hSgn]
            template = makeSum("template",hList)
            integral = float(template.Integral())
            axis = template.GetXaxis()
            y = 0
            df_opt_bins[ch][select].append(variable_min)
            for i in range(template.GetNbinsX()):
                y += float(template.GetBinContent(i))
                if y > integral/float(numb_bins):
                    if abs(y - integral/float(numb_bins)) < abs(y - float(template.GetBinContent(i)) - integral/float(numb_bins)):
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i+1))
                    else:
                        df_opt_bins[ch][select].append(axis.GetBinLowEdge(i))
                    y = 0
            df_opt_bins[ch][select].append(variable_max)
            # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
            # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
            if len(df_opt_bins[ch][select]) - (numb_bins+1) == -1: # if only one bin is missing split the first in two equal size bins
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -2: # if two bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatSB "+select+" 2BIN CORRECTION DONE **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) == -3: # if three bins are missing spit the first in three equal size bins
                step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
                df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
                print("** FlatSB "+select+" 3BIN CORRECTION DONE **")
            elif len(df_opt_bins[ch][select]) - (numb_bins+1) <= -4:
                print("** THE FlatSB "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_opt_bins[ch][select])-1)+" INSTEAD OF "+str(ch).replace('_',' ')+" **")
                print("** SUBSTITUTING WITH SINGLE BIN **")
                df_opt_bins[ch][select] = [variable_min,variable_max]
            # delete the variables to allow next step
            del template

        # delete the variables to avoid strange things happening at the next round of the select loop
        del hBkgs, hSigs, hSgn, hQCD, hTT, hDY, hOthers, hBkgList, hBkg

#################################
# DO THE ACTUAL LIMIT EXTRACTION
# create the folder to store the limit extraction results
mkdir_cmd = "mkdir OptimizedLimit"
os.system(mkdir_cmd)
# calculate the limits
limit_extraction(df_opt_bins)




##########################################################################################################################
# SOME PRINTS TO CHECK IF THE BINNINGS WE ARE PRODUCING ARE CORRECT IN LEGTH OR IF WE ARE PRODUCING LESS BINS THAN NEEDED
#print('\nFLAT S')
#print("2b0j")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['s2b0jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['s2b0jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
#print("boosted")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['sboostedLLMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['sboostedLLMcut']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
#print("1b1j")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['s1b1jresolvedMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['s1b1jresolvedMcut']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
#print("VBFloose")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFloose']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFloose']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
#print("VBFtight")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFtight']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFtight']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
