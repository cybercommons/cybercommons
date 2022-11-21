ARG BASE_DOCKER_IMAGE=debian:bullseye-slim
FROM $BASE_DOCKER_IMAGE
RUN apt-get update \
&& apt-get install -y \
    openssl \
&& rm -rf /var/lib/apt/lists/*

