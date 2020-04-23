
# tag is the path to the directory we want to save stuff in
# THE COMPLETE PATH WILL BE: /home/llr/cms/motta/CMSSW_10_2_16/src/KLUBAnalysis/$tag/$sel
tag=ThesisAnalysis/ETau/plots_yields_Legacy2018/w_Mcut

#selections
sel1=s0b2j
sel2=s1b1jresolvedMcut
sel3=s2b0jresolvedMcut
sel4=sboostedLLMcut
sel5=VBFlooseMcut


program=makeFinalYields.py

# call for the program
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel1
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel2
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel3
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel4
python scripts/$program --dir /data_CMS/cms/motta/$tag --sel $sel5 --last True
