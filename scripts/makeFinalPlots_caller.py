import os

channel = "TauTau"
#channel = "MuTau"
#channel = "ETau"

#year = "2016"
year = "2018"

#variable = "BDToutSM_kl_1"
variable = "DNNoutSM_kl_1"

# here we choose the correct selections depending on the year and channel we are considering
if year != "2016" and channel == "TauTau":
    # TauTau (only 2017/2018) selections
    selections = ["2b0j", "boosted", "VBFloose", "1b1j", "VBFtight"]
else:
    # ETau/MuTau (all years) + TauTau (2016) selections
    selections = ["2b0j", "boosted", "VBFloose", "1b1j"]

distribs = ["FlatS", "FlatB", "FlatSB", "ConstSize"]

plotter = "makeFinalPlots_binOptimization.py"

reg = "SR"  # A:SR , B:SStight , C:OSinviso, D:SSinviso, B': SSrlx

others_blind = "--quit --no-data --no-binwidth --sigscale 1"
others_blind_log = "--quit --no-data --no-binwidth --sigscale 1 --log"

for dist in distribs:
    for sel in selections:
        rootdir = "/home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/combiner_binOptimization/NumbAndDistribPostOpt/"+dist+"/"+sel+"/"
        #rootdir = "/home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/combiner_binOptimization/NumbAndDistribScanSteps/"+dist+"/"+sel+"/"

        for roots, dirs, files in os.walk(rootdir):
            for filename in [f for f in files if f == "analyzedOutPlotter.root"]:
                if sel == "2b0j": select = "s2b0jresolvedMcut"
                if sel == "1b1j": select = "s1b1jresolvedMcut"
                if sel == "boosted": select = "sboostedLLMcut"
                if sel == "VBFloose": select = "VBFlooseMcut"
                if sel == "VBFtight": select = "VBFtightMcut"

                mkdir_cmd = "mkdir "+roots+"/"+select
                os.system(mkdir_cmd)
                copy_cmd = "cp -a /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/index.php "+roots+"/"+select
                os.system(copy_cmd)

                if variable == "BDToutSM_kl_1":
                    plot1_cmd = "python scripts/"+plotter+" --dir "+roots+ " --var BDToutSM_kl_1 --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} BDT score" '+others_blind+" --quit"
                    plot2_cmd = "python scripts/"+plotter+" --dir "+roots+ " --var BDToutSM_kl_1 --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} BDT score" '+others_blind_log+" --quit"
                    os.system(plot1_cmd)
                    os.system(plot2_cmd)
                elif variable == "DNNoutSM_kl_1":
                    plot1_cmd = "python scripts/"+plotter+" --dir "+roots+ " --var DNNoutSM_kl_1 --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} DNN score" '+others_blind+" --quit"
                    plot2_cmd = "python scripts/"+plotter+" --dir "+roots+ " --var DNNoutSM_kl_1 --reg "+reg+" --sel "+select+" --channel "+channel+" --year "+year+" --lymin 0.7 --tag "+roots+' --label "HH vs t#bar{t} DNN score" '+others_blind_log+" --quit"
                    os.system(plot1_cmd)
                    os.system(plot2_cmd)
