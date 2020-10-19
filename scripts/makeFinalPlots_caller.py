import os

#channel = "TauTau"
#channel = "MuTau"
channel = "ETau"

year = "2016"
#year = "2017"
#year = "2018"

variable = "DNNoutSM_kl_1"

selections = ["s1b1jresolvedMcut", "s2b0jresolvedMcut", "sboostedLLMcut", "VBFloose"]

distribs = ["ConstSize", "FlatB", "FlatS", "FlatSB"]

plotter = "makeFinalPlots_binOptimization.py"

reg = "SR"

others_blind = "--quit --no-data --no-binwidth --sigscale 100"
others_blind_log = "--quit --no-data --no-binwidth --sigscale 100 --log"

for dist in distribs:
    for select in selections:
        rootdir = "/home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/binOptimization_Legacy/ScanSteps_{0}{1}{2}/".format(channel,year,variable)+dist+"/"+select+"/"

        for roots, dirs, files in os.walk(rootdir):
            for filename in [f for f in files if f == "prunedAnalyzedOutPlotter.root"]:

                os.system("mkdir "+roots+"/"+select)
                os.system("cp -a /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/index.php "+roots+"/"+select)

                os.system("python scripts/"+plotter+" --dir "+roots+ " --var "+variable+" --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} DNN score" '+others_blind+" --quit")
                os.system("python scripts/"+plotter+" --dir "+roots+ " --var "+variable+" --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} DNN score" '+others_blind_log+" --quit")
