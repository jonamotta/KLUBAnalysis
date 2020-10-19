import os
rootdir = "/data_CMS/cms/motta/HHLegacy_SKIMS/SKIMS_Legacy2016/v2/SKIMMED_Legacy2016_6May2020/"

for subdir, dirs, files in os.walk(rootdir):
    for file in files:
        if 'good' in file:
            os.system('chmod 777 '+os.path.join(subdir, file))
            txt = open(os.path.join(subdir, file),"r")
            lines = txt.readlines()
            os.system('rm '+os.path.join(subdir, file))
            new_txt = open(os.path.join(subdir, file),"w")
            for line in lines:
                new_txt.write(line.replace("/gwteraz/users/brivio", "/data_CMS/cms/motta/HHLegacy_SKIMS/SKIMS_Legacy2016/v2"))
            cmd = "chmod 777 "+file
