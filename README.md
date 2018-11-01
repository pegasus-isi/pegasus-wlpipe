# pegasus-wlpipe
A demonstration of the Dark Energy Survey Weak Lensing Pipeline using Pegasus. The scientific codes, are bundled into a Singularity container that is used for executing each job in the workflow. 

## Prerequistes

* Download the large input DES (Dark Energy Survey) catalogs 
** http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_ngmix.fits.gz
** http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_wlinfo.fits.gz
** http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_skynet_point.fits.gz
** http://desdr-server.ncsa.illinois.edu/despublic/sva1_files/sva1_gold_r1.0_skynet_pdf.fits.gz
* Before running edit plan_dax and update SURVEY_DIR variable to point to the directory where you downloaded the above files, and gunzip'ed them.

