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
def get_result(file_path, lambdaName):
	# check that the limits were calculated
	dir_to_check = file_path.split("/{0}".format(lambdaName))[0]
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
	return round(result,2)

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
def limit_calculation(nBins,new_bins_edges,mode_str,sel):
	if nBins >= bins_window[0]+3*coarsing_step:
		if results_dict["df_results_{0}".format(sel)][nBins-coarsing_step][mode_str] == -993:
			print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,sel,nBins))
			print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
			result = -993
			return result
		if results_dict["df_results_{0}".format(sel)][nBins-3*coarsing_step][mode_str] == -995 or results_dict["df_results_{0}".format(sel)][nBins-3*coarsing_step][mode_str] == -997 or results_dict["df_results_{0}".format(sel)][nBins-3*coarsing_step][mode_str] == -999:
			if results_dict["df_results_{0}".format(sel)][nBins-2*coarsing_step][mode_str] == -995 or results_dict["df_results_{0}".format(sel)][nBins-2*coarsing_step][mode_str] == -997 or results_dict["df_results_{0}".format(sel)][nBins-2*coarsing_step][mode_str] == -999:
				if results_dict["df_results_{0}".format(sel)][nBins-coarsing_step][mode_str] == -995 or results_dict["df_results_{0}".format(sel)][nBins-coarsing_step][mode_str] == -997 or results_dict["df_results_{0}".format(sel)][nBins-coarsing_step][mode_str] == -999:
					print("\n** THE {0} {1} {2}bins CONFIGURATION IS VERY UNLIKELY TO BE INTERESTING **".format(mode_str,sel,nBins))
					print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
					result = -993
					return result

	# if the calculation of the bins edges goes wrong it returns the result [-1,1]
	# when this happens we skip the calculation of the limit
	# we return a specific value to know what happened at the end
	if len(new_bins_edges) == 2:
		print("\n** THE {0} {1} {2}bins CONFIGURATION WAS NOT CALCULATED DUE TO PRECISION LIMITATION IN THE QUANTILE CALCULATION **".format(mode_str,sel,nBins))
		print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
		result = -995
		return result
	
	# adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
	adjust_new_bins(new_bins_edges)

	# protection against too scattered distributions -> it goes toward the continuous limit calculation and we don't want it
	# if the binning we get is to thin we reject it -> 0.009 is somewhat arbitrary and correspond to 200 same width bins
	# we return a specific value to know what happened at the end
	if mode_str != "ConstSize":
		for index in range(0,len(new_bins_edges)-1):
			if new_bins_edges[index] <= variable_min+abs(variable_max-variable_min)/4: continue # we do not apply this protection for the first 4th of the score
			if abs(new_bins_edges[index] - new_bins_edges[index+1]) <= 0.01:
				print("\n** THE {0} {1} {2}bins CONFIGURATION IS TOO SCATTERED **".format(mode_str,sel,nBins))
				print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
				result = -999
				return result

	i = 0
	not_sel = []
	for select in selections:
		if sel in select:
			continue
		not_sel.append(select)

	# create folder of the specific mode and number of bins we are testing and copy cfgs in it
	os.system("mkdir ScanSteps_{3}{4}{5}/{0}/{2}/bins_{1}".format(mode_str,str(nBins),sel,channel,year,variable))
	os.system("cp {0}/mainCfg* ScanSteps_{1}{2}{3}/{4}/{5}/bins_{6}".format(datasets_dir,channel,year,variable,mode_str,sel,str(nBins)))

	# append rebinning section in the mainCfg
	mainCfg = open("ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/mainCfg_{3}_Legacy{4}_binOptimization.cfg".format(str(nBins),mode_str,sel,channel,year,variable), "a")
	mainCfg.write("[pp_rebin]\n")
	# convert new binning edges to string and write them in the mainCfg
	edges_string = np.array2string(np.array(new_bins_edges), separator=',', max_line_width=None, precision=20).replace('\n','')
	mainCfg.write("r1 = {0}, {1}, %s \n".format(variable,sel) % edges_string.replace('[','').replace(']',''))
	mainCfg.close()

	os.system("python ../scripts/pruneAndRebinFillerOutputs.py --inDir {6} --outDir ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0} --sel '{7}'".format(str(nBins),mode_str,sel,channel,year,variable, datasets_dir,sel))
	print("")
	os.system("python ../scripts/pruneAndRebinFillerOutputs.py --inDir {6} --outDir ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0} --sel '{7}' --tag _NONweighted".format(str(nBins),mode_str,sel,channel,year,variable, datasets_dir,sel))
	
	# protection against almost empty bins -> can create bias in the final result
	# 1. we take the NON weighted histograms of the two most important backgrounds (which are also the ones we control the best)
	bkgListNonWeighted = ['TT', 'DYtot']
	doOverflow = False
	checkNonWeighted = TFile.Open("ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/prunedAnalyzedOutPlotter_NONweighted.root".format(str(nBins),mode_str,sel,channel,year,variable))
	hBkgsNonWeighted = retrieveHistos(checkNonWeighted,bkgListNonWeighted,variable,sel,"SR")
	hTT_NonWeighted = getHisto("TT",hBkgsNonWeighted,doOverflow)
	hDY_NonWeighted = getHisto("DYtot",hBkgsNonWeighted,doOverflow)
	makeNonNegativeHistos(hTT_NonWeighted)
	makeNonNegativeHistos(hDY_NonWeighted)
	# 2. we take the weighted histograms of all the backgrounds
	check = TFile.Open("ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/prunedAnalyzedOutPlotter.root".format(str(nBins),mode_str,sel,channel,year,variable))
	bkgList = ['QCD', 'TT', 'DYtot', 'others']
	hBkgs = retrieveHistos(check,bkgList,variable,sel,"SR")
	hQCD = getHisto("QCD",hBkgs,doOverflow)
	hTT = getHisto("TT",hBkgs,doOverflow)
	hDY = getHisto("DYtot",hBkgs,doOverflow)
	hOthers = getHisto("others",hBkgs,doOverflow)
	makeNonNegativeHistos(hQCD)
	makeNonNegativeHistos(hTT)
	makeNonNegativeHistos(hDY)
	makeNonNegativeHistos(hOthers)
	hBkgList = [hQCD, hTT, hDY, hOthers]
	hBackground = makeSum("background",hBkgList)
	# a. I ask that in each bin I have at least one raw event of the two most important bkgs (i.e. ttbar and DY)
	for i in range(nBins-5,nBins+1):
		if hTT_NonWeighted.GetBinContent(i) < 1. and hDY_NonWeighted.GetBinContent(i) < 1.:
			print("** "+str(hBackground.GetBinContent(i))+" weighted events &"+str(hcontrolBkgNonWeighted.GetBinContent(i))+" raw event @ bin "+str(i)+" **")
			print("** THE {0} {1} {2}bin CONFIGURATION CAN CAUSE BIAS IN THE LIMIT EXTRACTION **".format(mode_str,sel,nBins))
			print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
			result = -997 # we return a specific value to know what happened at the end
			return result 
	# b. I ask that every bin is populated by at leats 0.15 weighted events
	for i in range(2,nBins+1):
		if hBackground.GetBinContent(i) < 0.15: # we choose 0.15 cause then 1 is inside the edge of 2sigma
			if hBackground.GetBinContent(i-1) > 0.15:
				print("** "+str(hBackground.GetBinContent(i))+" weighted events &"+str(hcontrolBkgNonWeighted.GetBinContent(i))+" raw event @ bin "+str(i)+" **")
				print("** THE {0} {1} {2}bin CONFIGURATION CAN CAUSE BIAS IN THE LIMIT EXTRACTION **".format(mode_str,sel,nBins))
				print("** IGNORING IT AND SKIPPING TO THE NEXT CONFIGURATION **\n")
				result = -997 # we return a specific value to know what happened at the end
				return result
	del checkNonWeighted, hBkgsNonWeighted, doOverflow, hTT_NonWeighted, hDY_NonWeighted, hBkgListNonWeighted, hcontrolBkgNonWeighted, check, hBkgs, hQCD, hTT, hDY, hOthers, hBkgList, hBackground

	if "VBF" in sel:
		prod_mode = "VBF"
	else:
		prod_mode = "GGF"
	os.system("python wrapperHistos.py -f ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/prunedAnalyzedOutPlotter.root -c {3} -o bins_{0} -d ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0} -a '{6}' -y {4}".format(str(nBins),mode_str,sel,channel,year,variable,prod_mode))

	file = open("makeCategoriesOptimizer{0}.sh".format(year),"r")
	lines = file.readlines()
	file.close()
	os.system("rm makeCategoriesOptimizer{0}.sh".format(year))
	file = open("makeCategoriesOptimizer{0}.sh".format(year),"w")
	file.writelines(lines[7:])
	file.close()
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export VAR="{0}"'.format(variable))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export YEAR="{0}"'.format(year))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export SELECTIONS="{0}"'.format(sel))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export LEPTONS="{0}"'.format(channel))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export CF="$CMSSW_BASE/src/KLUBAnalysis/binOptimization_Legacy/ScanSteps_{3}{4}{5}/{1}/{2}/bins_{0}/"'.format(str(nBins),mode_str,sel,channel,year,variable))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),'export TAG="bins_{0}"'.format(str(nBins)))
	prepend_line("makeCategoriesOptimizer{0}.sh".format(year),"#!/bin/bash")
	os.system("chmod 777 makeCategoriesOptimizer{0}.sh".format(year))

	os.system("./makeCategoriesOptimizer{0}.sh".format(year))

	print("\n** {0} {1} {2}bins DONE **\n".format(mode_str,sel,nBins))

	return 0

