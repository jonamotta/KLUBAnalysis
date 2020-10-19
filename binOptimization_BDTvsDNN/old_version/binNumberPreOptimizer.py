import os
import time
import threading
from ROOT import *
import ROOT
import numpy as np
import pandas as pd
from array import array

# function for the threading -> it waits for the result to be created
# the function is deliberately inefficient so that we lower the probability of reading the resultin the exact same moment of its creation
def wait_for_file(file_path):
    while not os.path.exists(file_path):
        time.sleep(10) # sleep for 10 seconds -> only 10 because generally the file is produced rapidely

    found = False
    os.system('chmod 777 '+file_path)
    while os.path.exists(file_path):
        if found: break
        limits_file = open(file_path,'r')
        lines = limits_file.readlines()
        for line in lines:
            if "Done" in line:
                for check_result in lines:
                    if "50.0" in check_result:
                        try:
                            result = float(check_result.split('< ')[1].replace('\n',''))
                        except ValueError:
                            continue
                        else:
                            found = True
                            limits_file.close()
                            break
                if found: break
        limits_file.close()
        time.sleep(30) # sleep for 30 seconds -> only 60 because it is generally pretty fast (like 3/4 minutes max)

# function to write lines at the beginning of file
def prepend_line(file_name, line):
    """ Insert given string as a new line at the beginning of a file """
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

# remove negative bins and reset yield accordingly
def makeNonNegativeHistos (h):
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

# fct to adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
def adjust_new_bins(new_bins_edges):
    i = 0
    j = 0
    for new_edge in new_bins_edges:
        if new_edge == -1.:
            i += 1
            j += 1
            continue
        if new_edge == 1.:
            break
        while abs(new_edge - old_bins_edges[i]) > abs(new_edge - old_bins_edges[i+1]):
            i += 1
        new_bins_edges[j] = old_bins_edges[i]
        j += 1

