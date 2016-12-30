FROM ubuntu:16.04

# set up jail
RUN useradd --no-create-home --system -u 10000 vm && mkdir /vm

# install dependencies
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::="--force-confnew" --force-yes \
        install --yes --no-install-recommends \
        qemu-system-x86 qemu-utils python3-yaml python3-jsonschema python3-paramiko python3-scp git ca-certificates \
    && apt-get purge \
    && apt-get clean

# add own software
COPY constructor /constructor

# without this var, Docker might get output very delayed
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED "yes"

# make it the default execution
ENTRYPOINT /constructor/construct.py