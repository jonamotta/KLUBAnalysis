from ROOT import *
import re
import os
import sys
import argparse
import fnmatch
import math
from array import array
import modules.ConfigReader as cfgr
import modules.OutputManager as omng

def findInFolder (folder, pattern):
		ll = []
		for ff in os.listdir(folder):
			if fnmatch.fnmatch(ff, pattern): ll.append(ff)
		if len (ll) == 0:
			print "*** WARNING: No valid" , pattern , "found in " , folder
			return None
		if len (ll) > 1:
			print "*** WARNING: Too many files found in " , folder , ", using first one : " , ll
		return ll[0]



def flatBinning(rootFile,namelist, var,sel,reg):
	for name in namelist:
		fullName = name + "_" + sel + "_" + reg + "_" + var
		if not rootFile.GetListOfKeys().Contains(fullName):
			print "*** WARNING: histo " , fullName , " not available"
			continue

		if 'GGHHSM' in name:
			h = rootFile.Get(fullName)

			nq = h.GetNbinsX()/10
			xq = array('d', [0.] * nq)
			yq = array('d', [0.] * nq)

			for i in xrange(nq):
						xq[i] = float(i + 1) / nq

			h.GetQuantiles(nq, yq, xq)
			print yq
			return yq

def retrieveHistos (rootFile, namelist, var, sel, reg,flat,binning):
	res = {}
	for name in namelist:
		fullName = name + "_" + sel + "_" + reg + "_" + var

		if not rootFile.GetListOfKeys().Contains(fullName):
			print "*** WARNING: histo " , fullName , " not available"
			continue
		h = rootFile.Get(fullName)

		if not args.flat:
				res[name] = h
		else:
				hreb = h.Rebin(len(binning)-1,"hreb",binning)
				res[name] = hreb

	return res

def getHisto (histoName,inputList,doOverflow):

		for idx, name in enumerate(inputList):

				if (name.startswith(histoName) and name.endswith(histoName)):
						h = inputList[name].Clone (histoName)
						if doOverflow: h = addOverFlow(h)
						break

		return h

### QCD is special and has a strange name, need data to recontruct it
### CORR_DDQCD_SS_DATA_HHKin_mass_SS_defaultBtagMMNoIsoBBTTCut_DsingleMuRunD
#def retrieveQCD (rootFile, var, sel, dataNameList):
#    name = "CORR_DDQCD_SS_DATA_" + var + "_SS_" + sel + "_" + dataNameList[-1]
#    if not rootFile.GetListOfKeys().Contains(name):
#        print "*** WARNING: QCD histo " , name , " not available"
#        return None
#    hQCD = rootFile.Get(name)
#    return hQCD

# makes an histogram by adding together all those in the input list ; inputList: names, histoList: histograms
def makeStack (stackName, histoList):
	s = THStack (stackName, stackName)
	for h in histoList:
		s.Add(h)
	return s

def makeSum (sumName, histoList):
	for i,h in enumerate(histoList):
		if i == 0: hsum = h.Clone(sumName)
		else: hsum.Add(h)
	return hsum

def setPlotStyle ():
	#Styles are: Plain Bold Video Pub Classic Default Modern
	#Modern is the default one
	#ss = gROOT.GetListOfStyles()
	#for s in ss: sys.stdout.write(s.GetName() + " ")

	gROOT.SetStyle("Modern")
	#LucaStyle = TStyle ("LucaStyle", "LucaStyle")
	#LucaStyle

# tranform an histo into a TGraphAsymmErrors, with
def makeTGraphFromHist (histo, newName):
	nPoints  = hData.GetNbinsX()
	fX       = []
	fY       = []
	feYUp    = []
	feYDown  = []
	feXRight = []
	feXLeft  = []

	for ibin in range (1, nPoints+1):
		x = hData.GetBinCenter(ibin);
		y = hData.GetBinContent(ibin);
		dxRight = hData.GetBinLowEdge(ibin+1) - hData.GetBinCenter(ibin);
		dxLeft  = hData.GetBinCenter(ibin) - hData.GetBinLowEdge(ibin);
		dyUp    = hData.GetBinErrorUp(ibin);
		dyLow   = hData.GetBinErrorLow(ibin);

		#if (!drawGrass && (int) y == 0) continue;
		fY.append(y)
		fX.append(x)
		feYUp.append(dyUp)
		feYDown.append(dyLow)
		feXRight.append(dxRight)
		feXLeft.append(dxLeft)

	afX       = array ("d", fX      )
	afY       = array ("d", fY      )
	afeYUp    = array ("d", feYUp   )
	afeYDown  = array ("d", feYDown )
	afeXRight = array ("d", feXRight)
	afeXLeft  = array ("d", feXLeft )

	gData = TGraphAsymmErrors (len(afX), afX, afY, afeXLeft, afeXRight, afeYDown, afeYUp);
	gData.SetMarkerStyle(8);
	gData.SetMarkerSize(1.);
	gData.SetMarkerColor(kBlack);
	gData.SetLineColor(kBlack);
	gData.SetName(newName)
	return gData;

# set all horizontal bar errors to 0
def removeHErrors (graph):
	for ipt in range (0, graph.GetN()):
		graph.SetPointEXlow(ipt, 0)
		graph.SetPointEXhigh(ipt, 0)

# remove all points with content = 0
def removeEmptyPoints (graph):
	zeroes = []
	for ipt in range (0, graph.GetN()):
		x = Double(0.0)
		y = Double(0.0)
		graph.GetPoint(ipt,x,y)
		if y == 0:
			zeroes.append(ipt)
	for i in reversed (zeroes):
		graph.RemovePoint(i)



