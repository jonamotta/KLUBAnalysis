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
def limit_calculation(new_bins_edges_dataframe):
	# adjust the new bins to match the nearest edge of the old binning -> this avoids problems in the rebinning when calling combineFillerOutputs.py
	for index in new_bins_edges_dataframe.index.values:
		for column in new_bins_edges_dataframe.columns.values:
			adjust_new_bins(new_bins_edges_dataframe[column][index])

	# create folder of the specific channels and copy cfgs in it
	os.system("mkdir {0}optimizedLimit_Legacy{1}/ETau".format(analysis,year))
	os.system("mkdir {0}optimizedLimit_Legacy{1}/MuTau".format(analysis,year))
	os.system("mkdir {0}optimizedLimit_Legacy{1}/TauTau".format(analysis,year))
	sel_string = " ".join([str(sel) for sel in selections])
	for ch in channels:
		os.system("cp -a {0}/Legacy{1}/{2}/minibinned/mainCfg* {3}optimizedLimit_Legacy{1}/{2}/".format(datasets_dir,year,ch,analysis))

		# append rebinning section in the mainCfg
		mainCfg = open("{2}optimizedLimit_Legacy{1}/{0}/mainCfg_{0}_Legacy{1}_binOptimization.cfg".format(ch,year,analysis), "a")
		mainCfg.write("[pp_rebin]\n")
		# convert new binning edges to string and write them in the mainCfg
		for sel, i in zip(selections,range(1,len(selections)+1)):
			edges_string = np.array2string(np.array(new_bins_edges_dataframe[ch][sel]), separator=',', max_line_width=None, precision=20).replace('\n','')
			mainCfg.write("r{0} = {1}, {2}, %s \n".format(i,variable,sel) % edges_string.replace('[','').replace(']',''))
		mainCfg.close()

		# prune, rebin, wrap and copy
		os.system("python ../scripts/pruneAndRebinFillerOutputs.py --inDir {0}/Legacy{1}/{2}/minibinned/ --outDir {4}optimizedLimit_Legacy{1}/{2} --sel '{3}'".format(datasets_dir,year,ch,sel_string,analysis))
		os.system("python wrapperHistos.py -f {1}optimizedLimit_Legacy{2}/{0}/prunedAnalyzedOutPlotter.root -c {0} -o {0} -d {1}optimizedLimit_Legacy{2} -a '{1}' -y {2}".format(ch,analysis,year))
		os.system("cp -a {2}optimizedLimit_Legacy{1}/{0}/mainCfg_{0}_Legacy{1}_binOptimization.cfg {2}optimizedLimit_Legacy{1}/".format(ch,year,analysis))
	print("** FINISHED WRAPPING **")

	file = open("makeCategoriesLegacy.sh","r")
	lines = file.readlines()
	file.close()
	os.system("rm makeCategoriesLegacy.sh")
	file = open("makeCategoriesLegacy.sh","w")
	file.writelines(lines[7:])
	file.close()
	prepend_line("makeCategoriesLegacy.sh",'export VAR="{0}"'.format(variable))
	prepend_line("makeCategoriesLegacy.sh",'export YEAR="{0}"'.format(year))
	prepend_line("makeCategoriesLegacy.sh",'export SELECTIONS="{0}"'.format(sel_string))
	ch_string = " ".join([str(ch) for ch in channels])
	prepend_line("makeCategoriesLegacy.sh",'export LEPTONS="{0}"'.format(ch_string))
	prepend_line("makeCategoriesLegacy.sh",'export CF="$CMSSW_BASE/src/KLUBAnalysis/binOptimization_Legacy/{0}optimizedLimit_Legacy{1}/"'.format(analysis, year))
	prepend_line("makeCategoriesLegacy.sh",'export TAG="optimized"')
	prepend_line("makeCategoriesLegacy.sh","#!/bin/bash")

	os.system('chmod 777 makeCategoriesLegacy.sh')
	os.system('./makeCategoriesLegacy.sh')

	print("\n\n THE ANSWER TO THE ULTIMATE QUESTION OF LIFE, THE UNIVERSE AND EVERYTHING IS 42...")
	print(" ...BUT IT IS NOT THE ANSWER TO THE LIMIT CALCULATION!")
	print(" SO WHILE YOU WAIT FOR THE JOBS TO BE COMPLETED GO AND READ SOMETHING; I SUGGEST 'THE HITCHHIKERS GUIDE TO THE GALAXY', IT'S A GREAT BOOK!\n")

	return



