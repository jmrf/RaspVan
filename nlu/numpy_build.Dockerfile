FROM python:3.7-slim

# To build with:
# 1. Install buildx
#   https://github.com/jmrf/pyvosk-rpi/blob/main/scripts/init_multi-build.sh
# 2. run docker build:
  # docker buildx build --push \
  #   --platform linux/arm/v7 \
  #   -t jmrf/numpy-rpi:1.21.6-cp37 \
  #   -f np_build.Dockerfile .

RUN mkdir -p /app \
    && apt update \
    && apt install -y --no-install-recommends \
       build-essential \
       git \
       g++ \
       make \
       wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# Some pre-liminary python deps
RUN pip install -U pip \
    && pip install Cython

RUN git clone -b v1.21.6 --depth 1 https://github.com/numpy/numpy.git
RUN cd numpy && \
    python setup.py bdist_wheel
