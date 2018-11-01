#!/usr/bin/env python

import os
import pwd
import sys
import time
from itertools import combinations
from Pegasus.DAX3 import *

dataset="dessv"
fileprfx=dataset
omdeg=139.

nbtomo=3
zbins="0.30,0.55,0.83,1.30"

pz_startcol = "cat3:3"
pz_nbins = 200
pz_zlo = 0.005
pz_zhi = 1.8

thetamin = 2.0
thetamax = 300.
ntheta = 6
bin_slop = 0.059872647357406522
#bin_slop = 0.00

# The name of the DAX file is the first argument
if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s DAXFILE\n" % (sys.argv[0]))
        sys.exit(1)
daxfile = sys.argv[1]

USER = pwd.getpwuid(os.getuid())[0]

# Create an abstract dag
wlpipe = ADAG("wlpipe_dessv")

# Add some workflow-level metadata
wlpipe.metadata("creator", "%s@%s" % (USER, os.uname()[1]))
wlpipe.metadata("created", time.ctime())

# Input Catalogs
shape = File("shape.fits")
wlinfo = File("wlinfo.fits")
pzpoint = File("pzpoint.fits")
pdf = File("pdf.fits")

# Reference data files for comparisons
covrefnam="REF_dessv_ngmix_xi_cov_tomo.dat"
ggrefnam="REF_dessv_ngmix_xi_tomo.dat"
pzrefnam="REF_dessv_ngmix_skynet_pz.dat"

# +---------------------+
# | Tomographic Binning |
# +---------------------+
doTomoBinning = Job("doTomoBinning")
wcl=File("doTomoBinning-%s.wcl" % dataset)
neff = File("%s_neff.txt" % fileprfx)
doTomoBinning.addArguments("--input",wcl,
                           "--ntomo",str(nbtomo),"--zbins",zbins,"--ctomo","0",
                           "--cneff","1","--omdeg",str(omdeg),"--prefx",fileprfx)
doTomoBinning.uses(wcl, link=Link.INPUT)
doTomoBinning.uses(shape, link=Link.INPUT)
doTomoBinning.uses(wlinfo, link=Link.INPUT)
doTomoBinning.uses(pzpoint, link=Link.INPUT)
doTomoBinning.uses(neff, link=Link.OUTPUT, transfer=True, register=True)
ouname=[]
oufits=[]
for i in range(0,nbtomo):
    filename=fileprfx+"_gg_z"+str(i+1)+".fits"
    ouname.append(filename)
    oufits.append(File(filename))
    doTomoBinning.uses(oufits[-1], link=Link.OUTPUT, transfer=True, register=True)

wlpipe.addJob(doTomoBinning)

# +--------------------+
# | Calculate dN(z)/dz |
# +--------------------+
calDndz = Job("calDndz")
wcl=File("calDndz-%s.wcl" % dataset)
dndz1 = File("%s_dndz1.txt" % fileprfx)
dndz2 = File("%s_dndz2.txt" % fileprfx)
calDndz.addArguments("--input",wcl,"--ntomo",str(nbtomo),"--zbins",zbins,"--ctomo","1",
                     "--pzcol",str(pz_startcol),"--pznb",str(pz_nbins),
                     "--pzlo",str(pz_zlo),"--pzhi",str(pz_zhi),
                     "--out1",dndz1,"--out2",dndz2)
calDndz.uses(wcl, link=Link.INPUT)
calDndz.uses(shape, link=Link.INPUT)
calDndz.uses(wlinfo, link=Link.INPUT)
calDndz.uses(pdf, link=Link.INPUT)
calDndz.uses(dndz1, link=Link.OUTPUT, transfer=True, register=True)
calDndz.uses(dndz2, link=Link.OUTPUT, transfer=True, register=True)

wlpipe.addJob(calDndz)

# +---------------------------+
# | Create CosmoLike INI File |
# +---------------------------+

# Default CosmoLike ini file
defcosini=File("defCosmoLike.ini")
modcosini=File("%s_cosmolike.ini" % fileprfx)

