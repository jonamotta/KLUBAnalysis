
# tag is the path to the directory we want to save stuff in
# THE COMPLETE PATH WILL BE: /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel
#tag=KLUBAnalysis/test_Legacy2018
tag=ThesisAnalysis/TauTau/plots_yields_Legacy2018/wo_IDSF/wo_Mcut

#selections
sel1=s0b2j
sel2=s1b1jresolved
sel3=s2b0jresolved
sel4=sboostedLL
sel5=VBFloose
#sel5=baseline


program=makeFinalYields.py

# call for the program
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel1
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel2
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel3
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel4
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel5 --last True

# python scripts/$program --dir /home/llr/cms/motta/CMSSW_10_2_16/src/$tag --sel $sel1
# python scripts/$program --dir /home/llr/cms/motta/CMSSW_10_2_16/src/$tag --sel $sel2
# python scripts/$program --dir /home/llr/cms/motta/CMSSW_10_2_16/src/$tag --sel $sel3
# python scripts/$program --dir /home/llr/cms/motta/CMSSW_10_2_16/src/$tag --sel $sel4
# python scripts/$program --dir /home/llr/cms/motta/CMSSW_10_2_16/src/$tag --sel $sel5 --last True
