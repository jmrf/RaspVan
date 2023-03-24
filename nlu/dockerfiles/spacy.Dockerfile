FROM python:3.7-slim

# This stack-overflow question might help:
# https://stackoverflow.com/questions/59927844/is-it-possible-to-install-spacy-to-raspberry-pi-4-raspbian-buster

# To build with:
# 1. Install buildx
#   https://github.com/josemarcosrf/pyvosk-rpi/blob/main/scripts/init_multi-build.sh
#
# 2. run docker build:
  # docker buildx build --squash --push \
  #   --platform linux/arm/v7 \
  #   -t jmrf/spacy-rpi:3.3.1-cp37 \
  #   -f np_build.Dockerfile .


RUN mkdir -p /app \
    && apt update \
    && apt install -y --no-install-recommends \
       build-essential \
       libatlas-base-dev \
       gfortran \
       git \
       g++ \
       make \
       wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# TODO: If this works squash into a single command

# Update pip
RUN pip install -U pip

# # Pre-build Spacy wheels
# RUN pip install \
#     https://github.com/hoefling/so-59927844/releases/download/0.1/blis-0.4.1-cp37-cp37m-linux_armv7l.whl \
#     https://github.com/hoefling/so-59927844/releases/download/0.1/spacy-2.2.3-cp37-cp37m-linux_armv7l.whl

# Alternatively:
# 1. Build numpy's wheel
RUN git clone -b v1.21.6 --depth 1 https://github.com/numpy/numpy.git
RUN cd numpy \
    && pip install cython \
    && python setup.py bdist_wheel \
    && pip install dist/numpy-1.21.6-cp37-cp37m-linux_armv7l.whl

# 2. Build Spacy
RUN BLIS_ARCH="generic" pip install "spacy~=3.3.1" --no-binary blis

# 3. Install the rest
RUN pip install \
    pandas \
    "scikit-learn<0.24" \
    "spacy-crfsuite~=1.3.0"



