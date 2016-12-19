FROM ubuntu:16.04

# install dependencies
RUN apt-get update \
    && apt-get install -y debootstrap qemu-utils \
    && apt-get purge \
    && apt-get clean
