#if [ ! -d "/eos/home-c/camendol/www" ]; then
#    kinit camendol@CERN.CH
#    /opt/exp_soft/cms/t3/eos-login -username camendol
#fi

# tag is the path to the directory we want to save stuff in
# THE PATH IS FROM: /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/
#tag=ThesisAnalysis/ETau/plots_yields_Legacy2018/wo_Mcut
tag=combiner_binOptimization/OptimizedLimit/
log=(--log)

plotter=makeFinalPlots.py

#channel=TauTau
#channel=MuTau
channel=ETau
#channel=MuMu

lumi=59.97
reg=SR  # A:SR , B:SStight , C:OSinviso, D:SSinviso, B': SSrlx

sel1=s1b1jresolvedMcut
sel2=s2b0jresolvedMcut
sel3=sboostedLLMcut
#sel4=s0b2jMcut
#sel5=VBFtightMcut
sel6=VBFlooseMcut
#sel7=baselineMcut

# CREATE DIRECTORIES FOR THE SINGLE SELECTIONS
mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel1
mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel2
mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel3
#mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel4
#mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel5
mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel6
#mkdir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel7


others="--quit --ratio --sigscale 1"
others_blind="--quit --no-data --no-binwidth --sigscale 1"
others_blind_log="--quit --no-data --no-binwidth --sigscale 1 --log"

if [[ ${channel} = *"MuTau"* ]]
then
		obj1="#mu"
		obj2="#tau_{h}"
fi

if [[ ${channel} = *"ETau"* ]]
then
		obj1="e"
		obj2="#tau_{h}"
fi

if [[ ${channel} == *"TauTau"* ]]
then
		obj1="#tau_{h1}"
		obj2="#tau_{h2}"
fi

echo $obj1

#################################################################
## HH ###########################################################

# PLOTS OF SELCECTION1
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [Gev]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [Gev]"  $others --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel1 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind_log --quit

# PLOTS OF SELCECTION2
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel2 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind_log --quit

# PLOTS OF SELCECTION3
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "#eta_{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel3 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind_log --quit

# PLOTS OF SELCECTION4
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel4 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others --quit

# PLOTS OF SELCECTION5
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel5 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind_log --quit

# PLOTS OF SELCECTION6
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind --quit
python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel6 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others_blind_log --quit

# PLOTS OF SELCECTION7
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_pt --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau1_eta --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau1} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_pt --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{dau2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var dau2_eta --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "#eta^{dau2} HH"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_pt --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet1} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_pt --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "p_{T}^{bjet2} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet1_bID_deepFlavor --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet1 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bjet2_bID_deepFlavor --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "b-jet2 b-tag score"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var tauH_SVFIT_mass --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "m_{#tau#tau} SVfit HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var bH_mass --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "m_{bb} HH [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var HH_mass --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "m_{HH sys.} [GeV]"  $others --quit
#python scripts/$plotter --dir /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag --var BDToutSM_kl_1 --reg $reg --sel $sel7 --channel $channel --lymin 0.7 --tag $tag  --label "ggFHH vs t#bar{t} BDT score"  $others --quit
