#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_TauTau_11Oct2019_Thesis_lambdaScan_vtight/analyzedOutPlotter.root -c TauTau -o 2019_10_11_vtight_TauTau -a "GGF" &
#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_MuTau_11Oct2019_Thesis_lambdaScan_vtight/analyzedOutPlotter.root -c MuTau -o 2019_10_11_vtight_MuTau -a "GGF" &
#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_ETau_11Oct2019_Thesis_lambdaScan_vtight/analyzedOutPlotter.root -c ETau -o 2019_10_11_vtight_ETau -a "GGF" &

#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_ETau_12Sept2019_Thesis_DYLO_loosepu_mh_VBFrew/analyzedOutPlotter.root -c ETau -o 2019_10_11_VBFsig_DNN_ETau_count -a "VBF" &
#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_MuTau_12Sept2019_Thesis_DYLO_loosepu_mh_VBFrew/analyzedOutPlotter.root -c MuTau -o 2019_10_11_VBFsig_DNN_MuTau_count -a "VBF" &
#python wrapperHistos.py -f /data_CMS/cms/amendola/analysis2017/analysis_TauTau_12Sept2019_Thesis_DYLO_loosepu_mh_VBFrew/analyzedOutPlotter.root -c TauTau -o 2019_10_11_VBFsig_DNN_TauTau_count -a "VBF" &

#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_TauTau_2016.root -c TauTau -o TauTau_Legacy2016 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_MuTau_2016.root -c MuTau -o MuTau_Legacy2016 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_TauTau_2017.root -c TauTau -o TauTau_Legacy2017 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_MuTau_2017.root -c MuTau -o MuTau_Legacy2017 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_ETau_2017.root -c ETau -o ETau_Legacy2017 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_TauTau_2018.root -c TauTau -o TauTau_Legacy2018 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_MuTau_2018.root -c MuTau -o MuTau_Legacy2018 -d SMLimits_datasets/wrapped/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/SMLimits_datasets/analyzedOutPlotter_ETau_2018.root -c ETau -o ETau_Legacy2018 -d SMLimits_datasets/wrapped/ -a "GGF"

#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/DNNlimits/Legacy2016/analyzedOutPlotter_TauTau_2016.root -c TauTau -o TauTau_Legacy2016 -d DNNlimits/Legacy2016 -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/DNNlimits/Legacy2018_bin20/analyzedOutPlotter_TauTau_2018.root -c TauTau -o TauTau_Legacy2018 -d DNNlimits/Legacy2018_bin20 -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/DNNlimits/Legacy2018_bin30/analyzedOutPlotter_TauTau_2018.root -c TauTau -o TauTau_Legacy2018 -d DNNlimits/Legacy2018_bin30 -a "GGF"


#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/ETau/analyzedOutPlotter.root -c ETau -o ETau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/MuTau/analyzedOutPlotter.root -c MuTau -o MuTau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/ -a "GGF"
#python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/TauTau/analyzedOutPlotter.root -c TauTau -o TauTau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/test_benchmark/ -a "GGF"

python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/ETau/analyzedOutPlotter.root -c ETau -o ETau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/ -a "GGF"
python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/MuTau/analyzedOutPlotter.root -c MuTau -o MuTau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/ -a "GGF"
python combiner2018/wrapperHistos.py -f /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/TauTau/analyzedOutPlotter.root -c TauTau -o TauTau -d /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/20bin_benchmark/ -a "GGF"
