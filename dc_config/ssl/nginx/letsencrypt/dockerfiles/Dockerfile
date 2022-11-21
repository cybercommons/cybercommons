ARG BASE_DOCKER_IMAGE=debian:bullseye-slim
FROM $BASE_DOCKER_IMAGE
RUN apt-get update \
 && apt-get install -y certbot

COPY ./entrypoint.sh /

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

