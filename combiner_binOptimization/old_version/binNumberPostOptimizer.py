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
def limit_extraction(nBins,new_bins_edges_2b0j,new_bins_edges_boosted,new_bins_edges_1b1j,new_bins_edges_VBFloose,new_bins_edges_VBFtight):
    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    adjust_new_bins(new_bins_edges_2b0j)
    adjust_new_bins(new_bins_edges_boosted)
    adjust_new_bins(new_bins_edges_1b1j)
    adjust_new_bins(new_bins_edges_VBFloose)
    adjust_new_bins(new_bins_edges_VBFtight)

    # create folder of the specific mode and number of bins we are testing and copy cfgs in it
    mkdir_cmd = "mkdir PostOptSteps/bins_{0}".format(str(nBins))
    print("Executing: "+mkdir_cmd)
    os.system(mkdir_cmd)
    tag = "{0}_Legacy2018_binOptimization.cfg".format(channel)
    inDir = "{1}/PostOptData/{0}/bin_dataNonRebinned1M".format(channel,datasets_dir)
    copy_cmd = "cp -a {2}/mainCfg_{0} PostOptSteps/bins_{1}/; cp -a {2}/selectionCfg_{0} PostOptSteps/bins_{1}/; cp -a {2}/sampleCfg_Legacy2018.cfg PostOptSteps/bins_{1}/; cp -a {2}/outPlotter.root PostOptSteps/bins_{1}/".format(tag,str(nBins),inDir)
    print("Executing: "+copy_cmd)
    os.system(copy_cmd)

    # append rebinning section in the mainCfg
    mainCfg = open("PostOptSteps/bins_{0}/mainCfg_{1}".format(str(nBins),tag), "a")
    mainCfg.write("[pp_rebin]\n")
    # convert new binning edges to string and write them in the mainCfg
    edges2b0j_string = np.array2string(np.array(new_bins_edges_2b0j), separator=',', max_line_width=None, precision=20).replace('\n','')
    edgesboosted_string = np.array2string(np.array(new_bins_edges_boosted), separator=',', max_line_width=None, precision=20).replace('\n','')
    edges1b1j_string = np.array2string(np.array(new_bins_edges_1b1j), separator=',', max_line_width=None, precision=20).replace('\n','')
    edgesVBFloose_string = np.array2string(np.array(new_bins_edges_VBFloose), separator=',', max_line_width=None, precision=20).replace('\n','')
    edgesVBFtight_string = np.array2string(np.array(new_bins_edges_VBFtight), separator=',', max_line_width=None, precision=20).replace('\n','')
    mainCfg.write("r1 = BDToutSM_kl_1, sboostedLLMcut, %s \n" % edgesboosted_string.replace('[','').replace(']',''))
    mainCfg.write("r2 = BDToutSM_kl_1, s2b0jresolvedMcut, %s \n" % edges2b0j_string.replace('[','').replace(']',''))
    mainCfg.write("r3 = BDToutSM_kl_1, s1b1jresolvedMcut, %s \n" % edges1b1j_string.replace('[','').replace(']',''))
    mainCfg.write("r4 = BDToutSM_kl_1, VBFlooseMcut, %s \n" % edgesVBFloose_string.replace('[','').replace(']',''))
    mainCfg.write("r4 = BDToutSM_kl_1, VBFtightMcut, %s \n" % edgesVBFtight_string.replace('[','').replace(']',''))
    mainCfg.close()

    # call combineFillerOutputs.py
    comb_cmd = "python ../scripts/combineFillerOutputs.py --dir PostOptSteps/bins_{0}".format(str(nBins))
    print("Executing: "+comb_cmd)
    os.system(comb_cmd)

    # call wrapperHistos.py
    wrapper_cmd = "python wrapperHistos.py -f PostOptSteps/bins_{0}/analyzedOutPlotter.root -c {1} -o bins_{0} -d PostOptSteps/bins_{0} -a 'GGF'".format(str(nBins),channel)
    print("Executing: "+wrapper_cmd)
    os.system(wrapper_cmd)
    print("finished wrapping")

    # delete the first lines in makeCategories_postOpt.sh with the old exports (by wrong we mean 'of the old iteration')
    # and re-write them in makeCategories_postOpt.sh with the correct exports
    file = open("makeCategories_postOpt.sh","r")
    lines = file.readlines()
    file.close()
    rm_cmd = "rm makeCategories_postOpt.sh"
    os.system(rm_cmd)
    file = open("makeCategories_postOpt.sh","w")
    file.writelines(lines[5:])
    file.close()
    prepend_line("makeCategories_postOpt.sh",'export SELECTIONS="s2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFlooseMcut VBFtightMcut"')
    prepend_line("makeCategories_postOpt.sh",'export LEPTONS="{0}"'.format(channel))
    prepend_line("makeCategories_postOpt.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/PostOptSteps/bins_{0}/"'.format(str(nBins)))
    prepend_line("makeCategories_postOpt.sh",'export TAG="bins_{0}"'.format(str(nBins)))
    prepend_line("makeCategories_postOpt.sh","#!/bin/bash")

    # call makeCategories_postOpt.sh
    limits_cmd = "./makeCategories_postOpt.sh"
    os.system('chmod 777 makeCategories_postOpt.sh')
    os.system(limits_cmd)

    print("\n\n** WAITING FOR THE PREVIOUS JOBS TO BE COMPLETED **\n")
    thread = threading.Thread(target=wait_for_file("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel)))
    thread.start()
    # wait here for the result to be available before continuing
    thread.join()

    # store the results of the 2b0j category in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11s2b0jresolvedMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_2b0j.txt","r")
        except IOError:
            all_limits_2b0j = open("PostOptSteps/all_limits_2b0j.txt","a")
            all_limits_2b0j.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_2b0j.write("------------------------------------------------\n")
        else:
            all_limits_2b0j = open("PostOptSteps/all_limits_2b0j.txt","a")
        for line in lines:
            if "50.0" in line:
                result_2b0j = float(line.split('< ')[1].replace('\n',''))
                all_limits_2b0j.write("bins_{0}: ".format(str(nBins))+str(result_2b0j)+"\n")
        del lines

    # store the results of the boosted category in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11sboostedLLMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_boosted.txt","r")
        except IOError:
            all_limits_boosted = open("PostOptSteps/all_limits_boosted.txt","a")
            all_limits_boosted.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_boosted.write("------------------------------------------------\n")
        else:
            all_limits_boosted = open("PostOptSteps/all_limits_boosted.txt","a")
        for line in lines:
            if "50.0" in line:
                result_boosted = float(line.split('< ')[1].replace('\n',''))
                all_limits_boosted.write("bins_{0}: ".format(str(nBins))+str(result_boosted)+"\n")
        del lines

    # store the results of the 1b1j category in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11s1b1jresolvedMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_1b1j.txt","r")
        except IOError:
            all_limits_1b1j = open("PostOptSteps/all_limits_1b1j.txt","a")
            all_limits_1b1j.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_1b1j.write("------------------------------------------------\n")
        else:
            all_limits_1b1j = open("PostOptSteps/all_limits_1b1j.txt","a")
        for line in lines:
            if "50.0" in line:
                result_1b1j = float(line.split('< ')[1].replace('\n',''))
                all_limits_1b1j.write("bins_{0}: ".format(str(nBins))+str(result_1b1j)+"\n")
        del lines

    # store the results of the VBFloose category in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11VBFlooseMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_VBFloose.txt","r")
        except IOError:
            all_limits_VBFloose = open("PostOptSteps/all_limits_VBFloose.txt","a")
            all_limits_VBFloose.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_VBFloose.write("------------------------------------------------\n")
        else:
            all_limits_VBFloose = open("PostOptSteps/all_limits_VBFloose.txt","a")
        for line in lines:
            if "50.0" in line:
                result_VBFloose = float(line.split('< ')[1].replace('\n',''))
                all_limits_VBFloose.write("bins_{0}: ".format(str(nBins))+str(result_VBFloose)+"\n")
        del lines

    # store the results of the VBFtight category in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11VBFtightMcutBDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_VBFtight.txt","r")
        except IOError:
            all_limits_VBFtight = open("PostOptSteps/all_limits_VBFtight.txt","a")
            all_limits_VBFtight.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_VBFtight.write("------------------------------------------------\n")
        else:
            all_limits_VBFtight = open("PostOptSteps/all_limits_VBFtight.txt","a")
        for line in lines:
            if "50.0" in line:
                result_VBFtight = float(line.split('< ')[1].replace('\n',''))
                all_limits_VBFtight.write("bins_{0}: ".format(str(nBins))+str(result_VBFtight)+"\n")
        del lines

    # store the the combined results in a specific .txt
    with open("PostOptSteps/bins_{0}/cards_{1}_bins_{0}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("PostOptSteps/all_limits_combined.txt","r")
        except IOError:
            all_limits_combined = open("PostOptSteps/all_limits_combined.txt","a")
            all_limits_combined.write("ALL THE LIMITS CALCULATED IN THE BIN NUMBER SCAN\n")
            all_limits_combined.write("------------------------------------------------\n")
        else:
            all_limits_combined = open("PostOptSteps/all_limits_combined.txt","a")
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

# take a histogram as template
inRoot = TFile.Open("{1}/PostOptData/{0}/bin_dataNonRebinned1M/analyzedOutPlotter.root".format(channel,datasets_dir))
process = "GGHHSM"
select = "s2b0jresolvedMcut"
variable = "BDToutSM_kl_1"
templateName = "{0}_{1}_SR_{2}".format(process,select,variable)
template = inRoot.Get(templateName)
# old_bins_edges contains the edges of the bins of the 100k/1M/3M histograms -> they are used for the rebinning through combineFillerOutputs.py
nPoints  = template.GetNbinsX()
global old_bins_edges
old_bins_edges = [-1]
for ibin in range (1, nPoints+1):
    old_bins_edges.append(template.GetBinLowEdge(ibin+1))

selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFlooseMcut", "VBFtightMcut"]
variable = "BDToutSM_kl_1"

# CREATE ALL THE DATAFRAME OF THE DISTRIBUTION -> IT WILL CONTAIN THE NEW BINNINGS
# FlatS
df_flatS = pd.DataFrame(index=selections, columns=range(40,53))
for index in df_flatS.index.values:
    for column in df_flatS.columns.values:
        df_flatS[column][index] = []

############################################
# INSIDE THIS LOOP WE FILL THE DF FOR FlatS
for select in selections:
    hSgn = inRoot.Get("GGHHSM_{0}_SR_{1}".format(select,variable))
    makeNonNegativeHistos(hSgn)

    ####################################
    # FlatS (BDToutSM_kl_1 flat in sgn)
    template = hSgn
    integral = float(template.Integral())
    axis = template.GetXaxis()
    k = 0
    for column in df_flatS.columns.values:
        y = 0
        df_flatS[column][select].append(-1.)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(column):
                if abs(y - integral/float(column)) < abs(y - float(template.GetBinContent(i)) - integral/float(column)):
                    df_flatS[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatS[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatS[column][select].append(1.)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatS[column][select]) - (int(column)+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,(df_flatS[column][select][0]+df_flatS[column][select][1])/2)
        elif len(df_flatS[column][select]) - (int(column)+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/3.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 2BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (int(column)+1) == -3: # if three bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/4.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+3*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 3BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (int(column)+1) <= -4:
            print("** THE FlatS "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatS[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** SUBSTITUTING BINS WITH A SINGLE UNIFIED BIN **")
            df_flatS[column][select] = [-1.,1.]
        k += 1
    # delete the variables to allow next step
    del template

# create the forder to store all the steps of the bin number scan and the limit extraction results
mkdir_cmd = "mkdir PostOptSteps"
print("Executing: "+mkdir_cmd)
os.system(mkdir_cmd)

for column in df_flatS.columns.values:
    limit_extraction(int(column),df_flatS[column]["s2b0jresolvedMcut"],df_flatS[column]["sboostedLLMcut"],df_flatS[column]["s1b1jresolvedMcut"],df_flatS[column]["VBFlooseMcut"],df_flatS[column]["VBFtightMcut"])


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
#print("VBFlooseMcut")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFlooseMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFlooseMcut']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
#print("VBFtightMcut")
#ok = True
#for column in df_flatS.columns.values:
#    if len(df_flatS[column]['VBFtightMcut']) != int(column)+1:
#        print("-> "+str(len(df_flatS[column]['VBFtightMcut']))+" instead of "+str(int(column)+1))
#        ok = False
#if ok: print("-> all ok")