###############################################################################
################################# MAIN PROGRAM ################################
###############################################################################

parser = argparse.ArgumentParser(description='Command line parser of hyperparameters scan options')
parser.add_argument('--ch', dest='ch', help='channel to optimize', default=None)
parser.add_argument('--year', dest='year', help='year to optimize', default=None)
parser.add_argument('--var', dest='var', help='variable to optimize', default=None)
parser.add_argument('--sel', dest='sel', help='selections to optimize (str of selection complete names separated by space)')
parser.add_argument('--bins', dest='bins', help='from which number of bins to which number of bins (enter str with min and max separated by a space)', type=str)
parser.add_argument('--coarse', dest='coarse', help='step with which the bin scan has to be done', type=int)
parser.add_argument('--dir', dest='dir', help='directory where to find the distributions with minibins')
args = parser.parse_args()

global year
global variable
global channel
global selections
global coarsing_step
global bins_window
global datasets_dir
year = args.year
variable = args.var
channel = args.ch
selections = args.sel.split(" ")
coarsing_step = args.coarse
bins_window = range(int(args.bins.split(" ")[0]),int(args.bins.split(" ")[1]),coarsing_step)
datasets_dir = args.dir

print("** VARIABLE: {0} **".format(variable))
print("** CHANNEL: {0} **".format(channel))
print("** YEAR: {0} **".format(year))
print("** SELECTIONS: {0} **".format(args.sel))
print("** BINS RANGE TO SCAN: [{0},{1}] with step {2} **\n".format(args.bins.split(" ")[0],args.bins.split(" ")[1],coarsing_step))

