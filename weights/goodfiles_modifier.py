import os
rootdir = "/data_CMS/cms/motta/HHLegacy_SKIMS/SKIMS_Legacy2018/v2/SKIMS_8May2020/"

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        if 'good' in file:
            os.system('chmod 777 '+os.path.join(subdir, file))
            txt = open(os.path.join(subdir, file),"r")
            lines = txt.readlines()
            os.system('rm '+os.path.join(subdir, file))
            new_txt = open(os.path.join(subdir, file),"w")
            for line in lines:
                new_txt.write(line.replace("amendola/HHLegacy_2018_v2/SKIMS_8May2020/", "motta/HHLegacy_SKIMS/SKIMS_Legacy2018/v2/SKIMS_8May2020/"))
