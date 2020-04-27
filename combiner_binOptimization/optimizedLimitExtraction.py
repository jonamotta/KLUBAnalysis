import os
import sys
import time
from ROOT import *
import ROOT
import numpy as np
import pandas as pd
from array import array

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
def limit_extraction(nBins,new_bins_edges_dataframe):
    # adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
    for index in new_bins_edges_dataframe.index.values:
        for column in new_bins_edges_dataframe.columns.values:
            adjust_new_bins(new_bins_edges_dataframe[column][index])

    # create folder of the specific mode and number of bins we are testing and copy cfgs in it
    mkdirETau_cmd = "mkdir OptimizedLimit/ETau"
    print("Executing: "+mkdirETau_cmd)
    os.system(mkdirETau_cmd)
    mkdirMuTau_cmd = "mkdir OptimizedLimit/MuTau"
    print("Executing: "+mkdirMuTau_cmd)
    os.system(mkdirMuTau_cmd)
    mkdirTauTau_cmd = "mkdir OptimizedLimit/TauTau"
    print("Executing: "+mkdirTauTau_cmd)
    os.system(mkdirTauTau_cmd)
    for ch in channels:
        tag = "{0}_Legacy2018_binOptimization.cfg".format(ch)
        inDir = "{1}/OptimizedLimitData/{0}/".format(ch,datasets_dir)
        copy_cmd = "cp -a {2}/mainCfg_{0} OptimizedLimit/{1}/; cp -a {2}/selectionCfg_{0} OptimizedLimit/{1}/; cp -a {2}/sampleCfg_Legacy2018.cfg OptimizedLimit/{1}/; cp -a {2}/outPlotter.root OptimizedLimit/{1}/".format(tag,ch,inDir)
        print("Executing: "+copy_cmd)
        os.system(copy_cmd)

        # append rebinning section in the mainCfg
        mainCfg = open("OptimizedLimit/{0}/mainCfg_{1}".format(ch,tag), "a")
        mainCfg.write("[pp_rebin]\n")
        # convert new binning edges to string and write them in the mainCfg
        edges2b0j_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['s2b0jresolvedMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edgesboosted_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['sboostedLLMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edges1b1j_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['s1b1jresolvedMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        edgesVBFloose_string = np.array2string(np.array(new_bins_edges_dataframe[ch]['VBFlooseMcut']), separator=',', max_line_width=None, precision=20).replace('\n','')
        mainCfg.write("r1 = BDToutSM_kl_1, sboostedLLMcut, %s \n" % edgesboosted_string.replace('[','').replace(']',''))
        mainCfg.write("r2 = BDToutSM_kl_1, s2b0jresolvedMcut, %s \n" % edges2b0j_string.replace('[','').replace(']',''))
        mainCfg.write("r3 = BDToutSM_kl_1, s1b1jresolvedMcut, %s \n" % edges1b1j_string.replace('[','').replace(']',''))
        mainCfg.write("r4 = BDToutSM_kl_1, VBFlooseMcut, %s \n" % edgesVBFloose_string.replace('[','').replace(']',''))
        mainCfg.write("r5 = BDToutSM_kl_1, VBFtightMcut, %s \n" % edgesVBFloose_string.replace('[','').replace(']','')) # for now VBFtight is always empty -> we use VBFloose binning cause we are not optimizing its own

        mainCfg.close()

        # call combineFillerOutputs.py
        comb_cmd = "python ../scripts/combineFillerOutputs.py --dir OptimizedLimit/{0}".format(ch)
        print("Executing: "+comb_cmd)
        os.system(comb_cmd)

        # call wrapperHistos.py
        wrapper_cmd = "python wrapperHistos.py -f OptimizedLimit/{0}/analyzedOutPlotter.root -c {0} -o {0} -d OptimizedLimit -a 'GGF'".format(ch)
        print("Executing: "+wrapper_cmd)
        os.system(wrapper_cmd)

        copy_cmd = "cp -a OptimizedLimit/{1}/mainCfg_{0} OptimizedLimit/; cp -a OptimizedLimit/{1}/selectionCfg_{0} OptimizedLimit/".format(tag,ch)
        print("Executing: "+copy_cmd)
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
    file.writelines(lines[5:])
    file.close()
    prepend_line("makeCategories_optimized.sh",'export SELECTIONS="s2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFlooseMcut VBFtightMcut"')
    prepend_line("makeCategories_optimized.sh",'export LEPTONS="ETau MuTau TauTau"')
    prepend_line("makeCategories_optimized.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/combiner_binOptimization/OptimizedLimit/"')
    prepend_line("makeCategories_optimized.sh",'export TAG="optimized"')
    prepend_line("makeCategories_optimized.sh","#!/bin/bash")

    # call makeCategories_optimized.sh
    limits_cmd = "./makeCategories_optimized.sh"
    os.system('chmod 777 makeCategories_optimized.sh')
    os.system(limits_cmd)

    print("\n THE ANSWER TO THE ULTIMATE QUESTION OF LIFE, THE UNIVERSE AND EVERYTHING IS 42...")
    print("\n ...BUT IT IS NOT THE ANSWER TO THE LIMIT CALCULATION.")
    print("\n SO WHILE YOU WAIT FOR THE JOBS TO BE COMPLETED GO AND READ SOMETHING; I SUGGEST 'THE HITCHHIKERS GUIDE TO THE GALAXY', IT'S A GREAT BOOK!\n")



###############################################################################
############################# MAIN OF THE PROGRAM #############################
###############################################################################

global channels
channels = ["ETau", "MuTau", "TauTau"]

global datasets_dir
datasets_dir = "/data_CMS/cms/motta/binOptDatasets"

# take a histogram as template
inRoot = TFile.Open("{0}/OptimizedLimitData/TauTau/analyzedOutPlotter.root".format(datasets_dir))
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

# the VBFtight selection is missing because we will use the same binning of the VBFloose
selections = ["s2b0jresolvedMcut", "sboostedLLMcut", "s1b1jresolvedMcut", "VBFlooseMcut"]
variable = "BDToutSM_kl_1"

# CREATE ALL THE DATAFRAME OF THE DISTRIBUTION -> IT WILL CONTAIN THE NEW BINNINGS
# FlatS
df_flatS = pd.DataFrame(index=selections, columns=channels)
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
    for column in df_flatS.columns.values:
        # set the correct number of bins given the selection and the channel -> these values of optimized bins come from PostOptSteps
        if select == 's2b0jresolvedMcut':
            if column == "ETau": bins_number = 48
            if column == "MuTau": bins_number = 45
            if column == "TauTau": bins_number = 48
        if select == 'sboostedLLMcut':
            if column == "ETau": bins_number = 45
            if column == "MuTau": bins_number = 51
            if column == "TauTau": bins_number = 47
        if select == 's1b1jresolvedMcut':
            if column == "ETau": bins_number = 51
            if column == "MuTau": bins_number = 42
            if column == "TauTau": bins_number = 48
        if select == 'VBFlooseMcut':
            if column == "ETau": bins_number = 44
            if column == "MuTau": bins_number = 51
            if column == "TauTau": bins_number = 50
        y = 0
        df_flatS[column][select].append(-1.)
        for i in range(template.GetNbinsX()):
            y += float(template.GetBinContent(i))
            if y > integral/float(bins_number):
                if abs(y - integral/float(bins_number)) < abs(y - float(template.GetBinContent(i)) - integral/float(bins_number)):
                    df_flatS[column][select].append(axis.GetBinLowEdge(i+1))
                else:
                    df_flatS[column][select].append(axis.GetBinLowEdge(i))
                y = 0
        df_flatS[column][select].append(1.)
        # it could happen that the algorithm above produces 1/2 bins less then expected due to the acculmulation of the error in the quantile calculation
        # we correct for that by dividing the first bin in 2/3 to adjust the number of bins
        if len(df_flatS[column][select]) - (bins_number+1) == -1: # if only one bin is missing split the first in two equal size bins
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,(df_flatS[column][select][0]+df_flatS[column][select][1])/2)
        elif len(df_flatS[column][select]) - (bins_number+1) == -2: # if two bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/3.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" "+column+" 2BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_number+1) == -3: # if three bins are missing spit the first in three equal size bins
            step = abs(df_flatS[column][select][0]-df_flatS[column][select][1])/4.
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+3*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+2*step)
            df_flatS[column][select] = np.insert(df_flatS[column][select],1,df_flatS[column][select][0]+step)
            print("** FlatS "+select+" "+column+" 3BIN CORRECTION DONE **")
        elif len(df_flatS[column][select]) - (bins_number+1) <= -3:
            print("** THE FlatS "+select+" "+column+" ALGORITHM HAS PRODUCED A NUMBER OF BINS CONSIDERABLY SMALLER THAN EXPECTED: "+str(len(df_flatS[column][select])-1)+" INSTEAD OF "+str(column).replace('_',' ')+" **")
            print("** EXITING THE PROGRAM **")
            sys.exit(1)
    # delete the variables to allow next step
    del template, bins_number

#######################################################################################################################################
# MODIFICATION OF THE BINNING OF POORELY POPULATED CATEGORIES TO CHECK THAT WE ARE NOT PUSHING (BIASING) THE LIMIT THROUGH THE BINNING
# the 'rebinning' is based on the visual appearence of the plots produced in OptimizedLimit
print("\n ** RENBINNING THE POORELY POPULATED CATEGORIES ** \n")
# ETau - boosted rebinning
for i in range(len(df_flatS['ETau']["sboostedLLMcut"])):
    if df_flatS['ETau']["sboostedLLMcut"][i] > 0.7:
        cut_here = i
        break
df_flatS['ETau']["sboostedLLMcut"] = df_flatS['ETau']["sboostedLLMcut"][:cut_here+1]
df_flatS['ETau']["sboostedLLMcut"] = df_flatS['ETau']["sboostedLLMcut"].tolist()
df_flatS['ETau']["sboostedLLMcut"].append(1.)
# MuTau - boosted rebinning
for i in range(len(df_flatS['MuTau']["sboostedLLMcut"])):
    if df_flatS['MuTau']["sboostedLLMcut"][i] > 0.6:
        cut_here = i
        break
df_flatS['MuTau']["sboostedLLMcut"] = df_flatS['MuTau']["sboostedLLMcut"][:cut_here+1]
df_flatS['MuTau']["sboostedLLMcut"] = df_flatS['MuTau']["sboostedLLMcut"].tolist()
df_flatS['MuTau']["sboostedLLMcut"].append(1.)
# TauTau - boosted rebinning
for i in range(len(df_flatS['TauTau']["sboostedLLMcut"])):
    if df_flatS['TauTau']["sboostedLLMcut"][i] > 0.62:
        cut_here = i
        break
df_flatS['TauTau']["sboostedLLMcut"] = df_flatS['TauTau']["sboostedLLMcut"][:cut_here+1]
df_flatS['TauTau']["sboostedLLMcut"] = df_flatS['TauTau']["sboostedLLMcut"].tolist()
df_flatS['TauTau']["sboostedLLMcut"].append(1.)
# TauTau - VBFloose rebinning
for i in range(len(df_flatS['TauTau']["VBFlooseMcut"])):
    if df_flatS['TauTau']["VBFlooseMcut"][i] > 0.8:
        cut_here = i
        break
df_flatS['TauTau']["VBFlooseMcut"] = df_flatS['TauTau']["VBFlooseMcut"][:cut_here]
df_flatS['TauTau']["VBFlooseMcut"] = df_flatS['TauTau']["VBFlooseMcut"].tolist()
df_flatS['TauTau']["VBFlooseMcut"].append(1.)



# create the forder to store the limit extraction results
mkdir_cmd = "mkdir OptimizedLimit"
print("Executing: "+mkdir_cmd)
os.system(mkdir_cmd)

limit_extraction('optimized',df_flatS)



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