# start clock
start = time.time()

inRoot = TFile.Open("{0}/analyzedOutPlotter.root".format(datasets_dir))

templateName = "GGHHSM_s2b0jresolvedMcut_SR_{0}".format(variable)
template = inRoot.Get(templateName)

# old_bins_edges contains the edges of the minibins -> they are used for the rebinning through combineFillerOutputs.py
nPoints  = template.GetNbinsX()
global old_bins_edges
old_bins_edges = [template.GetBinLowEdge(0)]
for ibin in range (1, nPoints+1):
	old_bins_edges.append(template.GetBinLowEdge(ibin+1))

# define the range in which the variable is defined; e.g. BDT = [-1,1] and DNN = [0,1]
global variable_min
global variable_max
variable_min = round(old_bins_edges[0],0)
variable_max = round(old_bins_edges[-1],0)

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
doOverflow = False
for select in selections:
	if "VBF" in select:
		sigList = ['VBFHHSM']
	else:
		sigList = ['GGHHSM']
	# there is no iterative way of accessing these histos becase python does not know how to use += for the TH1Fs
	hBkgs = retrieveHistos(inRoot,bkgList,variable,select,"SR")
	hSigs = retrieveHistos(inRoot,sigList,variable,select,"SR")
	if "VBF" in select:
		hSgn = getHisto("VBFHHSM",hSigs,doOverflow)
	else:
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

print("")

