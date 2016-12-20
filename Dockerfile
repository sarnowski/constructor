FROM ubuntu:16.04

# set up jail
RUN useradd --no-create-home --system -u 10000 vm && mkdir /vm

# install dependencies
RUN apt-get update \
    && apt-get install -y qemu-system-x86 \
        python3-yaml python3-paramiko python3-scp \
        git \
    && apt-get purge \
    && apt-get clean

# add own software
COPY constructor /constructor

# make it the default execution
ENTRYPOINT /constructor/construct.py