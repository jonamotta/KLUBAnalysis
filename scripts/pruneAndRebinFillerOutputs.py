import modules.ConfigReader as cfgr
import modules.OutputManager as omng
import argparse
import fnmatch
import os
import sys
import ROOT
import itertools

def findInFolder (folder, pattern):
    ll = []
    for ff in os.listdir(folder):
        if fnmatch.fnmatch(ff, pattern): ll.append(ff)
    if len (ll) == 0:
        print "*** WARNING: No valid file " , pattern , "found in " , folder
        return None
    if len (ll) > 1:
        print "*** WARNING: Too many files found in " , folder , ", using first one : " , ll
    return ll[0]

# prototype: ZZTo2L2Q_defaultBtagLLNoIsoBBTTCut_SSrlx_HHsvfit_deltaPhi
def retrieveHisto (rootFile, name, var, sel):
    fullName = name + '_' + sel + '_' + var
    if not rootFile.GetListOfKeys().Contains(fullName):
        print "*** WARNING: histo " , fullName , " not available"
        return None
    hFound = rootFile.Get(fullName)
    return hFound

# tag = "sig", "bkg", "DATA"
def retrieveHistos (rootFile, namelist, var, sel):
    res = {}
    for name in namelist:
        theH = retrieveHisto(rootFile, name, var, sel)
        if not theH:
            continue
        # res[name] = SampleHist.SampleHist(name=name, inputH=theH)
        res[name] = theH
    return res

###############################################################################
###############################################################################

parser = argparse.ArgumentParser(description='Command line parser of plotting options')
parser.add_argument('--outDir', dest='outDir', help='directory where to find the distributions with minibins', default="./")
parser.add_argument('--inDir', dest='inDir', help='directory where to save the pruned and rebinned histo', default="./")
parser.add_argument('--tag', dest='tag', help='specify if we want to take the NON weighted sample', default="")
parser.add_argument('--sel', dest='sel', help='specify selections we want to keep after the pruning', default="")
args = parser.parse_args()

cfgName        = findInFolder(args.outDir+"/", 'mainCfg_*.cfg')
outplotterName = findInFolder(args.inDir+args.tag+"/", 'analyzedOutPlotter.root')

cfg        = cfgr.ConfigReader (args.outDir+"/"+cfgName)
varList    = cfg.readListOption("general::variables")
selDefList = args.sel.split(" ") ## the selection definition
regDefList = ['SR']
bkgList    = cfg.readListOption("general::backgrounds")
bkgList.append("QCD") # add QCD because it is not in the cfg list, but it was calculatedFilleOuput.py step in the combine step
dataList   = cfg.readListOption("general::data")
sigList    = cfg.readListOption("general::signals")

## replace what was merged
if cfg.hasSection("merge"):
    for groupname in cfg.config['merge']: 
        mergelist = cfg.readListOption('merge::'+groupname)
        mergelistA = cfg.readOption('merge::'+groupname)
        theList = None
        if   mergelist[0] in dataList: theList = dataList
        elif mergelist[0] in sigList:  theList = sigList
        elif mergelist[0] in bkgList:  theList = bkgList
        for x in mergelist: theList.remove(x)
        theList.append(groupname)

rootfile = ROOT.TFile.Open(args.inDir+args.tag+"/"+outplotterName)
print '... opening ' , (args.inDir+args.tag+"/"+outplotterName)

ROOT.gROOT.SetBatch(True)
omngr = omng.OutputManager()
omngr.sel_def     = selDefList
omngr.sel_regions = regDefList    
omngr.variables   = varList  
# omngr.samples     = sigList + bkgList + dataList
omngr.data        = dataList
omngr.sigs        = sigList
omngr.bkgs        = bkgList
omngr.readSR(rootfile)

## always group together the data and rename them to 'data'
# omngr.groupTogether('data_obs', dataList)

if cfg.hasSection('pp_merge'):
    for groupname in cfg.config['pp_merge']:
        omngr.groupTogether(groupname, cfg.readListOption('pp_merge::'+groupname))                                                                                                                              
            
if cfg.hasSection('pp_rebin'):
    for ri in cfg.config['pp_rebin']:
        opts = cfg.readListOption('pp_rebin::'+ri)
        if len(opts) < 4:
            print '** Error: Cannot interpret your rebin instructions:', opts
            continue
        var = opts[0]
        seldef = opts[1]
        newbinning = [float(x) for x in opts[2:]]
        if not var in omngr.variables:
            print ' * var' , var , "was not plotted, won't rebin"
            continue
        if not seldef in omngr.sel_def:
            print ' * sel' , seldef , "was not used, won't rebin"
            continue            
        for reg in omngr.sel_regions:
            sel = seldef + '_' + reg
            omngr.rebin(var, sel, newbinning)

fOut = ROOT.TFile(args.outDir+"/" + 'prunedAnalyzedOutPlotter{0}.root'.format(args.tag), 'recreate')
omngr.saveToFile(fOut)

