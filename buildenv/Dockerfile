FROM ubuntu:16.04

# install dependencies
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::="--force-confnew" --force-yes \
        install --yes --no-install-recommends \
        debootstrap qemu-utils \
    && apt-get purge \
    && apt-get clean