mkCosmoLikeIni = Job("mkCosmoLikeIni")
mkCosmoLikeIni.addArguments("--defini",defcosini,"--modini",modcosini,"--fneff",neff,
     "--thmin",str(thetamin),"--thmax",str(thetamax),"--nth",str(ntheta),
     "--outdir","./","--prefx",fileprfx,"--survey",dataset,"--omdeg",str(omdeg),
     "--ntomosrc",str(nbtomo),"--ntomolns",str(nbtomo),"--fnzsrc",dndz1,"--fnzcls",dndz1)
mkCosmoLikeIni.uses(defcosini, link=Link.INPUT)
mkCosmoLikeIni.uses(neff, link=Link.INPUT)
mkCosmoLikeIni.uses(modcosini, link=Link.OUTPUT, transfer=True, register=True)

wlpipe.addJob(mkCosmoLikeIni)
wlpipe.depends(mkCosmoLikeIni,doTomoBinning)
wlpipe.depends(mkCosmoLikeIni,calDndz)

# +----------------------+ 
# | Calculate Covariance |
# +----------------------+
nctomo=0
for i in range(0,nbtomo):
    nctomo=nctomo+i+1
nsubmat=nctomo*(2*nctomo+1)

cljobs=[]
covnam=[]
covout=[]
for id in range(1,nsubmat+1):
    cl=Job("cosmolike")
    cljobs.append(cl)
    filename="%s_cov_Ntheta%s_Ntomo%s_%s" % (fileprfx,ntheta,nbtomo,id)
    covnam.append(filename)
    covout.append(File(filename))
    cl.addArguments(modcosini,str(id))
    cl.uses(modcosini, link=Link.INPUT)
    cl.uses(dndz1, link=Link.INPUT)
    cl.uses(covout[-1], link=Link.OUTPUT)

    wlpipe.addJob(cl)
    wlpipe.depends(cl,mkCosmoLikeIni)

# +-------------------------------+
# | Concatenate CosmoLike outputs |
# +-------------------------------+
catCosmoLikeOut=Job("cat")
covcatnam = "%s_covcat.out" % fileprfx
covcat = File(covcatnam)
catCosmoLikeOut.addArguments(' '.join(covnam))
catCosmoLikeOut.setStdout(covcat)
for f in covout:
    catCosmoLikeOut.uses(f, link=Link.INPUT)
catCosmoLikeOut.uses(covcat, link=Link.OUTPUT, transfer=True, register=True)

wlpipe.addJob(catCosmoLikeOut)
for j in cljobs:
    wlpipe.depends(catCosmoLikeOut, j)

# +----------------+
# | 2PCF: TreeCorr |
# +----------------+

# Default TreeCorr config file
tccfg=File("defTreeCorr.yaml")

# ... Calculate 2pcf for Xipm
#  .. Xipm cross correlations
ggjobs=[]
ggnam=[]
ggout=[]
for c in combinations(range(1,nbtomo+1),2):
    tc=Job("treecorr")
    ggjobs.append(tc)
    filename=fileprfx+"_gg%s%s.out" % c
    ggnam.append(filename)
    ggout.append(File(filename))
    tc.addArguments(tccfg,("file_name=%s" % ouname[c[0]-1]),
                    ("file_name2=%s" % ouname[c[1]-1]),
                    "ra_col=RA","dec_col=DEC","ra_units=degrees","dec_units=degrees",
                    "g1_col=S_1","g2_col=S_2","w_col=W","flip_g1=false","flip_g2=false",
                    ("min_sep=%s" % thetamin),("max_sep=%s" % thetamax),
                    ("nbins=%s" % ntheta),("bin_slop=%s" % bin_slop),
                    ("gg_file_name=%s" % filename))
    tc.uses(tccfg, link=Link.INPUT)
    tc.uses(oufits[c[0]-1], link=Link.INPUT)
    tc.uses(oufits[c[1]-1], link=Link.INPUT)
    tc.uses(ggout[-1], link=Link.OUTPUT)

    wlpipe.addJob(tc)
    wlpipe.depends(tc, doTomoBinning)

