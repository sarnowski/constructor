#!/bin/sh

docker=docker
[ ! -z "$DOCKER_SUDO" ] && docker="sudo docker"

# reset path
cd $(dirname $0)

# build qemu disk
$docker run --tty --privileged -v $(pwd):/work ubuntu:16.04 /work/build-disk.sh

# build Docker image
