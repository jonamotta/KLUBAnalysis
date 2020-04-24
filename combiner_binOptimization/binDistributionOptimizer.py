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
# -> WORKS ONLY FOR THE 2D BIN-DISTRIBUTION SCAN (because of the specific names that we give to files and folders
def HPlimit_extraction(nBins_2b0j,nBins_boosted,new_bins_edges_2b0j,new_bins_edges_boosted,mode_str):
    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    adjust_new_bins(new_bins_edges_2b0j)
    adjust_new_bins(new_bins_edges_boosted)

    # create folder of the specific mode and number of bins we are testing and copy cfgs in it
    mkdir_cmd = "mkdir DistribScanSteps/{0}/bins_{1}_{2}".format(mode_str,str(nBins_2b0j),str(nBins_boosted))
    print("Executing: "+mkdir_cmd)
    os.system(mkdir_cmd)
    tag = "{0}_Legacy2018_binOptimization.cfg".format(channel)
    inDir = "{1}/PreOptData/{0}/bin_dataNonRebinned1M".format(channel,datasets_dir)
    copy_cmd = "cp -a {2}/mainCfg_{0} DistribScanSteps/{3}/bins_{1}_{4}/; cp -a {2}/selectionCfg_{0} DistribScanSteps/{3}/bins_{1}_{4}/; cp -a {2}/sampleCfg_Legacy2018.cfg DistribScanSteps/{3}/bins_{1}_{4}/; cp -a {2}/outPlotter.root DistribScanSteps/{3}/bins_{1}_{4}/".format(tag,str(nBins_2b0j),inDir,mode_str,str(nBins_boosted))
    print("Executing: "+copy_cmd)
    os.system(copy_cmd)

    # append rebinning section in the mainCfg
    mainCfg = open("DistribScanSteps/{2}/bins_{0}_{3}/mainCfg_{1}".format(str(nBins_2b0j),tag,mode_str,str(nBins_boosted)), "a")
    mainCfg.write("[pp_rebin]\n")
    # convert new binning edges to string and write them in the mainCfg
    edges2b0j_string = np.array2string(np.array(new_bins_edges_2b0j), separator=',', max_line_width=None, precision=20).replace('\n','')
    edgesboosted_string = np.array2string(np.array(new_bins_edges_boosted), separator=',', max_line_width=None, precision=20).replace('\n','')
    mainCfg.write("r1 = BDToutSM_kl_1, sboostedLLMcut, %s \n" % edgesboosted_string.replace('[','').replace(']',''))
    mainCfg.write("r2 = BDToutSM_kl_1, s2b0jresolvedMcut, %s \n" % edges2b0j_string.replace('[','').replace(']',''))
    mainCfg.close()

    # call combineFillerOutputs.py
    comb_cmd = "python ../scripts/combineFillerOutputs.py --dir DistribScanSteps/{1}/bins_{0}_{2}".format(str(nBins_2b0j),mode_str,str(nBins_boosted))
    print("Executing: "+comb_cmd)
    os.system(comb_cmd)

    # call wrapperHistos.py
    wrapper_cmd = "python wrapperHistos.py -f DistribScanSteps/{1}/bins_{0}_{2}/analyzedOutPlotter.root -c {3} -o bins_{0}_{2} -d DistribScanSteps/{1}/bins_{0}_{2} -a 'GGF'".format(str(nBins_2b0j),mode_str,str(nBins_boosted),channel)
    print("Executing: "+wrapper_cmd)
    os.system(wrapper_cmd)
    print("finished wrapping")

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
    prepend_line("makeCategories_preOpt.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/DistribScanSteps/{1}/bins_{0}_{2}/"'.format(str(nBins_2b0j),mode_str,str(nBins_boosted)))
    prepend_line("makeCategories_preOpt.sh",'export TAG="bins_{0}_{1}"'.format(str(nBins_2b0j),str(nBins_boosted)))
    prepend_line("makeCategories_preOpt.sh","#!/bin/bash")

    # call makeCategories_preOpt.sh
    limits_cmd = "./makeCategories_preOpt.sh"
    os.system('chmod 777 makeCategories_preOpt.sh')
    os.system(limits_cmd)

    print("\n\n** WAITING FOR THE PREVIOUS JOBS TO BE COMPLETED **\n")
    thread = threading.Thread(target=wait_for_file("DistribScanSteps/{1}/bins_{0}_{2}/cards_{3}_bins_{0}_{2}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins_2b0j),mode_str,str(nBins_boosted),channel)))
    thread.start()
    # wait here for the result to be available before continuing
    thread.join()

    with open("DistribScanSteps/{1}/bins_{0}_{2}/cards_{3}_bins_{0}_{2}/ggHH_bbtt11BDToutSM_kl_1/out_Asym_ggHH_bbtt11_blind.log".format(str(nBins_2b0j),mode_str,str(nBins_boosted),channel),'r') as limits_file:
        lines = limits_file.readlines()
        try:
            open("DistribScanSteps/{0}/all_limits.txt".format(mode_str),"r")
        except IOError:
            all_limits = open("DistribScanSteps/{0}/all_limits.txt".format(mode_str),"a")
            all_limits.write("ALL THE LIMITS CALCULATED IN THE DISTRIBUTION SCAN\n")
            all_limits.write("--------------------------------------------------\n")
        else:
            all_limits = open("DistribScanSteps/{0}/all_limits.txt".format(mode_str),"a")
        for line in lines:
            if "50.0" in line:
                result = float(line.split('< ')[1].replace('\n',''))
                all_limits.write("bins_{0}_{1}: ".format(str(nBins_2b0j),str(nBins_boosted))+str(result)+"\n")

    return result


###############################################################################
############################# MAIN OF THE PROGRAM #############################
###############################################################################

channel = "ETau"
#channel = "MuTau"
#channel = "TauTau"

global datasets_dir
datasets_dir = "/data_CMS/cms/motta/binOptDatasets"

# take a histogram as template
inRoot = TFile.Open("{1}/PreOptData/{0}/bin_dataNonRebinned1M/analyzedOutPlotter.root".format(channel,datasets_dir))
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

# SET THE OPTIMAL BINNIGS FOR THE TWO CATEGORIES AND THE BIN WINDOWS
optimal_bins_2b0j = 48
optimal_bins_boosted = 45
print('** OPTIMAL BINNING 2b0j CATEGORY = '+str(optimal_bins_2b0j)+' **')
print('** OPTIMAL BINNING boosted CATEGORY = '+str(optimal_bins_boosted)+' **')
# based on the best performing binning found for 2b0j, take a window of 5 different binnings (around the optimal) to be tested
global bins_window_2b0j
bins_window_2b0j = []
k = 0
for i in range(optimal_bins_2b0j-2,optimal_bins_2b0j+3): # the upper limit must be 1 unity bigger than the actual value we will want to test
    bins_window_2b0j.append(i)
    k += 1
# based on the best performing binning found for boosted, take a window of 5 different binnings (around the optimal) to be tested
global bins_window_boosted
bins_window_boosted = []
k = 0
for i in range(optimal_bins_boosted-2,optimal_bins_boosted+3): # the upper limit must be 1 unity bigger than the actual value we will want to test
    bins_window_boosted.append(i)
    k += 1

selections = ["s2b0jresolvedMcut", "sboostedLLMcut"]
variable = "BDToutSM_kl_1"
windows = [bins_window_2b0j, bins_window_boosted]

# CREATE ALL THE DATAFRAMES OF THE DIFFERENT DISTRIBUTIONS -> THEY WILL CONTAIN THE NEW BINNINGS
# ConstSize
df_ConstSize = pd.DataFrame(index=selections, columns=['optimal-2', 'optimal-1', 'optimal', 'optimal+1', 'optimal+2'])
for index in df_ConstSize.index.values:
    for column in df_ConstSize.columns.values:
        df_ConstSize[column][index] = []
# FlatS
df_flatS = pd.DataFrame(index=selections, columns=['optimal-2', 'optimal-1', 'optimal', 'optimal+1', 'optimal+2'])
for index in df_flatS.index.values:
    for column in df_flatS.columns.values:
        df_flatS[column][index] = []
# FlatB
df_flatB = pd.DataFrame(index=selections, columns=['optimal-2', 'optimal-1', 'optimal', 'optimal+1', 'optimal+2'])
for index in df_flatB.index.values:
    for column in df_flatB.columns.values:
        df_flatB[column][index] = []
# FlatSB
df_flatSB = pd.DataFrame(index=selections, columns=['optimal-2', 'optimal-1', 'optimal', 'optimal+1', 'optimal+2'])
for index in df_flatSB.index.values:
    for column in df_flatSB.columns.values:
        df_flatSB[column][index] = []


#########################################################################
# INSIDE THIS LOOP WE FILL THE DFs FOR ConstSize, FlatS, FlatB, FlatSB
for select in selections:
    # there is no iterative way of accessing these histos becase python does not know how to use += for the TH1Fs
    hSgn = inRoot.Get("GGHHSM_{0}_SR_{1}".format(select,variable))
    hQCD = inRoot.Get("QCD_{0}_SR_{1}".format(select,variable))
    hDY = inRoot.Get("DY_{0}_SR_{1}".format(select,variable))
    hTT = inRoot.Get("TT_{0}_SR_{1}".format(select,variable))
    hVVV = inRoot.Get("tripleV_{0}_SR_{1}".format(select,variable))
    hWJets = inRoot.Get("WJets_{0}_SR_{1}".format(select,variable))
    hVV = inRoot.Get("doubleV_{0}_SR_{1}".format(select,variable))
    hTTVV = inRoot.Get("doubleTVV_{0}_SR_{1}".format(select,variable))
    hTTV = inRoot.Get("doubleTsingleV_{0}_SR_{1}".format(select,variable))
    hEWK = inRoot.Get("EWK_{0}_SR_{1}".format(select,variable))
    hggH = inRoot.Get("ggHTauTau_{0}_SR_{1}".format(select,variable))
    hVBFH = inRoot.Get("VBFHTauTau_{0}_SR_{1}".format(select,variable))
    httH = inRoot.Get("ttH_{0}_SR_{1}".format(select,variable))
    hVH = inRoot.Get("VH_{0}_SR_{1}".format(select,variable))
    hsingleT = inRoot.Get("singleT_{0}_SR_{1}".format(select,variable))
    # protection against negative bins
    makeNonNegativeHistos(hSgn)
    makeNonNegativeHistos(hQCD)
    makeNonNegativeHistos(hDY)
    makeNonNegativeHistos(hTT)
    makeNonNegativeHistos(hVVV)
    makeNonNegativeHistos(hWJets)
    makeNonNegativeHistos(hVV)
    makeNonNegativeHistos(hTTVV)
    makeNonNegativeHistos(hTTV)
    makeNonNegativeHistos(hEWK)
    makeNonNegativeHistos(hggH)
    makeNonNegativeHistos(hVBFH)
    makeNonNegativeHistos(httH)
    makeNonNegativeHistos(hVH)
    makeNonNegativeHistos(hsingleT)
    hBkg = hQCD + hDY + hTT + hVVV + hWJets + hVV + hTTVV + hTTV + hEWK + hggH + hVBFH + httH + hVH + hsingleT

    ###################################################
    # ConstSize (BDToutSM_kl_1 bins of constant width)
    k = 0
    if select == 's2b0jresolvedMcut': bins_window = windows[0]
    if select == 'sboostedLLMcut': bins_window = windows[1]
    for column in df_ConstSize.columns.values:
        # define array of the new bins edges based on the number of bins to be tested
        df_ConstSize[column][select].append(-1.)
        step = 2.0/float(bins_window[k])
        i = 0
        # the loop looks a bit redundant with the if inside the while, but it is to protect against having both 0.99999999 and 1 at the end of the array
        while df_ConstSize[column][select][i] < 1.:
            df_ConstSize[column][select].append(df_ConstSize[column][select][i]+step)
            if df_ConstSize[column][select][i+1]+step > 1.00001:
                df_ConstSize[column][select].remove(df_ConstSize[column][select][i+1])
                df_ConstSize[column][select].append(1.0)
                break
            i += 1
        k += 1
    # delete the variables to allow next step
    del bins_window

    ####################################
    # FlatS (BDToutSM_kl_1 flat in sgn)
    template = hSgn
    integral = float(template.Integral())
    axis = template.GetXaxis()
    if select == 's2b0jresolvedMcut': bins_window = windows[0]
    if select == 'sboostedLLMcut': bins_window = windows[1]
    k = 0
    for column in df_flatS.columns.values:
        y = 0
        df_flatS[column][select].append(-1.)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatS[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatS[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatS[column][select].append(1.)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatS[column][select]) - (bins_window[k]+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,(df_flatS[column][select][0]+df_flatS[column][select][1])/2)
        elif len(df_flatS[column][select]) - (bins_window[k]+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/3.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 2BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_window[k]+1) == -3: # if three bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/4.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+3*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" 3BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_window[k]+1) <= -4:
            print("** THE FlatS "+select+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatS[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** SUBSTITUTING BINS WITH CONSTANT WIDTH BINS **")
            df_flatS[column][select] = df_ConstSize[column][select]
        k += 1
    # delete the variables to allow next step
    del template, bins_window

    ####################################
    # FlatB (BDToutSM_kl_1 flat in bkg)
    template = hBkg
    integral = float(template.Integral())
    axis = template.GetXaxis()
    if select == 's2b0jresolvedMcut': bins_window = windows[0]
    if select == 'sboostedLLMcut': bins_window = windows[1]
    k = 0
    for column in df_flatB.columns.values:
        y = 0
        df_flatB[column][select].append(-1.)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatB[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatB[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatB[column][select].append(1.)
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
            print("** SUBSTITUTING BINS WITH CONSTANT WIDTH BINS **")
            df_flatB[column][select] = df_ConstSize[column][select]
        k += 1
    # delete the variables to allow next step
    del template, bins_window

    ###########################################
    # FlatSB (BDToutSM_kl_1 flat in sgn+bkg)
    template = hSgn + hBkg
    integral = float(template.Integral())
    axis = template.GetXaxis()
    if select == 's2b0jresolvedMcut': bins_window = windows[0]
    if select == 'sboostedLLMcut': bins_window = windows[1]
    k = 0
    for column in df_flatSB.columns.values:
        y = 0
        df_flatSB[column][select].append(-1.)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_window[k]):
                if abs(y - integral/float(bins_window[k])) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_window[k])):
                    df_flatSB[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatSB[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatSB[column][select].append(1.)
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
            print("** SUBSTITUTING BINS WITH CONSTANT WIDTH BINS **")
            df_flatSB[column][select] = df_ConstSize[column][select]
        k += 1
    # delete the variables to avoid strange things happening at the next round of the select loop
    del template, bins_window
    del hQCD, hDY, hTT, hVVV, hWJets, hVV, hTTVV, hTTV, hEWK, hggH, hVBFH, httH, hVH, hsingleT, hSgn, hBkg


##################################
# DO THE ACTUAL DISTRIBUTION SCAN
# mode_str STRINGS FOR THE HPlimit_extraction FUNCTION ARE:
# FlatS
# FlatB
# FlatSB
# ConstSize

# create the folders that will contain all the results
mkdir_cmd = "mkdir DistribScanSteps"
print("Executing: "+mkdir_cmd)
os.system(mkdir_cmd)
mkdir_cmd1 = "mkdir DistribScanSteps/FlatS"
print("Executing: "+mkdir_cmd1)
os.system(mkdir_cmd1)
mkdir_cmd2 = "mkdir DistribScanSteps/FlatB"
print("Executing: "+mkdir_cmd2)
os.system(mkdir_cmd2)
mkdir_cmd3 = "mkdir DistribScanSteps/FlatSB"
print("Executing: "+mkdir_cmd3)
os.system(mkdir_cmd3)
mkdir_cmd4 = "mkdir DistribScanSteps/ConstSize"
print("Executing: "+mkdir_cmd4)
os.system(mkdir_cmd4)

# create a single dataframe that will contain all the results of the distribution scan
df_results = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=['{0}_2b0j/{1}_boosted'.format(bins_window_2b0j[0],bins_window_boosted[0]),'{0}_2b0j/{1}_boosted'.format(bins_window_2b0j[1],bins_window_boosted[1]),'{0}_2b0j/{1}_boosted'.format(bins_window_2b0j[2],bins_window_boosted[2]),'{0}_2b0j/{1}_boosted'.format(bins_window_2b0j[3],bins_window_boosted[3]),'{0}_2b0j/{1}_boosted'.format(bins_window_2b0j[4],bins_window_boosted[4])])
# fill it
k = 0
for (nBins_2b0j,nBins_boosted) in zip(bins_window_2b0j,bins_window_boosted):
    if k == 0: column = 'optimal-2'
    if k == 1: column = 'optimal-1'
    if k == 2: column = 'optimal'
    if k == 3: column = 'optimal+1'
    if k == 4: column = 'optimal+2'
    df_results['{0}_2b0j/{1}_boosted'.format(nBins_2b0j,nBins_boosted)]['ConstSize'] = HPlimit_extraction(bins_window_2b0j[k],bins_window_boosted[k],df_ConstSize[column]['s2b0jresolvedMcut'],df_ConstSize[column]['sboostedLLMcut'],'ConstSize')*1000.
    df_results['{0}_2b0j/{1}_boosted'.format(nBins_2b0j,nBins_boosted)]['FlatS'] = HPlimit_extraction(bins_window_2b0j[k],bins_window_boosted[k],df_flatS[column]['s2b0jresolvedMcut'],df_flatS[column]['sboostedLLMcut'],'FlatS')*1000.
    df_results['{0}_2b0j/{1}_boosted'.format(nBins_2b0j,nBins_boosted)]['FlatB'] = HPlimit_extraction(bins_window_2b0j[k],bins_window_boosted[k],df_flatB[column]['s2b0jresolvedMcut'],df_flatB[column]['sboostedLLMcut'],'FlatB')*1000.
    df_results['{0}_2b0j/{1}_boosted'.format(nBins_2b0j,nBins_boosted)]['FlatSB'] = HPlimit_extraction(bins_window_2b0j[k],bins_window_boosted[k],df_flatSB[column]['s2b0jresolvedMcut'],df_flatSB[column]['sboostedLLMcut'],'FlatSB')*1000.
    k += 1

df_results.rename(index={'FlatSB':'FlatS+B'})
df_results.to_html('DistribScanSteps/distribScanResults.html')


##########################################################################################################################
# SOME PRINTS TO CHECK IF THE BINNINGS WE ARE PRODUCING ARE CORRECT IN LEGTH OR IF WE ARE PRODUCING LESS BINS THAN NEEDED
#print('\nConstSize')
#print("resolved")
#print("-> "+str(len(df_ConstSize['optimal-2']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_ConstSize['optimal-1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_ConstSize['optimal']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_ConstSize['optimal+1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_ConstSize['optimal+2']['s2b0jresolvedMcut'])))
#print("boosted")
#print("-> "+str(len(df_ConstSize['optimal-2']['sboostedLLMcut'])))
#print("-> "+str(len(df_ConstSize['optimal-1']['sboostedLLMcut'])))
#print("-> "+str(len(df_ConstSize['optimal']['sboostedLLMcut'])))
#print("-> "+str(len(df_ConstSize['optimal+1']['sboostedLLMcut'])))
#print("-> "+str(len(df_ConstSize['optimal+2']['sboostedLLMcut'])))
#print('\nFLAT S')
#print("resolved")
#print("-> "+str(len(df_flatS['optimal-2']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatS['optimal-1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatS['optimal']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatS['optimal+1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatS['optimal+2']['s2b0jresolvedMcut'])))
#print("boosted")
#print("-> "+str(len(df_flatS['optimal-2']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatS['optimal-1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatS['optimal']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatS['optimal+1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatS['optimal+2']['sboostedLLMcut'])))
#print('\nFLAT B')
#print("resolved")
#print("-> "+str(len(df_flatB['optimal-2']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatB['optimal-1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatB['optimal']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatB['optimal+1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatB['optimal+2']['s2b0jresolvedMcut'])))
#print("boosted")
#print("-> "+str(len(df_flatB['optimal-2']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatB['optimal-1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatB['optimal']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatB['optimal+1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatB['optimal+2']['sboostedLLMcut'])))
#print('\nFLAT S+B')
#print("resolved")
#print("-> "+str(len(df_flatSB['optimal-2']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatSB['optimal-1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatSB['optimal']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatSB['optimal+1']['s2b0jresolvedMcut'])))
#print("-> "+str(len(df_flatSB['optimal+2']['s2b0jresolvedMcut'])))
#print("boosted")
#print("-> "+str(len(df_flatSB['optimal-2']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatSB['optimal-1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatSB['optimal']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatSB['optimal+1']['sboostedLLMcut'])))
#print("-> "+str(len(df_flatSB['optimal+2']['sboostedLLMcut'])))
