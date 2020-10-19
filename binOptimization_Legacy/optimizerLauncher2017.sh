#!/bin/bash

# with this we launch in sequence all the coarse scans of the hyperparameters space

python optimizer.py --ch "TauTau" --year "2017" --var "DNNoutSM_kl_1" --sel 's2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFloose' --bins '5 50' --coarse 1 --dir '/data_CMS/cms/motta/PhDwork/HHanalysis/binOptDataset/Legacy2017/TauTau/minibinned' 2>&1 | tee ScanSteps_TauTau2017DNNoutSM_kl_1.log
sleep 20s
mv ScanSteps_TauTau2017DNNoutSM_kl_1.log ScanSteps_TauTau2017DNNoutSM_kl_1/
sleep 5m

python optimizer.py --ch "MuTau" --year "2017" --var "DNNoutSM_kl_1" --sel 's2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFloose' --bins '5 50' --coarse 1 --dir '/data_CMS/cms/motta/PhDwork/HHanalysis/binOptDataset/Legacy2017/MuTau/minibinned' # 2>&1 | tee ScanSteps_MuTau2017DNNoutSM_kl_1.log
sleep 20s
mv ScanSteps_MuTau2017DNNoutSM_kl_1.log ScanSteps_MuTau2017DNNoutSM_kl_1/
sleep 5m

python optimizer.py --ch "ETau" --year "2017" --var "DNNoutSM_kl_1" --sel 's2b0jresolvedMcut sboostedLLMcut s1b1jresolvedMcut VBFloose' --bins '5 50' --coarse 1 --dir '/data_CMS/cms/motta/PhDwork/HHanalysis/binOptDataset/Legacy2017/ETau/minibinned' 2>&1 | tee ScanSteps_ETau2017DNNoutSM_kl_1.log
sleep 20s
mv ScanSteps_ETau2017DNNoutSM_kl_1.log ScanSteps_ETau2017DNNoutSM_kl_1/
