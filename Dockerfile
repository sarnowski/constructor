FROM ubuntu:16.04

# install dependencies
RUN apt-get update \
    && apt-get install -y qemu-system-x86 python3-paramiko \
    && apt-get purge \
    && apt-get clean

# add own software
COPY constructor /constructor

# make it the default execution
ENTRYPOINT /constructor/construct.py