def addOverFlow (histo):
	dummy = TH1F ("tempo",histo.GetTitle (),histo.GetNbinsX () + 1, histo.GetXaxis ().GetXmin (),histo.GetXaxis ().GetXmax () + histo.GetBinWidth (1))

	for iBin in range(1,histo.GetNbinsX () + 2):
			dummy.SetBinContent (iBin, histo.GetBinContent (iBin))
			dummy.SetBinError (iBin, histo.GetBinError (iBin))


	if(histo.GetDefaultSumw2()):
		   dummy.Sumw2 ()

	name = histo.GetName ()
	histo.SetName ("trash")
	if args.label:
			dummy.GetXaxis().SetTitle(args.label)
	else:
			dummy.GetXaxis().SetTitle(args.var)
	dummy.SetName (name)
	histo, dummy = dummy, histo
	return histo






def addOverAndUnderFlow ( histo):


  histo.SetBinContent(histo.GetNbinsX(),histo.GetBinContent(histo.GetNbinsX())+histo.GetBinContent(histo.GetNbinsX()+1));
  histo.SetBinContent(1,histo.GetBinContent(1)+histo.GetBinContent(0))

  if (histo.GetBinErrorOption() != TH1.kPoisson):
	histo.SetBinError(histo.GetNbinsX(),sqrt(pow(histo.GetBinError(histo.GetNbinsX()),2)+pow(histo.GetBinError(histo.GetNbinsX()+1),2)))
	histo.SetBinError(1,sqrt(pow(histo.GetBinError(1),2)+pow(histo.GetBinError(0),2)))


  histo.SetBinContent(0,0)
  histo.SetBinContent(histo.GetNbinsX()+1,0)
  if (histo.GetBinErrorOption() != TH1.kPoisson):
	  histo.SetBinError(0,0)
	  histo.SetBinError(histo.GetNbinsX()+1,0)



# NB!! need to be called BEFORE removeHErrors or cannot know bin width
def scaleGraphByBinWidth (graph):
	for ipt in range (0, graph.GetN()):
		bwh = graph.GetErrorXhigh(ipt)
		bwl = graph.GetErrorXlow(ipt)
		bw = bwl + bwh

		eyh = graph.GetErrorYhigh(ipt)
		eyl = graph.GetErrorYlow(ipt)
		x = Double(0.0)
		y = Double(0.0)
		graph.GetPoint (ipt, x, y)
		graph.SetPoint (ipt, x, y/bw)
		graph.SetPointEYlow(ipt, eyl/bw)
		graph.SetPointEYhigh(ipt, eyh/bw)


# Get the uncertainty band from BKG to be plotted in the ratio plot
def makeMCUncertaintyBand (bkgSum):
	nPoints = bkgSum.GetNbinsX()
	fX       = []
	fY       = []
	feYUp    = []
	feYDown  = []
	feXRight = []
	feXLeft  = []

	for ibin in range (1, nPoints+1):
		central = bkgSum.GetBinContent(ibin)
		if central > 0:
			fX.append      (bkgSum.GetBinCenter(ibin))
			fY.append      (1.0)
			feYUp.append   (bkgSum.GetBinErrorUp(ibin)  / central)
			feYDown.append (bkgSum.GetBinErrorLow(ibin) / central)
			feXRight.append(bkgSum.GetBinLowEdge(ibin+1) - bkgSum.GetBinCenter(ibin))
			feXLeft.append (bkgSum.GetBinCenter(ibin) - bkgSum.GetBinLowEdge(ibin))

	afX       = array ("d", fX      )
	afY       = array ("d", fY      )
	afeYUp    = array ("d", feYUp   )
	afeYDown  = array ("d", feYDown )
	afeXRight = array ("d", feXRight)
	afeXLeft  = array ("d", feXLeft )
	gBand = TGraphAsymmErrors (len(afX), afX, afY, afeXLeft, afeXRight, afeYDown, afeYUp);
	return gBand;


## do ratio of Data/MC
# horErrs : do horizontal errors
def makeDataOverMCRatioPlot (hData, hMC, newName, horErrs=False):
	nPoints = hData.GetNbinsX()
	fX       = []
	fY       = []
	feYUp    = []
	feYDown  = []
	feXRight = []
	feXLeft  = []

	for ibin in range (1, nPoints+1):
		num = hData.GetBinContent(ibin)
		den = hMC.GetBinContent(ibin)
		if den > 0:
			# Y
			fY.append(num/den)
			feYUp.append(hData.GetBinErrorUp(ibin) / den)
			feYDown.append(hData.GetBinErrorLow(ibin) / den)

			# X
			fX.append (hData.GetBinCenter(ibin))
			if horErrs:
				feXRight.append(hData.GetBinLowEdge(ibin+1) - hData.GetBinCenter(ibin))
				feXLeft.append(hData.GetBinCenter(ibin) - hData.GetBinLowEdge(ibin))
			else:
				feXLeft.append(0.0)
				feXRight.append(0.0)

	afX       = array ("d", fX      )
	afY       = array ("d", fY      )
	afeYUp    = array ("d", feYUp   )
	afeYDown  = array ("d", feYDown )
	afeXRight = array ("d", feXRight)
	afeXLeft  = array ("d", feXLeft )
	gRatio = TGraphAsymmErrors (len(afX), afX, afY, afeXLeft, afeXRight, afeYDown, afeYUp);

	gRatio.SetMarkerStyle(8);
	gRatio.SetMarkerSize(1.);
	gRatio.SetMarkerColor(kBlack);
	gRatio.SetLineColor(kBlack);
	gRatio.SetName(newName)

	return gRatio;

