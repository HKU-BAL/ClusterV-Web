# ClusterV-Web: a web application for finding HIV quasispecies from ONT sequencing data

[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause) 
[![docker](https://img.shields.io/badge/build-docker-brightgreen)](https://www.docker.com/)
[![ONT](https://img.shields.io/badge/Support-ONT-005c75)](https://nanoporetech.com/)




Contact: Ruibang Luo, Junhao Su  
Email: rbluo@cs.hku.hk, jhsu@cs.hku.hk  

----

## Introduction

ClusterV-Web is a powerful and user-friendly web application designed to accurately identify HIV quasispecies from ONT sequencing data using the [ClusterV](https://github.com/HKU-BAL/ClusterV) algorithm. By utilizing ClusterV-Web, users can input the alignment BAM file, reference FastA file, and target region BED file (which defines the specific regions of interest) for their HIV data. The application then generates comprehensive results, including the discovered quasispecies with their respective abundance, alignment information, variants (such as SNPs and INDELs), and detailed drug resistance reports.

ClusterV-Web is hosted by the BAL laboratory and can be accessed through the following website: [http://www.bio8.cs.hku.hk/ClusterVW/](http://www.bio8.cs.hku.hk/ClusterVW/). This user-friendly web application facilitates the analysis of HIV quasispecies and provides invaluable insights into the genetic diversity and drug resistance profiles of the virus.

<img src="./app/static/web.png" width = "800" alt="ClusterV web">


## Contents

* [Introduction](#introduction)
* [Installation](#installation)
  + [Option 1. Docker pre-built image](#option-1-docker-pre-built-image)
  + [Option 2. Docker Dockerfile](#option-2-docker-dockerfile)

## Installation

### Option 1. Docker pre-built image
A pre-built docker image is available [here](https://hub.docker.com/r/hkubal/clustervw). With it you can run ClusterV-Web using a single command.

```
docker run --name clustervw -d -p 8000:5000 --rm hkubal/clustervw:latest
#docker run --name clustervw -d -p 8000:5000 --rm hkubal/clustervw:v0.5 --cpus=8  --memory-swap=16g

# the website should be available at 127.0.0.1:8000, 
# or [YOUR IP]:8000, you can check your IP via `ifconfig`

# close the website by
docker ps
docker rm -f [DOCKER CONTAINER ID FOR CLUSTERVW]
```



### Option 2. Docker Dockerfile
Building a docker image.
```
# clone ClusterV-Web
git clone https://github.com/hku-bal/ClusterV-Web.git
cd ClusterV-Web

# build a docker image named hkubal/clustervw:latest
# might require docker authentication to build docker image 
docker build -f ./Dockerfile -t hkubal/clustervw:latest .

# run clustervw docker image like 
docker run --name clustervw -d -p 8000:5000 --rm hkubal/clustervw:latest
#docker run --name clustervw -d -p 8000:5000 --rm hkubal/clustervw:v0.5 --cpus=8  --memory-swap=16g

# the website should be available at your web browser via address of 127.0.0.1:8000, or YOUR IP:8000
# you can check your IP via `ifconfig`
# for security concerns, please change `this-is-a-long-secret-key` in ./app/config.py file when building the docker image before you expose your website to the public.

```
