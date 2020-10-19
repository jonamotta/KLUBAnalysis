#!/bin/bash

# with this we launch in sequence all the coarse scans of the hyperparameters space

# python binNumberAndDistributionOptimizer.py --year "2016" --ch "TauTau" --var "BDToutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_TauTau2016BDToutSM_kl_1.log
# sleep 20s
# mv NumbAndDistribScanSteps_TauTau2016BDToutSM_kl_1.log NumbAndDistribScanSteps_TauTau2016BDToutSM_kl_1/
# sleep 5m
#
# python binNumberAndDistributionOptimizer.py --year "2016" --ch "MuTau" --var "BDToutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_MuTau2016BDToutSM_kl_1.log
# sleep 20s
# mv NumbAndDistribScanSteps_MuTau2016BDToutSM_kl_1.log NumbAndDistribScanSteps_MuTau2016BDToutSM_kl_1/
# sleep 5m

python binNumberAndDistributionOptimizer.py --year "2016" --ch "ETau" --var "BDToutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_ETau2016BDToutSM_kl_1.log
sleep 20s
mv NumbAndDistribScanSteps_ETau2016BDToutSM_kl_1.log NumbAndDistribScanSteps_ETau2016BDToutSM_kl_1/
sleep 5m

# python binNumberAndDistributionOptimizer.py --year "2016" --ch "TauTau" --var "DNNoutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_TauTau2016DNNoutSM_kl_1.log
# sleep 20s
# mv NumbAndDistribScanSteps_TauTau2016DNNoutSM_kl_1.log NumbAndDistribScanSteps_TauTau2016DNNoutSM_kl_1/
# sleep 5m
#
# python binNumberAndDistributionOptimizer.py --year "2016" --ch "MuTau" --var "DNNoutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_MuTau2016DNNoutSM_kl_1.log
# sleep 20s
# mv NumbAndDistribScanSteps_MuTau2016DNNoutSM_kl_1.log NumbAndDistribScanSteps_MuTau2016DNNoutSM_kl_1/
# sleep 5m

python binNumberAndDistributionOptimizer.py --year "2016" --ch "ETau" --var "DNNoutSM_kl_1" 2>&1 | tee NumbAndDistribScanSteps_ETau2016DNNoutSM_kl_1.log
sleep 20s
mv NumbAndDistribScanSteps_ETau2016DNNoutSM_kl_1.log NumbAndDistribScanSteps_ETau2016DNNoutSM_kl_1/
