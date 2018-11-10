# pegasus-wlpipe

A demonstration of the Dark Energy Survey Weak Lensing Pipeline using Pegasus. The scientific codes, are bundled into a Singularity container that is used for executing each job in the workflow.

This example is setup to run in a local Condor pool, that has a shared filesystem between the worker nodes. The shared filesystem is used as the staging site. Also it assumes that the input directory on the submit node is accessible to the condorpool.

## Prerequistes

* Download the large input DES (Dark Energy Survey) catalogs 
  * http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_ngmix.fits.gz
  * http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_wlinfo.fits.gz
  * http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_skynet_point.fits.gz
  * http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_skynet_pdf.fits.gz
* Before running edit plan_dax and update SURVEY_DIR variable to point to the directory where you downloaded the above files, and gunzip'ed them.

## Description of pipeline steps in demo

This pipeline is an example of a typical gravitational weak lensing analysis. It uses publicly available Science Verification catalogs of the Dark Energy Survey (DES-SV).  The very first two steps of the pipeline are doTomoBinning and calDndz, which directly read from the DES-SV input catalogs.  doTomoBinning selects and sorts the objects in the input shape catalog into tomographic bins, writing out smaller fits files for each bin.  calDndz sums up the PDFs for each galaxy in the input catalog to calculate the full redshift distribution.  After doTomoBinning completes, nctomo=nbtomo(nbtomo+1)/2 TreeCorr jobs are launched in parallel to calculate the two-point shear correlation functions using the fits files produced by doTomoBinning as input. After both doTomoBinning and calDndz are done, CosmoLike is launched to calculate the analytic covariance associated with the data vector.  It uses the redshift distributions from calDndz and the effective number density and ellipticity noise from doTomoBinning as input.  A total of Nc(2Nc+1) CosmoLike jobs are launched in parallel to calculate all the submatrices of the full covariance matrix.  After TreeCorr and CosmoLike complete, their results are each concatenated into two separate files which, together with the redshift distributions from calDndz, serve as input for mkCosmosisFits.  This last step produces an output fits file that has all the relevant information arranged in a format supported by the CosmoSIS framework used to extract the cosmological parameters.

## Description and default values of parameters in daxgen_dessv.py

nbtomo=3			                number of tomographic bins
zbins"0.30,0.55,0.83,1.30"	edges of tomographic bins

pz_startcol = "cat3:3"	starting column of PDF in input fits file for calDndz
pz_nbins = 200		       number of bins in redshift distributions from calDndz
pz_zlo = 0.005         lower limit of redshift distribution from calDndz
pz_zhi = 1.8           upper limit of redshift distribution from calDndz

thetamin = 2.0		   minimum angular separation for TreeCorr
thetamax = 300.		  maximum angular separation for TreeCorr
ntheta = 6		       number of angular separation bins
bin_slop = 0.05987	treecorr parameter that controls accuracy of results,

## Generate and plan a workflow

daxgen_dessv.py is a python dax generator for this pipeline. 
 
    ./generate_dax.sh wlpipe.dax