###############################################################################
################################# MAIN PROGRAM ################################
###############################################################################

parser = argparse.ArgumentParser(description='Command line parser of hyperparameters scan options')
parser.add_argument('--ch', dest='ch', help='channels to use (str of channels names separated by space)', default=None)
parser.add_argument('--year', dest='year', help='year to use', default=None)
parser.add_argument('--var', dest='var', help='variable to use', default=None)
parser.add_argument('--sel', dest='sel', help='selections to use (str of selection complete names separated by space)')
parser.add_argument('--dir', dest='dir', help='directory where to find the distributions with minibins')
parser.add_argument('--analysis', dest='analysis', help='type of analysis we are doing: GGF or VBF')
args = parser.parse_args()

global year
global variable
global channels
global selections
global coarsing_step
global bins_window
global datasets_dir
global analysis
year = args.year
variable = args.var
channels = args.ch.split(" ")
selections = args.sel.split(" ")
datasets_dir = args.dir
analysis = args.analysis

print("** VARIABLE: {0} **".format(variable))
print("** CHANNELS: {0} **".format(channels))
print("** YEAR: {0} **".format(year))
print("** SELECTIONS: {0} **".format(args.sel))

inRoot = TFile.Open("{0}/Legacy{1}/TauTau/minibinned/analyzedOutPlotter.root".format(datasets_dir,year))

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

# FILL DATAFRAMEs WITH THE OPTIMIZED SPECIFICATIONS FOR THE BINNING
df_distribs = pd.DataFrame(index=selections, columns=channels)
df_numb_bins = pd.DataFrame(index=selections, columns=channels)
for ch in channels:
	file = open("optBinConfig/{0}{1}.txt".format(ch,year),"r")
	lines = file.readlines()
	for line in lines:
		specs = line.split()
		for sel in selections:
			if specs[0] == sel:
				df_distribs[ch][sel] = specs[1]
				df_numb_bins[ch][sel] = specs[2]
	del lines
	file.close() 

print("")
print("INFO : Optimized distributions")
print(df_distribs)
print("\nINFO : Optimized number of bins")
print(df_numb_bins)
print("")

# CREATE THE DATAFRAME OF THE DISTRIBUTIONS -> IT WILL CONTAIN THE NEW BINNINGS
df_opt_bins = pd.DataFrame(index=selections, columns=channels)
for index in df_opt_bins.index.values:
	for column in df_opt_bins.columns.values:
		df_opt_bins[column][index] = []


######################################################################
# INSIDE THE FOLLOWING LOOP WE FILL THE DF FOR THE OPTIMIZED BINNINGS

bkgList = ['QCD', 'TT', 'DYtot', 'others']
sigList = ['GGHHSM']
doOverflow = False
for select in selections:
	for ch in channels:
		print(ch+"  "+select)
		# open the right root file
		RootFile = TFile.Open("{0}/Legacy{1}/{2}/minibinned/analyzedOutPlotter.root".format(datasets_dir,year,ch))
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
			if len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -1: # if only one bin is missing split the first in two equal size bins
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -2: # if two bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatS "+select+" 2BIN CORRECTION DONE **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -3: # if three bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatS "+select+" 3BIN CORRECTION DONE **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) <= -4:
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
			if len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -1: # if only one bin is missing split the first in two equal size bins
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -2: # if two bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatB "+select+" 2BIN CORRECTION **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -3: # if three bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatB "+select+" 3BIN CORRECTION DONE **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) <= -4:
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
			if len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -1: # if only one bin is missing split the first in two equal size bins
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,(df_opt_bins[ch][select][0]+df_opt_bins[ch][select][1])/2)
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -2: # if two bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/3.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatSB "+select+" 2BIN CORRECTION DONE **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) == -3: # if three bins are missing spit the first in three equal size bins
				step = abs(df_opt_bins[ch][select][0]-df_opt_bins[ch][select][1])/4.
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+3*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+2*step)
				df_opt_bins[ch][select] = np.insert(df_opt_bins[ch][select],1,df_opt_bins[ch][select][0]+step)
				print("** FlatSB "+select+" 3BIN CORRECTION DONE **")
			elif len(df_opt_bins[ch][select]) - (int(numb_bins)+1) <= -4:
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
os.system("mkdir {0}optimizedLimit_Legacy{1}".format(analysis, year))
# calculate the limits
print("")
limit_calculation(df_opt_bins)

















