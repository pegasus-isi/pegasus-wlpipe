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

This pipeline is an example of a typical gravitational weak lensing analysis. It uses publicly available Science Verification catalogs of the Dark Energy Survey (DES-SV).  
![Weak Lensing Pipeline](docs/images/WLPipeDAG-900x675.png?raw=true "Weak Lensing Pipeline")

The very first two steps of the pipeline are doTomoBinning and calDndz, which directly read from the DES-SV input catalogs.  doTomoBinning selects and sorts the objects in the input shape catalog into tomographic bins, writing out smaller fits files for each bin.  calDndz sums up the PDFs for each galaxy in the input catalog to calculate the full redshift distribution.  After doTomoBinning completes, Nc=nbtomo(nbtomo+1)/2 TreeCorr jobs are launched in parallel to calculate the two-point shear correlation functions using the fits files produced by doTomoBinning as input. 

After both doTomoBinning and calDndz are done, CosmoLike is launched to calculate the analytic covariance associated with the data vector.  It uses the redshift distributions from calDndz and the effective number density and ellipticity noise from doTomoBinning as input.  A total of Nc(2Nc+1) CosmoLike jobs are launched in parallel to calculate all the submatrices of the full covariance matrix. 

After TreeCorr and CosmoLike complete, their results are each concatenated into two separate files which, together with the redshift distributions from calDndz, serve as input for mkCosmosisFits.  This last step produces an output fits file that has all the relevant information arranged in a format supported by the CosmoSIS framework used to extract the cosmological parameters.

## Description and default values of parameters in daxgen_dessv.py

* nbtomo=3			                number of tomographic bins
* zbins"0.30,0.55,0.83,1.30"	edges of tomographic bins

* pz_startcol = "cat3:3"	starting column of PDF in input fits file for calDndz
* pz_nbins = 200		       number of bins in redshift distributions from calDndz
* pz_zlo = 0.005         lower limit of redshift distribution from calDndz
* pz_zhi = 1.8           upper limit of redshift distribution from calDndz

* thetamin = 2.0		   minimum angular separation for TreeCorr
* thetamax = 300.		  maximum angular separation for TreeCorr
* ntheta = 6		       number of angular separation bins
* bin_slop = 0.05987	treecorr parameter that controls accuracy of results,

## Generate and plan a workflow

daxgen_dessv.py is a python dax generator for this pipeline. 
 
    ./generate_dax.sh wlpipe.dax 
    Generated dax wlpipe.dax

