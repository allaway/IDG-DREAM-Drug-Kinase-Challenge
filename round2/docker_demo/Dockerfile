## Start from this Docker image
FROM rocker/r-ver 
## use rocker as a base image

## Install R packages in Docker image
RUN echo "r <- getOption('repos'); r['CRAN'] <- 'http://cran.us.r-project.org'; options(repos = r);" > ~/.Rprofile
RUN Rscript -e "install.packages('readr')" 

## Make directories and copy your files into Docker image
RUN mkdir model #make directory for scripts
RUN mkdir input #make input directory
RUN mkdir output #make output directory
COPY demo_prediction.R /model/demo_prediction.R 

RUN chmod a+x /model/demo_prediction.R

## Make Docker container executable
ENTRYPOINT ["Rscript", "/model/demo_prediction.R"]