# SINGLE FUNCTION CONTAINING ALL THE STEPS FOR A COMPLETE ANALYSIS
# -> WORKS ONLY FOR THIS OPTIMIZATION (because of the specific names that we give to files and folders)
def limit_extraction(bins_number,channel):
    nBins = int(bins_number)
    # define array of the new bins edges based on the number of bins to be tested
    # the loop looks a bit redundant with the if inside the while, but it is to protect against having 0.99999999 and then 1 -> we only want 1 at the end
    new_bins_edges = [-1.]
    step = 2.0/nBins
    i = 0
    while new_bins_edges[i] < 1.:
        new_bins_edges.append(new_bins_edges[i]+step)
        if new_bins_edges[i+1]+step > 1.:
            new_bins_edges.remove(new_bins_edges[i+1])
            new_bins_edges.append(1.0)
            break
        i += 1

    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    adjust_new_bins(new_bins_edges)

    # create folder of the specific number of bins we are testing and copy cfgs in it
    mkdir_cmd = "mkdir PreOptSteps/bins_{0}".format(str(nBins))
    print("Executing: "+mkdir_cmd)
    os.system(mkdir_cmd)
    tag = "{0}_Legacy2018_binOptimization.cfg".format(channel)
    inDir = "{1}/PreOptData/{0}/bin_dataNonRebinned1M".format(channel,datasets_dir)
    copy_cmd = "cp -a {2}/mainCfg_{0} PreOptSteps/bins_{1}/; cp -a {2}/selectionCfg_{0} PreOptSteps/bins_{1}/; cp -a {2}/sampleCfg_Legacy2018.cfg PreOptSteps/bins_{1}/; cp -a {2}/outPlotter.root PreOptSteps/bins_{1}/".format(tag,str(nBins),inDir)
    print("Executing: "+copy_cmd)
    os.system(copy_cmd)

    # append rebinning section in the mainCfg
    mainCfg = open("PreOptSteps/bins_{0}/mainCfg_{1}".format(str(nBins),tag), "a")
    mainCfg.write("[pp_rebin]\n")
    # convert new binning edges to string and write them in the mainCfg
    edges_string = np.array2string(np.array(new_bins_edges), separator=',', max_line_width=None, precision=20).replace('\n','')
    mainCfg.write("r1 = BDToutSM_kl_1, sboostedLLMcut, %s \n" % edges_string.replace('[','').replace(']',''))
    mainCfg.write("r2 = BDToutSM_kl_1, s2b0jresolvedMcut, %s \n" % edges_string.replace('[','').replace(']',''))
    mainCfg.close()

    # call combineFillerOutputs.py
    comb_cmd = "python ../scripts/combineFillerOutputs.py --dir PreOptSteps/bins_{0}".format(str(nBins))
    print("Executing: "+comb_cmd)
    os.system(comb_cmd)

    # call wrapperHistos.py
    wrapper_cmd = "python wrapperHistos.py -f PreOptSteps/bins_{0}/analyzedOutPlotter.root -c {1} -o bins_{0} -d PreOptSteps/bins_{0} -a 'GGF'".format(str(nBins),channel)
    print("Executing: "+wrapper_cmd)
    os.system(wrapper_cmd)

    # delete the first lines in makeCategories_preOpt.sh with the old exports (by wrong we mean 'of the old iteration')
    # and re-write them in makeCategories_preOpt.sh with the correct exports
    file = open("makeCategories_preOpt.sh","r")
    lines = file.readlines()
    file.close()
    rm_cmd = "rm makeCategories_preOpt.sh"
    os.system(rm_cmd)
    file = open("makeCategories_preOpt.sh","w")
    file.writelines(lines[5:])
    file.close()
    prepend_line("makeCategories_preOpt.sh",'export SELECTIONS="s2b0jresolvedMcut sboostedLLMcut"')
    prepend_line("makeCategories_preOpt.sh",'export LEPTONS="{0}"'.format(channel))
    prepend_line("makeCategories_preOpt.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/PreOptSteps/bins_{0}/"'.format(str(nBins)))
    prepend_line("makeCategories_preOpt.sh",'export TAG="bins_{0}"'.format(str(nBins)))
    prepend_line("makeCategories_preOpt.sh","#!/bin/bash")

    # call makeCategories_preOpt.sh
    limits_cmd = "./makeCategories_preOpt.sh"
    os.system('chmod 777 makeCategories_preOpt.sh')
    os.system(limits_cmd)

    print("\n\n** WAITING FOR THE PREVIOUS JOBS TO BE COMPLETED **\n")
    thread = threading.Thread(target=wait_for_file("PreOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel)))
    thread.start()
    # wait here for the result to be available before continuing
    thread.join()

    # store the results of the 2b0j category in a specific .txt
    with open("PreOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11s2b0jresolvedMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PreOptSteps/all_limits_2b0j.txt","r")
        except IOError:
            all_limits_2b0j = open("PreOptSteps/all_limits_2b0j.txt","a")
            all_limits_2b0j.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_2b0j.write("------------------------------------------------\n")
        else:
            all_limits_2b0j = open("PreOptSteps/all_limits_2b0j.txt","a")
        for line in lines:
            if "50.0" in line:
                result_2b0j = float(line.split('< ')[1].replace('\n',''))
                all_limits_2b0j.write("bins_{0}: ".format(str(nBins))+str(result_2b0j)+"\n")
        del lines

    # store the results of the boosted category in a specific .txt
    with open("PreOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11sboostedLLMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PreOptSteps/all_limits_boosted.txt","r")
        except IOError:
            all_limits_boosted = open("PreOptSteps/all_limits_boosted.txt","a")
            all_limits_boosted.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_boosted.write("------------------------------------------------\n")
        else:
            all_limits_boosted = open("PreOptSteps/all_limits_boosted.txt","a")
        for line in lines:
            if "50.0" in line:
                result_boosted = float(line.split('< ')[1].replace('\n',''))
                all_limits_boosted.write("bins_{0}: ".format(str(nBins))+str(result_boosted)+"\n")
        del lines

    # store the the combined results in a specific .txt
    with open("PreOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PreOptSteps/all_limits_combined.txt","r")
        except IOError:
            all_limits_combined = open("PreOptSteps/all_limits_combined.txt","a")
            all_limits_combined.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_combined.write("------------------------------------------------\n")
        else:
            all_limits_combined = open("PreOptSteps/all_limits_combined.txt","a")
        for line in lines:
            if "50.0" in line:
                result_boosted = float(line.split('< ')[1].replace('\n',''))
                all_limits_combined.write("bins_{0}: ".format(str(nBins))+str(result_boosted)+"\n")
        del lines


###############################################################################
############################# MAIN OF THE PROGRAM #############################
###############################################################################

#channel = "ETau"
#channel = "MuTau"
channel = "TauTau"

print("** CHANNEL: {0} ** \n".format(channel))

global datasets_dir
datasets_dir = "/data_CMS/cms/motta/binOptDatasets"

inRoot = TFile.Open("{1}/PreOptData/{0}/bin_dataNonRebinned1M/analyzedOutPlotter.root".format(channel,datasets_dir))
process = "GGHHSM"
select = "s2b0jresolvedMcut"
variable = "BDToutSM_kl_1"
templateName = "{0}_{1}_SR_{2}".format(process,select,variable)
template = inRoot.Get(templateName)

# get the old bin edges -> it will be used for the rebinning using combineFillerOutputs.py
nPoints  = template.GetNbinsX()
global old_bins_edges
old_bins_edges = [-1]
for ibin in range (1, nPoints+1):
    old_bins_edges.append(template.GetBinLowEdge(ibin+1))

# create the forder to store all the steps of the bin number scan and the limit extraction results
mkdir_cmd = "mkdir PreOptSteps"
print("Executing: "+mkdir_cmd)
os.system(mkdir_cmd)

# scan the values of the number of bins we are interested in
# suggestion is tu use a coarse step (e.g. 3) because the next script of the optimization will then use a window of 5 bins
# the maximum number of bins that the next script is able to handle is 52-53, therefore we san only up to it
for bins in range(10,53,3):
    limit_extraction(bins, channel)