#  .. Xipm auto correlations
ggnam2=[]
ggout2=[]
for i in range(1,nbtomo+1):
    tc=Job("treecorr")
    ggjobs.append(tc)
    filename=fileprfx+"_gg%s%s.out" % (i,i)
    ggnam2.append(filename)
    ggout2.append(File(filename))
    tc.addArguments(tccfg,("file_name=%s" % ouname[i-1]),
                    "ra_col=RA","dec_col=DEC","ra_units=degrees","dec_units=degrees",
                    "g1_col=S_1","g2_col=S_2","w_col=W","flip_g1=false","flip_g2=false",
                    ("min_sep=%s" % thetamin),("max_sep=%s" % thetamax),
                    ("nbins=%s" % ntheta),("bin_slop=%s" % bin_slop),
                    ("gg_file_name=%s" % filename))
    tc.uses(tccfg, link=Link.INPUT)
    tc.uses(oufits[i-1], link=Link.INPUT)
    tc.uses(ggout2[-1], link=Link.OUTPUT)

    wlpipe.addJob(tc)
    wlpipe.depends(tc, doTomoBinning)

# ... Calculate 2pcf for the correction factor
#  .. correction factor cross correlations
kkjobs=[]
kknam=[]
kkout=[]
for c in combinations(range(1,nbtomo+1),2):
    tc=Job("treecorr")
    kkjobs.append(tc)
    filename=fileprfx+"_kk%s%s.out" % c
    kknam.append(filename)
    kkout.append(File(filename))
    tc.addArguments(tccfg,("file_name=%s" % ouname[c[0]-1]),
                    ("file_name2=%s" % ouname[c[1]-1]),
                    "ra_col=RA","dec_col=DEC","ra_units=degrees","dec_units=degrees",
                    "k_col=SCORR","w_col=W",("min_sep=%s" % thetamin),
                    ("max_sep=%s" % thetamax),("nbins=%s" % ntheta),
                    ("bin_slop=%s" % bin_slop),("kk_file_name=%s" % filename))
    tc.uses(tccfg, link=Link.INPUT)
    tc.uses(oufits[c[0]-1], link=Link.INPUT)
    tc.uses(oufits[c[1]-1], link=Link.INPUT)
    tc.uses(kkout[-1], link=Link.OUTPUT)

    wlpipe.addJob(tc)
    wlpipe.depends(tc, doTomoBinning)

#  .. correction factor auto correlations
kknam2=[]
kkout2=[]
for i in range(1,nbtomo+1):
    tc=Job("treecorr")
    kkjobs.append(tc)
    filename=fileprfx+"_kk%s%s.out" % (i,i)
    kknam2.append(filename)
    kkout2.append(File(filename))
    tc.addArguments(tccfg,("file_name=%s" % ouname[i-1]),
                    "ra_col=RA","dec_col=DEC","ra_units=degrees","dec_units=degrees",
                    "k_col=SCORR","w_col=W",("min_sep=%s" % thetamin),
                    ("max_sep=%s" % thetamax),("nbins=%s" % ntheta),
                    ("bin_slop=%s" % bin_slop),("kk_file_name=%s" % filename))
    tc.uses(tccfg, link=Link.INPUT)
    tc.uses(oufits[i-1], link=Link.INPUT)
    tc.uses(kkout2[-1], link=Link.OUTPUT)

    wlpipe.addJob(tc)
    wlpipe.depends(tc, doTomoBinning)

# ... Merge the cross correlation and auto correlation results into a single list with
#     the sequence 11, 12, 13, ..., 22, 23, ..
i=0
for j in range(0,nbtomo):
     ggnam.insert(i,ggnam2[j])
     kknam.insert(i,kknam2[j])
     ggout.insert(i,ggout2[j])
     kkout.insert(i,kkout2[j])
     i=i+nbtomo-j

# +------------------------------+
# | Concatenate TreeCorr outputs |
# +------------------------------+
catjobs=[]

# ... Now concatenate the results for gg into single output file
catFilesInList = Job("catFilesInList")
catjobs.append(catFilesInList)
ggcat = File("%s_ggcat.out" % fileprfx)
catFilesInList.addArguments("--filelist",','.join(ggnam),"--outfile",ggcat,
                            "--nskip","1","--header","True")
