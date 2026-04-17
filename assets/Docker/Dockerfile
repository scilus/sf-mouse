FROM scilus/scilus:2.2.0

USER root

WORKDIR /
RUN --mount=type=cache,sharing=locked,target=/var/cache/apt \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential gcc bc\
        zlib1g-dev \
        clinfo \
        git \
        libblas-dev \
        libfreetype6-dev \
        liblapack-dev \
        locales \
        imagemagick && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY maskbackgroundnoise /usr/bin/
COPY ants_generate_iterations.py /ants/bin/
RUN chmod 777 /ants/bin/ants_generate_iterations.py

COPY ANO_taxonomy_EC_V4.csv /
RUN chmod 777 /ANO_taxonomy_EC_V4.csv

COPY mouse_extract_masks.py /usr/local/bin/
RUN chmod 777 /usr/local/bin/mouse_extract_masks.py

COPY brain_extraction.py /usr/local/bin/
RUN chmod 777 /usr/local/bin/brain_extraction.py

WORKDIR /
ADD atlas.tar.gz /

ARG NUMBA_CACHE_DIR
ENV NUMBA_CACHE_DIR="/tmp"

WORKDIR /
