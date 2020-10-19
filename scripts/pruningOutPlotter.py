import os
from ROOT import *
import ROOT
import argparse
import modules.ConfigReader as cfgr
import modules.OutputManager as omng
import fnmatch
import sys
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

parser = argparse.ArgumentParser(description='Command line parser of hyperparameters scan options')
parser.add_argument('--dir', dest='dir', help='directory where analyzedOutPlotter.root to prune is', default=None)
args = parser.parse_args()

inFile = TFile.Open("{0}/analyzedOutPlotter.root".format(args.dir))
tempRoot = TFile.Open("{0}/tempOutPlotter.root".format(args.dir), "RECREATE")

for histo in inFile.GetListOfKeys():
    if "SR" in histo.GetName():
        tempRoot.Add(inFile.Get(histo.GetName()))

tempRoot.Write()
inFile.Close()
tempRoot.Close()

cfgName    = findInFolder  (args.dir+"/", 'mainCfg_*.cfg')
cfg        = cfgr.ConfigReader (args.dir + "/" + cfgName)
varList    = cfg.readListOption("general::variables")
selDefList = cfg.readListOption("general::selections") ## the selection definition
regDefList = ['SR']

tempRoot = TFile.Open("{0}/tempOutPlotter.root".format(args.dir))

ROOT.gROOT.SetBatch(True)
omngr = omng.OutputManager()
omngr.sel_def     = selDefList
omngr.sel_regions = regDefList    
omngr.variables   = varList 
omngr.readAll(tempRoot) 

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

fOut = TFile.Open("{0}/prunedOutPlotter.root".format(args.dir), "RECREATE")
omngr.saveToFile(fOut)

tempRoot.Close()
fOut.Close()