The above created the pipeline description in the portable Pegasus format DAX.
We can now plan and submit this workflow

     ./plan_dax.sh wlpipe.dax 
     2018.11.12 09:27:25.467 PST: [INFO]  Planner invoked with following arguments --conf pegasus.properties --dax wlpipe.dax --dir /local-scratch/vahi/work/dess/pegasus-wlpipe/submit --output-dir /local-scratch/vahi/work/dess/pegasus-wlpipe/output --cleanup none --cluster label --force --sites condorpool --staging-site condorpool -v --submit  
    2018.11.12 09:27:25.996 PST: [INFO] event.pegasus.parse.dax dax.id /local-scratch/vahi/work/dess/pegasus-wlpipe/wlpipe.dax  - STARTED 
    2018.11.12 09:27:25.997 PST: [INFO] event.pegasus.parse.dax dax.id /local-scratch/vahi/work/dess/pegasus-wlpipe/wlpipe.dax  (0.001 seconds) - FINISHED 
    2018.11.12 09:27:26.000 PST: [INFO] event.pegasus.parse.dax dax.id /local-scratch/vahi/work/dess/pegasus-wlpipe/wlpipe.dax  - STARTED 
    2018.11.12 09:27:26.142 PST: [INFO] event.pegasus.add.data-dependencies dax.id wlpipe_dessv_0  - STARTED 
    2018.11.12 09:27:26.145 PST: [INFO] event.pegasus.add.data-dependencies dax.id wlpipe_dessv_0  (0.003 seconds) - FINISHED 
    2018.11.12 09:27:26.145 PST: [INFO] event.pegasus.parse.dax dax.id /local-scratch/vahi/work/dess/pegasus-wlpipe/wlpipe.dax  (0.145 seconds) - FINISHED 
    ....
    2018.11.12 09:27:26.381 PST: [INFO] event.pegasus.generate.transfer-nodes dax.id wlpipe_dessv_0  - STARTED 
    2018.11.12 09:27:26.471 PST: [INFO] event.pegasus.generate.transfer-nodes dax.id wlpipe_dessv_0  (0.09 seconds) - FINISHED 
    2018.11.12 09:27:26.473 PST: [INFO] event.pegasus.generate.workdir-nodes dax.id wlpipe_dessv_0  - STARTED 
    2018.11.12 09:27:26.480 PST: [INFO] event.pegasus.generate.workdir-nodes dax.id wlpipe_dessv_0  (0.007 seconds) - FINISHED 
    2018.11.12 09:27:26.480 PST: [INFO] event.pegasus.refinement dax.id wlpipe_dessv_0  (0.231 seconds) - FINISHED 
    2018.11.12 09:27:26.507 PST: [INFO]  Generating codes for the executable workflow 
    2018.11.12 09:27:26.507 PST: [INFO] event.pegasus.code.generation dax.id wlpipe_dessv_0  - STARTED 
    2018.11.12 09:27:26.823 PST:    
    2018.11.12 09:27:26.828 PST:   ----------------------------------------------------------------------- 
    2018.11.12 09:27:26.833 PST:   File for submitting this DAG to HTCondor           : wlpipe_dessv-0.dag.condor.sub 
    2018.11.12 09:27:26.839 PST:   Log of DAGMan debugging messages                 : wlpipe_dessv-0.dag.dagman.out 
    2018.11.12 09:27:26.844 PST:   Log of HTCondor library output                     : wlpipe_dessv-0.dag.lib.out 
    2018.11.12 09:27:26.849 PST:   Log of HTCondor library error messages             : wlpipe_dessv-0.dag.lib.err 
    2018.11.12 09:27:26.854 PST:   Log of the life of condor_dagman itself          : wlpipe_dessv-0.dag.dagman.log 
    2018.11.12 09:27:26.859 PST:    
    2018.11.12 09:27:26.865 PST:   -no_submit given, not submitting DAG to HTCondor.  You can do this with: 
    2018.11.12 09:27:26.875 PST:   ----------------------------------------------------------------------- 
    2018.11.12 09:27:26.884 PST: [INFO] event.pegasus.code.generation dax.id wlpipe_dessv_0  (0.377 seconds) - FINISHED 
    2018.11.12 09:27:27.736 PST:   Your database is compatible with Pegasus version: 4.9.0 
    2018.11.12 09:27:27.932 PST:   Submitting to condor wlpipe_dessv-0.dag.condor.sub 
    2018.11.12 09:27:28.019 PST:   Submitting job(s). 
    2018.11.12 09:27:28.024 PST:   1 job(s) submitted to cluster 1058650. 
    2018.11.12 09:27:28.029 PST:    
    2018.11.12 09:27:28.034 PST:   Your workflow has been started and is running in the base directory: 
    2018.11.12 09:27:28.040 PST:    
    2018.11.12 09:27:28.045 PST:     /local-scratch/vahi/work/dess/pegasus-wlpipe/submit/vahi/pegasus/wlpipe_dessv/run0001 
    2018.11.12 09:27:28.050 PST:    
    2018.11.12 09:27:28.055 PST:   *** To monitor the workflow you can run *** 
    2018.11.12 09:27:28.060 PST:    
    2018.11.12 09:27:28.066 PST:     pegasus-status -l /local-scratch/vahi/work/dess/pegasus-wlpipe/submit/vahi/pegasus/wlpipe_dessv/run0001 
    2018.11.12 09:27:28.071 PST:    
    2018.11.12 09:27:28.076 PST:   *** To remove your workflow run *** 
    2018.11.12 09:27:28.081 PST:    
    2018.11.12 09:27:28.086 PST:     pegasus-remove /local-scratch/vahi/work/dess/pegasus-wlpipe/submit/vahi/pegasus/wlpipe_dessv/run0001 
    2018.11.12 09:27:28.092 PST:    
    2018.11.12 09:27:28.139 PST:   Time taken to execute is 2.722 seconds 
    2018.11.12 09:27:28.139 PST: [INFO] event.pegasus.planner planner.version 4.9.0  (2.688 seconds) - FINISHED 
    
In the above output, you will see helpful pegasus commands that you can invoke to monitor and remove your workflow