## find maximum of tgraph, including error
def findMaxOfGraph (graph):
	uppers = []
	for i in range (0, graph.GetN()):
		x = Double(0.0)
		y = Double(0.0)
		graph.GetPoint(i, x, y)
		uppers.append (y + graph.GetErrorYhigh(i))
	return max(uppers)

# def makeSystUpDownStack (bkgList, systList, newNamePart):
#     for i, name in bkgList:
#         scale = systList[i] # error on nominal histo
#         hUp = None   # the histograms with up/down syst
#         hDown = None #
#         if i == 0:
#             hUp = bkgList[i].Clone (newNamePart + "_up")
#             hDown = bkgList[i].Clone (newNamePart + "_up")
#             hUp.Scale (1.0 + scale)
#             hDown.Scale (1.0 - scale)
#         else:
#             hTempUp   = bkgList[i].Clone (newNamePart + "_tmp_up" + i)
#             hTempDown = bkgList[i].Clone (newNamePart + "_tmp_up" + i)
#             hTempUp.Scale (1.0 + scale)
#             hTempDown.Scale (1.0 - scale)

## remove negative bins and reset yield accordingly
## NB: must be done BEFORE bin width division
def makeNonNegativeHistos (hList):
	for h in hList:
		integral = h.Integral()
		for b in range (1, h.GetNbinsX()+1):
			if (h.GetBinContent(b) < 0):
			   h.SetBinContent (b, 0)
		integralNew = h.Integral()
		if (integralNew != integral):
			print "** INFO: removed neg bins from histo " , h.GetName()

		# print h.GetName() , integral , integralNew
		if integralNew == 0:
			h.Scale(0)
		else:
			h.Scale(integral/integralNew)


### script body ###

