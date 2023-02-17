FROM continuumio/miniconda3:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PATH=/opt/bin:/opt/conda/bin:$PATH

# update ubuntu packages
RUN apt-get update --fix-missing && \
    yes|apt-get upgrade && \
    apt-get install -y \
    zip

RUN useradd clustervw

WORKDIR /home/clustervw

# install anaconda
RUN  conda config --add channels defaults && \
conda config --add channels bioconda && \
conda config --add channels conda-forge 


COPY clustervw_env_t.yml clustervw_env_t.yml
RUN conda env create -f clustervw_env_t.yml
ENV PATH /opt/conda/envs/clustervw_env_t/bin:$PATH
ENV CONDA_DEFAULT_ENV clustervw_env_t
RUN /bin/bash -c "source activate clustervw_env_t" && \
	pypy3 -m ensurepip && \
	pypy3 -m pip install --no-cache-dir intervaltree==3.0.2  && \
    conda install -c bioconda mosdepth -y && \
    conda install flask -y && \
    pip install flask-bootstrap && \
    pip install flask_sqlalchemy && \
    pip install flask_migrate && \
    pip install flask_wtf && \
    pip install rq && \
    pip install gunicorn && \
	echo "source activate clustervw_env_t" > ~/.bashrc

COPY . . 
RUN chmod +x boot.sh

ENV FLASK_APP run_clusterv_web.py

RUN chown -R clustervw:clustervw ./
USER clustervw

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]