##################################
# DO THE ACTUAL DISTRIBUTION SCAN
# mode_str STRINGS FOR THE limit_calculation FUNCTION ARE:
# FlatS
# FlatB
# FlatSB
# ConstSize

# create the folders that will contain all the results
os.system("mkdir ScanSteps_{0}{1}{2}".format(channel,year,variable))
os.system("cp optimizer.py ScanSteps_{0}{1}{2}/".format(channel,year,variable))
os.system("mkdir ScanSteps_{0}{1}{2}/FlatS; mkdir ScanSteps_{0}{1}{2}/FlatB; mkdir ScanSteps_{0}{1}{2}/FlatSB; mkdir ScanSteps_{0}{1}{2}/ConstSize".format(channel,year,variable))
for sel in selections:
	os.system("mkdir ScanSteps_{0}{1}{2}/FlatS/{3}; mkdir ScanSteps_{0}{1}{2}/FlatB/{3}; mkdir ScanSteps_{0}{1}{2}/FlatSB/{3}; mkdir ScanSteps_{0}{1}{2}/ConstSize/{3}".format(channel,year,variable,sel))

global results_dict 
results_dict = {}
for sel in selections:
	results_dict["df_results_{0}".format(sel)] = pd.DataFrame(index=['ConstSize', 'FlatS', 'FlatB', 'FlatSB'],columns=bins_window)

# fill them
for sel in selections:
	for column in results_dict["df_results_{0}".format(sel)].columns.values:
		results_dict["df_results_{0}".format(sel)][column]['ConstSize'] = limit_calculation(int(column), df_ConstSize[column][sel], 'ConstSize', sel) 
		results_dict["df_results_{0}".format(sel)][column]['FlatS'] = limit_calculation(int(column), df_flatS[column][sel], 'FlatS', sel)
		results_dict["df_results_{0}".format(sel)][column]['FlatB'] = limit_calculation(int(column), df_flatB[column][sel], 'FlatB', sel)
		results_dict["df_results_{0}".format(sel)][column]['FlatSB'] = limit_calculation(int(column), df_flatSB[column][sel], 'FlatSB', sel)

# get the results of the limit extractions (-> the loop above only saves aeb, tsd and qcl)
for sel in selections:
	for dist in ["ConstSize", "FlatB", "FlatS", "FlatSB"]:
		for bins in bins_window:
			if "VBF" in sel:
				lambdaName = "VBFHH"
			else:
				lambdaName = "ggHH"
			
			results_dict["df_results_{0}".format(sel)][bins][dist] += get_result("ScanSteps_{2}{4}{3}/{0}/{5}/bins_{1}/cards_{2}_bins_{1}/{6}_bbtt11{5}{3}/out_Asym_{6}_bbtt11_blind.log".format(dist,bins,channel,variable,year,sel,lambdaName),lambdaName)
						
			# a little bit of cosmetics for the DataFrames
			if results_dict["df_results_{0}".format(sel)][bins][dist] == -993: results_dict["df_results_{0}".format(sel)][bins][dist] = "---"
			if results_dict["df_results_{0}".format(sel)][bins][dist] == -995: results_dict["df_results_{0}".format(sel)][bins][dist] = "q.c.l."
			if results_dict["df_results_{0}".format(sel)][bins][dist] == -997: results_dict["df_results_{0}".format(sel)][bins][dist] = "a.e.b."
			if results_dict["df_results_{0}".format(sel)][bins][dist] == -999: results_dict["df_results_{0}".format(sel)][bins][dist] = "t.s.d."

	# cosmetics for the html output
	for column in results_dict["df_results_{0}".format(sel)].columns.values:
		results_dict["df_results_{0}".format(sel)] = results_dict["df_results_{0}".format(sel)].rename(columns={column:str(column)+' bins'})
	results_dict["df_results_{0}".format(sel)] = results_dict["df_results_{0}".format(sel)].rename(index={'FlatSB':'FlatS+B'})

	# save the results
	results_dict["df_results_{0}".format(sel)].to_html('ScanSteps_{0}{1}{2}/results_{3}.html'.format(channel,year,variable,sel))


# stop clock and print time of running
end = time.time()
print('\n\nScan running time = {0}h {1}m {2}s'.format(int((end-start)/3600.),int(((end-start)/3600.)%1*60),int((((end-start)/3600.)%1*60)%1*60)))