if __name__ == "__main__" :
	TH1.AddDirectory(0)

	titleSize = 24
	labelSize = 22
	# gStyle.SetLabelFont(43)
	# gStyle.SetTitleFont(43)

	parser = argparse.ArgumentParser(description='Command line parser of plotting options')

	#string opts
	parser.add_argument('--var', dest='var', help='variable name', default=None)
	parser.add_argument('--sel', dest='sel', help='selection name', default=None)
	parser.add_argument('--name', dest='name', help='selection name for plot', default=None)
	parser.add_argument('--dir', dest='dir', help='analysis output folder name', default="./")
	parser.add_argument('--tag', dest='tag', help='plots output folder name', default="./")
	parser.add_argument('--reg', dest='reg', help='region name', default=None)
	parser.add_argument('--title', dest='title', help='plot title', default=None)
	parser.add_argument('--label', dest='label', help='x label', default=None)
	parser.add_argument('--channel', dest='channel', help='channel = (MuTau, ETau, TauTau)', default=None)
	parser.add_argument('--siglegextratext', dest='siglegextratext', help='additional optional text to be plotted in legend after signal block', default=None)

	#bool opts
	parser.add_argument('--log',     dest='log', help='use log scale',  action='store_true', default=False)
	parser.add_argument('--no-data', dest='dodata', help='disable plotting data',  action='store_false', default=True)
	parser.add_argument('--no-sig',  dest='dosig',  help='disable plotting signal',  action='store_false', default=True)
	parser.add_argument('--no-legend',   dest='legend',   help = 'disable drawing legend',       action='store_false', default=True)
	parser.add_argument('--no-binwidth', dest='binwidth', help = 'disable scaling by bin width', action='store_false', default=True)
	parser.add_argument('--ratio',    dest='ratio', help = 'do ratio plot at the botton', action='store_true', default=False)
	parser.add_argument('--no-print', dest='printplot', help = 'no pdf output', action='store_false', default=True)
	parser.add_argument('--quit',    dest='quit', help = 'quit at the end of the script, no interactive window', action='store_true', default=False)
	parser.add_argument('--overflow',    dest='overflow', help = 'add overflow bin', action='store_true', default=False)
	parser.add_argument('--flat',    dest='flat', help = 'rebin getting flat signal', action='store_true', default=False)

	# par list opt
	parser.add_argument('--blind-range',   dest='blindrange', nargs=2, help='start and end of blinding range', default=None)

	#float opt
	parser.add_argument('--lymin', dest='lymin', type=float, help='legend min y position in pad fraction', default=None)
	parser.add_argument('--ymin', dest='ymin', type=float, help='min y range of plots', default=None)
	parser.add_argument('--ymax', dest='ymax', type=float, help='max y range of plots', default=None)
	parser.add_argument('--sigscale', dest='sigscale', type=float, help='scale to apply to all signals', default=None)
	parser.add_argument('--lumi', dest='lumi_num', type=float, help='lumi in fb-1', default=None)


	args = parser.parse_args()

	if args.quit : gROOT.SetBatch(True)

	######################### CANVASES #################################

	c1 = TCanvas ("c1", "c1", 600, 600)
	# c1.SetLeftMargin(0.15);
	# c1.SetBottomMargin(0.12);
	# c1.SetTopMargin(0.055);

	pad1 = None
	pad2 = None

	if args.ratio:
		pad1 = TPad ("pad1", "pad1", 0, 0.25, 1, 1.0)
		pad1.SetFrameLineWidth(3)
		pad1.SetLeftMargin(0.12);
		pad1.SetBottomMargin(0.02);
		pad1.SetTopMargin(0.055);

		pad1.Draw()
	else:
		pad1 = TPad ("pad1", "pad1", 0, 0.0, 1.0, 1.0)
		pad1.SetFrameLineWidth(3)
		pad1.SetLeftMargin(0.12);
		pad1.SetBottomMargin(0.12);
		pad1.SetTopMargin(0.055);
		pad1.Draw()


	pad1.cd()



	######################### PUT USER CONFIGURATION HERE ####################
	#cfgName  =  args.dir + "/mainCfg_"+args.channel+"_Legacy2018_lambdaScan.cfg"
	cfgName  =  args.dir + "/mainCfg_"+args.channel+"_Legacy2018_binOptimization.cfg"
	#cfgName  =  args.dir + "/mainCfg_"+args.channel+"_Legacy2018.cfg"
	cfg        = cfgr.ConfigReader (cfgName)
	bkgList    = cfg.readListOption("general::backgrounds")

	doQCD = True
	if not "SR" in args.reg: doQCD = False
	if not "Tau" in args.channel: doQCD = False

	if doQCD:
		bkgList.append('QCD')
	sigList = cfg.readListOption("general::signals")

	sigList = ['ggHH_bbtt11']
	#sigList = ["VBFC2V1","ggHH"]
	#sigList = ["VBFRadion600","VBFRadion900","VBFRadion2000"]

	sigNameList = []
	if args.log:
			#sigNameList = ["VBFC2V1","ggHH"]
			#sigNameList = ["VBFRadion600","VBFRadion900","VBFRadion2000"]
			#sigNameList = ["VBF HH SM (x10)"]
			sigNameList = ["gg HH SM (x"+str(int(args.sigscale))+"pb)"]
	else:
		   #sigNameList = ["VBFC2V1","ggHH (#times 0.1)"]
		   #sigNameList = ["VBFRadion600","VBFRadion900","VBFRadion2000"]
		   #sigNameList = ["VBF HH SM (x10)"]
		   sigNameList = ["gg HH SM (x"+str(int(args.sigscale))+"pb)"]

	sigColors = {}
	#sigColors["VBFC2V1"] = 2
	#sigColors["ggHH"] = kCyan
	#sigColors["VBFRadion600"]  = kBlack
	#sigColors["VBFRadion900"]  = kBlue
	#sigColors["VBFRadion2000"] = kCyan
	sigColors["VBFSM"] = kBlack

	bkgColors = {}
	#bkgColors["singleT"] = kOrange+10
	#bkgColors["EWKW"] = kGreen+3
	#bkgColors["doubleV"] = kViolet
	#bkgColors["SM"] = kBlue+1
	#bkgColors["DY"] = kGreen+1
	#bkgColors["TT"] =  kOrange+1
	#bkgColors["WJets"] = kAzure-2
	#bkgColors["other"] = kCyan+1

	# RGB/HEX colors
	col = TColor()
	bkgColors["DY"] = col.GetColor("#44BA68") #(TColor(68 ,186,104)).GetNumber() #gROOT.GetColor("#44BA68")
	bkgColors["TT"]    = col.GetColor("#F4B642") #(TColor(244,182,66 )).GetNumber() #gROOT.GetColor("#F4B642")
	bkgColors["WJets"] = col.GetColor("#41B4DB") #(TColor(65 ,180,219)).GetNumber() #gROOT.GetColor("#41B4DB")
	bkgColors["Other"] = col.GetColor("#ED635E") #(TColor(237,99 ,94 )).GetNumber() #gROOT.GetColor("#ED635E")

	bkgLineColors = {}
	bkgLineColors["DY"]    = col.GetColor("#389956")
	bkgLineColors["TT"]    = col.GetColor("#dea63c")
	bkgLineColors["WJets"] = col.GetColor("#3ca4c8")
	bkgLineColors["Other"] = col.GetColor("#d85a56")


	#if args.sigscale:
	#     for i in range(0,len(sigScale)): sigScale[i] = args.sigscale
	sigScale = [args.sigscale]

	plotTitle = ""

	if args.title:
		plotTitle = args.title
	dataList = ["data_obs"]


	if cfg.hasSection("merge"):
		for groupname in cfg.config['merge']:
			if "data" in groupname: continue
			mergelist = cfg.readListOption('merge::'+groupname)
			for x in mergelist:
				bkgList.remove(x)
			bkgList.append(groupname)





	###########################################################################
	#setPlotStyle()

	#outplotterName = findInFolder  (args.dir+"/", 'analyzedOutPlotter.root')
	outplotterName = findInFolder  (args.dir+"/", 'analyzedOutPlotter_{0}.root'.format(args.channel))


	#    if not "Tau" in args.channel:
	#           outplotterName = findInFolder  (args.dir+"/", 'outPlotter.root')

	rootFile = TFile.Open (args.dir+"/"+outplotterName)
	print(rootFile)

	binning = None
	if (args.flat): binning = flatBinning(rootFile, sigList, args.var, args.sel,args.reg)


	hSigs = retrieveHistos (rootFile, sigList, args.var, args.sel,args.reg,args.flat,binning)
	hBkgs = retrieveHistos  (rootFile, bkgList, args.var, args.sel,args.reg,args.flat,binning)

	hDatas = retrieveHistos  (rootFile, dataList, args.var, args.sel,args.reg,args.flat,binning)



	xsecRatio = 19.56
	if not args.log: xsecRatio = xsecRatio/float(10)
	#sigScale = [1. , xsecRatio*hSigs["ggHH"].GetEntries()/float(hSigs["VBFC2V1"].GetEntries())]


	doOverflow = args.overflow

	#hGGHHSM = getHisto("GGHHSM",hSigs,doOverflow)
	hGGHHSM = getHisto("ggHH_bbtt11",hSigs,doOverflow)
	#sum the signal channels in a single histo
	hSignal = hGGHHSM

	hDY = getHisto("DY",hBkgs,doOverflow)
	hTT = getHisto("TT",hBkgs,doOverflow)
	#hothers = getHisto("other", hBkgs,doOverflow)

	# the following accessing of the hitos is used when the histos are not merged all in 'other' but are merged in categories like doubleTVV, doubleTsingleV etc.
	# if we use this we must comment the line above that sets hothers
	hVVV = getHisto("tripleV",hBkgs,doOverflow)
	hWJets = getHisto("WJets",hBkgs,doOverflow)
	hVV = getHisto("doubleV", hBkgs,doOverflow)
	hTTVV = getHisto("doubleTVV",hBkgs,doOverflow)
	hTTV = getHisto("doubleTsingleV",hBkgs,doOverflow)
	hEWK = getHisto("EWK", hBkgs,doOverflow)
	hggH = getHisto("ggHTauTau", hBkgs,doOverflow)
	hVBFH = getHisto("VBFHTauTau", hBkgs,doOverflow)
	httH = getHisto("ttH", hBkgs,doOverflow)
	hVH = getHisto("VH", hBkgs,doOverflow)
	hsingleT = getHisto("singleT", hBkgs,doOverflow)

	hsingleH = httH + hVH + hVBFH + hggH
	hsingleH.SetName("singleH")
	hothers = hVVV + hVV + hTTVV + hTTV  + hEWK + hsingleT + hsingleH + hWJets
	hothers.SetName("Others")

	# full list for stack
	hBkgList = [hothers, hTT, hDY]
	# full list for yields
	# we have to subtruct the singleH to others because in this part we separate singleH channels from others in order to calculate their specific yields
	# we include singleH as well as its separated contibutions to avoid having to sum them afterwards as it would introduce a wrong propagation of the stat. error
	hothers_split = hothers - hsingleH
	hBkgList_split = [hothers_split, hTT, hDY, hWJets, hVVV, hVV, hTTVV, hTTV, hEWK, hsingleT, httH, hVH, hggH, hVBFH, hsingleH]


	hBkgNameList = ["Others", "t#bar{t}", "DY + jets"] # list for legend


	#if cfg.hasSection('pp_QCD'):
	if doQCD:
		hQCD    = getHisto ("QCD", hBkgs,doOverflow)
		hQCD.SetName("QCD")
		hBkgList.append(hQCD)
		hBkgList_split.append(hQCD)
		hBkgNameList.append("QCD")
		#bkgColors["QCD"] = kPink+5
		col = TColor()
		bkgColors["QCD"] = col.GetColor("#F29563") #(TColor(242,149,99)).GetNumber() #gROOT.GetColor("#F29563")
		bkgLineColors["QCD"] = col.GetColor("#DC885A")


	hData = getHisto("data_obs", hDatas , doOverflow).Clone("hData")

	# remove all data from blinding region before creating tgraph etc...
	if args.blindrange:
		blow = float (args.blindrange[0])
		bup = float (args.blindrange[1])
		for ibin in range (1, hData.GetNbinsX()+1):
			center = hData.GetBinCenter(ibin)
			if center > blow and center < bup:
				hData.SetBinContent(ibin, 0)


	hDataNonScaled = hData.Clone("hDataNonScaled")
	gData = makeTGraphFromHist (hData, "grData")




	# apply sig color if available
	for key in hSigs:
		hSigs[key].SetLineWidth(2)
		if doOverflow: hSigs[key] = addOverFlow(hSigs[key])
		if key in sigColors:
			thecolor = int(sigColors[key])
			hSigs[key].SetLineColor(thecolor)


	# apply bkg color if available
	for h in hBkgList:
			histoname =h.GetName()
			for key,value in bkgColors.items():
				if key in histoname:
						thecolor = int(bkgColors[key])
						h.SetFillColor(thecolor)
						h.SetFillStyle(1001)

	# apply bkg lines colors if available
	for h in hBkgList:
		histoname = h.GetName()
		for key,value in bkgLineColors.items():
			if key in histoname:
				thecolor = int(bkgLineColors[key])
				h.SetLineColor(thecolor)
				h.SetLineWidth(1)


	#################### REMOVE NEGARIVE BINS #######################
	print "** INFO: removing all negative bins from bkg histos"
	makeNonNegativeHistos (hBkgList)

	for h in hBkgList: print "Integral ", h.GetName(), " : ", h.Integral(), " - ", h.Integral(-1,-1)
	for n in hDatas: print "Integral ", hDatas[n].GetName(), " : ", hDatas[n].Integral(), " - ", hDatas[n].Integral(-1,-1)

	#################### CREATE FILES CONTAINING THE YIELDS OF THE SINGLE HISTOGRAMS #######################
	try:
		open(args.dir+"/"+args.sel+"/single_yields.txt","r")
	except IOError:
		single_yields_txt = open(args.dir+"/"+args.sel+"/single_yields.txt","a")
		single_yields_txt.write("YIELDS OF THE DIFFERENT PROCESSES - DIVIDED BY VARIABLE AND PROCESS\n")
		single_yields_txt.write("-------------------------------------------------------------------\n")
	else:
		single_yields_txt = open(args.dir+"/"+args.sel+"/single_yields.txt","a")

	single_yields_txt.write("\n-------------------------------------------------------------------\n")
	single_yields_txt.write("## "+args.var+" \n")
	error = Double(0)
	single_yields_txt.write("Signal: "+str(hSignal.IntegralAndError(-1,-1,error))+" +/- "+str(error)+"\n")
	for h in hBkgList_split:
		error = Double(0)
		single_yields_txt.write(h.GetName()+": "+str(h.IntegralAndError(-1,-1,error))+" +/- "+str(error)+"\n")
	for n in hDatas:
		error = Double(0)
		single_yields_txt.write("Data: "+str(hDatas[n].IntegralAndError(-1,-1,error))+" +/- "+str(error)+"\n")

	#################### UNDERSTAND HUGE UNDERFLUCTUATION IN 13th BIN OF BDT SCORE IN boosted CATEGORY #######################
	if "BDT" in args.var:
		if "boosted" in args.sel:
			if not "Mcut" in args.sel:
				underfluctuation = open(args.dir+"/"+args.sel+"/underfluctuation.txt","w")
				underfluctuation.write("YIELDS OF THE DIFFERENT PROCESSES INSIDE THE UNDERFLUCTUATING 13th BIN\n")
				underfluctuation.write("----------------------------------------------------------------------\n\n")
				underfluctuation.write("Signal: "+str(hSignal.GetBinContent(13))+" +/- "+str(hSignal.GetBinError(13))+"\n")
				for h in hBkgList_split:
					underfluctuation.write(h.GetName()+": "+str(h.GetBinContent(13))+" +/- "+str(h.GetBinError(13))+"\n")
				for n in hDatas:
					underfluctuation.write("Data: "+str(hDatas[n].GetBinContent(13))+" +/- "+str(hDatas[n].GetBinError(13))+"\n")

	#################### PERFORM DIVISION BY BIN WIDTH #######################
	#clones non scaled (else problems with graph ratio because I pass data evt hist)
	bkgStackNS = makeStack ("bkgStackNS", hBkgList)
	hBkgEnvelopeNS = bkgStackNS.GetStack().Last().Clone("hBkgEnvelopeNS")

	if args.binwidth:
		scaleGraphByBinWidth (gData)
		for h in hBkgList:
			h.Scale(1., "width")
		for i, name in enumerate (sigNameList):
			histo = hSigs[sigList[i]]
			histo.Scale(1., "width")


	#################### DO STACK AND PLOT #######################

	bkgStack = makeStack ("bkgStack", hBkgList)
	bkgSum = makeSum ("bkgSum", hBkgList)


	if args.log: pad1.SetLogy()


	################## TITLE AND AESTETICS ############################
	bkgStack.Draw("HIST")

	bkgStack.GetXaxis().SetTitleFont(43)
	bkgStack.GetYaxis().SetTitleFont(43)
	bkgStack.GetXaxis().SetLabelFont(43)
	bkgStack.GetYaxis().SetLabelFont(43)

	bkgStack.GetXaxis().SetTitleOffset(1.0)
	bkgStack.GetYaxis().SetTitleOffset(1.4)

	bkgStack.GetXaxis().SetTitleSize(titleSize)
	bkgStack.GetYaxis().SetTitleSize(titleSize)

	bkgStack.GetXaxis().SetLabelSize(labelSize)
	bkgStack.GetYaxis().SetLabelSize(labelSize)

	if args.label: bkgStack.GetXaxis().SetTitle (args.label)
	else: bkgStack.GetXaxis().SetTitle (args.var)

	width = ((bkgStack.GetXaxis().GetXmax() - bkgStack.GetXaxis().GetXmin())/bkgStack.GetStack().Last().GetNbinsX())
	ylabel = "Events/%.1f" % width
	if args.label:
		if "GeV" in args.label: ylabel +=" GeV"
	bkgStack.GetYaxis().SetTitle(ylabel)

	#intBkg = bkgStack.GetHistogram().Integral()
	intBkg = bkgStack.GetStack().Last().Integral()
	bkgStack.SetTitle(plotTitle)


	for key in hSigs:
		intSig = hSigs[key].Integral()
		if intSig > 0:
				hSigs[key].Scale(intBkg/intSig)

	# apply sig scale
	for i, scale in enumerate (sigScale):
		histo = hSigs[sigList[i]]
		histo.Scale(scale)

	################## LEGEND ######################################

	legmin = 0.45
	if args.lymin: legmin = args.lymin
	legminx = 0.50
	if (len(hBkgNameList) +len(hSigs)>6): legminx = 0.4
	leg = TLegend (legminx, legmin, 0.85, 0.93)
	if (len(hBkgNameList) +len(hSigs)> 6): leg.SetNColumns(2)
	leg.SetFillStyle(0)
	leg.SetBorderSize(0)
	leg.SetTextFont(43)
	leg.SetTextSize(20)

	# add element in same order as stack --> top-bottom
	for i, name in reversed(list(enumerate(hBkgNameList))):
		leg.AddEntry(hBkgList[i], name, "f")

	if args.dosig:
		#for i, name in enumerate (sigNameList):
		for i, name in reversed(list(enumerate (sigNameList))):
			histo = hSigs[sigList[i]]
			leg.AddEntry (histo, name, "l")
		# null entry to complete signal Xsection
		if args.siglegextratext:
			leg.AddEntry(None, args.siglegextratext, "")

	if args.dodata:
		leg.AddEntry(gData, "Data", "pe")


	################## Y RANGE SETTINGS ############################
	ymin = 0
	if args.log: ymin = 0.1

	maxs = []

	# bkgmax = 0
	# for h in hBkgList: bkgmax+= h.GetMaximum()
	# maxs.append(bkgmax)
	maxs.append(bkgStack.GetStack().Last().GetMaximum())

	if args.dodata:
		maxs.append(findMaxOfGraph(gData))
		#if not args.binwidth:
		#    maxs.append(hData.GetMaximum() + math.sqrt(hData.GetMaximum()))

	if args.dosig :
		for key in hSigs: maxs.append(hSigs[key].GetMaximum())

	ymax = max(maxs)

	# scale max to leave some space (~10%)
	extraspace = 0.3

	if not args.log:
		ymax += extraspace* (ymax-ymin)

	else:
		new = extraspace * (math.log(ymax, 10) - math.log(ymin, 10)) + math.log(ymax, 10)
		ymax = math.pow(10, new)


	#print "limits: " , ymin, ymax

	## override form args
	if args.ymin: ymin = args.ymin
	if args.ymax: ymax = args.ymax

	bkgStack.SetMinimum(ymin)
	bkgStack.SetMaximum(ymax)

	# interactive display
	bkgStack.Draw("HIST")
	bkgSum.SetFillColor(kGray+2);
	bkgSum.SetFillStyle(3002);
	bkgSum.Draw("e2 same")
	if args.dosig:
		for key in hSigs: hSigs[key].Draw("hist same")
	if args.dodata:
		removeHErrors(gData)
		removeEmptyPoints(gData)
		gData.Draw("P Z same") # Z: no small line at the end of error bar

	###################### OTHER TEXT ON PLOT #########################

	# extraText = "preliminary"
	# CMStext = "CMS"

	cmsTextFont     = 61  # font of the "CMS" label
	cmsTextSize   = 0.05  # font size of the "CMS" label
	extraTextFont   = 52     # for the "preliminary"
	extraTextSize   = 0.76 * cmsTextSize # for the "preliminary"



	t = gPad.GetTopMargin()
	b = gPad.GetBottomMargin()
	l = gPad.GetLeftMargin()
	r = gPad.GetRightMargin()
	#yoffset = 0.05 # fractional shift

	CMSbox       = TLatex  (l , 1 - t + 0.02, "CMS")
	extraTextBox = TLatex  (l + 0.1 , 1 - t + 0.02,"Preliminary")
	CMSbox.SetNDC()
	extraTextBox.SetNDC()
	CMSbox.SetTextSize(cmsTextSize)
	CMSbox.SetTextFont(cmsTextFont)
	CMSbox.SetTextColor(kBlack)
	CMSbox.SetTextAlign(11)
	extraTextBox.SetTextSize(extraTextSize)
	extraTextBox.SetTextFont(extraTextFont)
	extraTextBox.SetTextColor(kBlack)
	extraTextBox.SetTextAlign(11)

	x = 0
	y = 0
	#    histoWidth = histo.GetXaxis().GetBinWidth(1)*histo.GetXaxis().GetNbins()
	#    histoHeight = histo.GetMaximum()-histo.GetMinimum()


	#lumi = "%.1f fb^{-1} (13 TeV)" % args.lumi_num
	lumi = cfg.readListOption("general::lumi_fb")[0] + " fb^{-1} (13 TeV)"
	lumibox = TLatex  (1-r, 1 - t + 0.02 , lumi)
	lumibox.SetNDC()
	lumibox.SetTextAlign(31)
	lumibox.SetTextSize(extraTextSize)
	lumibox.SetTextFont(42)
	lumibox.SetTextColor(kBlack)

	if args.channel:
		if args.channel == "MuTau":
			chName = "bb #mu#tau_{h}"
		elif args.channel == "ETau":
			chName = "bb e#tau_{h}"
		elif args.channel == "TauTau":
			chName = "bb #tau_{h}#tau_{h}"
		elif args.channel == "MuMu":
			chName = "bb #mu#mu"
		else:
			print "*** Warning: channel name must be MuTau, ETau, TauTau, you wrote: " , args.channel

		if chName:
			chBox = TLatex  (l + 0.04 , 1 - t - 0.02, chName)
			chBox.SetNDC()
			chBox.SetTextSize(cmsTextSize+20)
			chBox.SetTextFont(43)
			chBox.SetTextColor(kBlack)
			chBox.SetTextAlign(13)

	CMSbox.Draw()
	extraTextBox.Draw()
	lumibox.Draw()

	if args.legend: leg.Draw()
	if chBox: chBox.Draw()


	if not args.name:
			if "baseline" in args.sel:
					selName = "baseline"
			if "1b1j" in args.sel:
					selName = "1b1j"
			if "2b0j" in args.sel:
					selName = "2b0j"
			if "0b2j" in args.sel:
					selName = "0b2j"
			if "boosted" in args.sel:
					selName = "boosted"
			if "tight" in args.sel:
				selName = "VBFtight"
			if "loose" in args.sel:
				selName = "VBFloose"
	else:
			selName = args.name

	selBox = TLatex  (l + 0.04 , 1 - t - 0.02 - 0.06, selName)
	selBox.SetNDC()
	selBox.SetTextSize(cmsTextSize+20)
	selBox.SetTextFont(43)
	selBox.SetTextColor(kBlack)
	selBox.SetTextAlign(13)
	selBox.Draw()

	###################### BLINDING BOX ###############################
	if args.blindrange:
		blow = float(args.blindrange[0])
		bup = float(args.blindrange[1])
		bBox = TBox (blow, ymin, bup, 0.93*ymax)
		bBox.SetFillStyle(3002) # NB: does not appear the same in displayed box and printed pdf!!
		bBox.SetFillColor(kGray+2) # NB: does not appear the same in displayed box and printed pdf!!
		bBox.Draw()


	###################### RATIO PLOT #################################
	if args.ratio:
		bkgStack.GetXaxis().SetTitleSize(0.00);
		bkgStack.GetXaxis().SetLabelSize(0.00);

		c1.cd()
		pad2 = TPad ("pad2", "pad2", 0, 0.0, 1, 0.2496)
		pad2.SetLeftMargin(0.12);
		pad2.SetTopMargin(0.02);
		pad2.SetBottomMargin(0.4);
		pad2.SetGridy(True);
		pad2.SetFrameLineWidth(3)
		#pad2.SetGridx(True);
		pad2.Draw()
		pad2.cd()

		grRatio = makeDataOverMCRatioPlot (hDataNonScaled, hBkgEnvelopeNS, "grRatio")
		hRatio = hDataNonScaled.Clone("hRatioAxis") # for ranges only
		hRatio = hSignal.Clone("hRatioAxis") # for ranges only
		grUncert = makeMCUncertaintyBand (bkgSum) # uncertainty band from MC, always centered at 1.0

		hRatio.GetXaxis().SetTitleFont(43) # so that size is in pixels
		hRatio.GetYaxis().SetTitleFont(43) # so that size is in pixels
		hRatio.GetXaxis().SetLabelFont(43) # so that size is in pixels
		hRatio.GetYaxis().SetLabelFont(43) # so that size is in pixels
		hRatio.GetYaxis().SetNdivisions(505)

		#hRatio.GetXaxis().SetTitle(bkgStack.GetXaxis().GetName())
		hRatio.SetTitle(plotTitle)
		hRatio.GetYaxis().SetTitle ("Data/Bkg.") #("Data/MC")
		if args.label: hRatio.GetXaxis().SetTitle (args.label)
		else: hRatio.GetXaxis().SetTitle (args.var)
		hRatio.GetXaxis().SetTitleOffset(3.9)
		hRatio.GetYaxis().SetTitleOffset(1.2)

		hRatio.GetXaxis().SetTitleSize(titleSize);
		hRatio.GetXaxis().SetLabelSize(labelSize);
		hRatio.GetYaxis().SetTitleSize(titleSize);
		hRatio.GetYaxis().SetLabelSize(labelSize);

		hRatio.GetXaxis().SetTickSize(0.10)
		hRatio.GetYaxis().SetTickSize(0.05)

		hRatio.SetStats(0)
		removeEmptyPoints (grRatio)
		# SET THE Y-AXIS OF THE RATIO PLOT BASED ON THE VALUES OF THE RATIO ITSELF -> IN THIS WAY THE PLOTS WILL ALWAYS BE MEANINGFUL
		lim_yLow = TMath.MinElement(hDataNonScaled.GetNbinsX(),grRatio.GetY())
		lim_yUp = TMath.MaxElement(hDataNonScaled.GetNbinsX(),grRatio.GetY())
		# WHEN THE VALUES OF THE RATIO ARE NOT NICE TO BE USED FOR THE PLOT WE SET THE LIMITS MANUALLY
		if lim_yLow > 1: lim_yLow = 0.75
		elif lim_yLow == 0: lim_yLow = 0.75
		if lim_yUp < 1.02: lim_yUp = 1.15
		elif lim_yUp > 2: lim_yUp = 1.35
		if "boosted" in args.sel:
			lim_yLow = 0
			lim_yUp = 3
		hRatio.SetMinimum(lim_yLow-0.05)
		hRatio.SetMaximum(lim_yUp+0.05)
		#hRatio.SetMinimum(0.5)
		#hRatio.SetMaximum(1.5)

		hRatio.Draw("axis")

		grRatio.Draw("0P same") # Z: no small limes at the end of points; 0: draw error bars even when points are outside the plot
		xmin =hRatio.GetXaxis().GetXmin()
		xmax = hRatio.GetXaxis().GetXmax()
		l1 = TLine(xmin, 1, xmax, 1)
		l1.SetLineColor(kRed)
		l1.SetLineStyle(4)
		l1.SetLineWidth(1)
		l1.Draw("same")

		grUncert.SetFillColor(kGray+2)
		grUncert.SetFillStyle(3002)
		grUncert.Draw("e2")

		pad2.RedrawAxis();
		pad2.RedrawAxis("g"); #otherwise no grid..
	###################### DISPLAY ###################################
	if not args.quit:
		pad1.Update() # necessary to show plot
		pad2.Update() # necessary to show plot
		c1.Update()
		pad1.Update()
		if pad2: pad2.Update()
		raw_input() # to prevent script from closing

	if args.printplot:
		tagch = ""
		if args.channel:
			tagch = "_" + args.channel
		#saveName = "./plotsHH2017_"+args.channel+"/"+args.tag+"/"+args.sel+"_"+args.reg+"/plot_" + args.var + "_" + args.sel +"_" + args.reg+ tagch
		saveName = args.tag+"/"+args.sel+"/plot_" + args.var + "_" + args.sel +"_" + args.reg+ tagch
		if args.log:
			saveName = saveName+"_log"
		if args.flat:
			saveName = saveName+"_flat"
		c1.SaveAs (saveName+".pdf")
		#c1.SaveAs (saveName+".png")
