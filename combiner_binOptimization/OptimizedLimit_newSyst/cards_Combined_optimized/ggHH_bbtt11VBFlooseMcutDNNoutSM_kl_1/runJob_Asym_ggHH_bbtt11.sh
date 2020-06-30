#!/bin/bash
export X509_USER_PROXY=~/.t3/proxy.cert
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc6_amd64_gcc472
cd /grid_mnt/vol__vol_U__u/llr/cms/motta/CMSSW_10_2_16/src/
eval `scram r -sh`
cd /grid_mnt/vol__vol_U__u/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/combiner_binOptimization/OptimizedLimit/cards_Combined_optimized/ggHH_bbtt11VBFlooseMcutDNNoutSM_kl_1
combine -M AsymptoticLimits /grid_mnt/vol__vol_U__u/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/combiner_binOptimization/OptimizedLimit/cards_Combined_optimized/ggHH_bbtt11VBFlooseMcutDNNoutSM_kl_1/comb.root -m 11 -n ggHH_bbtt11_forLim --run blind &> out_Asym_ggHH_bbtt11_blind.log 
combine -M AsymptoticLimits /grid_mnt/vol__vol_U__u/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/combiner_binOptimization/OptimizedLimit/cards_Combined_optimized/ggHH_bbtt11VBFlooseMcutDNNoutSM_kl_1/comb.root -m 11 -n ggHH_bbtt11_forLim_noTH --freezeNuisanceGroups theory --run blind &> out_Asym_ggHH_bbtt11_noTH_blind.log 
echo "All done for job ggHH_bbtt11" 