for f in ggout:
    catFilesInList.uses(f, link=Link.INPUT)
catFilesInList.uses(ggcat, link=Link.OUTPUT, transfer=True, register=True)
wlpipe.addJob(catFilesInList)
for j in ggjobs:
    wlpipe.depends(catFilesInList, j)

# ... Now concatenate the results for kk into single output file
catFilesInList = Job("catFilesInList")
catjobs.append(catFilesInList)
kkcat = File("%s_kkcat.out" % fileprfx)
catFilesInList.addArguments("--filelist",','.join(kknam),"--outfile",kkcat,
                            "--nskip","1","--header","True")
for f in kkout:
    catFilesInList.uses(f, link=Link.INPUT)
catFilesInList.uses(kkcat, link=Link.OUTPUT, transfer=True, register=True)

wlpipe.addJob(catFilesInList)
for j in kkjobs:
    wlpipe.depends(catFilesInList, j)

#
# - Create the Cosmosis input files and plot their contents
#
fitnames=["","_covg","_covng"]
covnames=[covrefnam,covcatnam,covcatnam]
covtypes=["1","0","0"]
gastruth=["False","True","False"]
ggrefopt=[ggrefnam,"None","None"]
pzrefopt=[pzrefnam,"None","None"]

for ift in range(0,3):

    newprefix=fileprfx+fitnames[ift]
    
    # +------------------------------------+
    # | Create the input file for Cosmosis |
    # +------------------------------------+
    mkCosmosisFits = Job("mkCosmosisFits")
    covmat=File(covnames[ift])
    cosmofits=File("%s.fits" % newprefix)
    mkCosmosisFits.addArguments("--cvfile",covmat,"--ggfile",ggcat,"--kkfile",kkcat,
                            "--nzfile",dndz2,"--oufits",cosmofits,"--ntomo",str(nbtomo),
                            "--pznb",str(pz_nbins),"--ntheta",str(ntheta),
                            "--covtyp",covtypes[ift],"--gausscov",gastruth[ift])
    mkCosmosisFits.uses(covmat,link=Link.INPUT)
    mkCosmosisFits.uses(ggcat, link=Link.INPUT)
    mkCosmosisFits.uses(kkcat, link=Link.INPUT)
    mkCosmosisFits.uses(dndz2, link=Link.INPUT)
    mkCosmosisFits.uses(cosmofits, link=Link.OUTPUT, transfer=True, register=True)

    wlpipe.addJob(mkCosmosisFits)
    for j in catjobs:
        wlpipe.depends(mkCosmosisFits,j)
    wlpipe.depends(mkCosmosisFits,calDndz)
    wlpipe.depends(mkCosmosisFits,catCosmoLikeOut)

    # +----------------------------------+
    # | Plot data in Cosmosis input file |
    # +----------------------------------+
    plotCosmosisFits = Job("plotCosmosisFits")
    plotCosmosisFits.addArguments("--infit",cosmofits,"--ggref",ggrefopt[ift],
                      "--pzref",pzrefopt[ift],"--pztyp","1","--prefx",("%s_" % newprefix))
    plotCosmosisFits.uses(cosmofits,link=Link.INPUT)
    if ggrefopt[ift]!="None": plotCosmosisFits.uses(File(ggrefopt[ift]),link=Link.INPUT)
    if pzrefopt[ift]!="None": plotCosmosisFits.uses(File(pzrefopt[ift]),link=Link.INPUT)
    plotCosmosisFits.uses(File("%s_cov.png"  % newprefix), link=Link.OUTPUT, transfer=True, register=True)
    plotCosmosisFits.uses(File("%s_xipm.png" % newprefix), link=Link.OUTPUT, transfer=True, register=True)
    plotCosmosisFits.uses(File("%s_pz.png"   % newprefix), link=Link.OUTPUT, transfer=True, register=True)

    wlpipe.addJob(plotCosmosisFits)
    wlpipe.depends(plotCosmosisFits,mkCosmosisFits)

f = open(daxfile, "w")
wlpipe.writeXML(f)
f.close()
print "Generated dax %s" %daxfile
