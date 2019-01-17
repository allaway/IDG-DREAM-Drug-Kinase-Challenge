FROM rocker/tidyverse

RUN Rscript -e "install.packages('devtools')"
RUN Rscript -e "install.packages('argparse')"
RUN Rscript -e "install.packages('reticulate')"
RUN Rscript -e "install.packages('rjson')"
RUN Rscript -e "install.packages('doMC')"
RUN Rscript -e "devtools::install_github('Sage-Bionetworks/challengescoring', ref = 'develop')"

RUN apt-get install -y python-pip

RUN pip install numpy scipy sklearn

COPY bin/* /usr/local/bin/
