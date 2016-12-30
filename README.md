<img src="head.png" align="right" height="90"/>
# Constructor

[![Build Status](https://travis-ci.org/sarnowski/constructor.svg?branch=master)](https://travis-ci.org/sarnowski/constructor)

A Docker image that can build software in a secure way, including Docker images. This is a building block for
continuous integration systems and acts as a worker to fetch inputs, builds artifacts and uploads those.

## Usage

`constructor` comes packaged as a Docker image (`sarnowski/constructor`) and is executed by passing in a *plan*.
A plan itself might require additional files that contain certain secrets to access external repositories.

### Plans

* [./plan-example.yaml](plan-example.yaml)
  * This file shows everything there is.
* [./plan-constructor.yaml](plan-constructor.yaml)
  * `constructor` itself can be build with `constructor`.
* [./plan-example-docker.yaml](plan-example-docker.yaml)
  * This example shows how to build and push Docker images.
* [./plan-constructor-kubernetes-job.yaml](plan-constructor-kubernetes-job.yaml)
  * And also in every Kubernetes cluster.

### Plan Discovery

`constructor` supports multiple ways of discovering its plan:

* **local**
  * If a file called `/plan.yaml` is found in the Docker container, it will be used. This is typically mounted into the
    container by for example `docker run -v $(pwd)/myplan.yaml:/plan.yaml sarnowski/constructor`.
* **Kubernetes**
  * If the container runs within Kubernetes, one can use the
    [Downward API](http://kubernetes.io/docs/user-guide/downward-api/). By mounting a `downwardAPI` volume with the 
    `fieldPath: metadata.annotations` to `/kubernetes/annotations/`, `constructor` will take its plan from the
    `constructionPlan` annotation. For an example, see the
    [./plan-constructor-kubernetes-job.yaml](plan-constructor-kubernetes-job.yaml).

### KVM acceleration

By default, the Docker container will run a full user-space [QEMU](http://www.qemu.org) virtual machine. This works
and is considered most secure, especially with the hardening features enabled. This leads to full (user space)
emulation of the CPU which is naturally slower than hardware supported virtualization. If you want to trade off some 
security for performance, you can use KVM by just enabling the KVM device in the container. `constructor` will
automatically pick it up if it detects it. In Docker terms, this would look like this:

    $ docker run --device /dev/kvm:/dev/kvm sarnowski/constructor

## Building

    $ make

After successful build, a Docker image called `constructor` is available. If you need to run the Docker command with
`sudo`, set up the `DOCKER_CMD` variable:

    $ DOCKER_CMD="sudo docker" make

The build will install a couple of opinionated packages by default including Java, JavaScript, Go and Python
dependencies. If these are not desired or you want more, you can specify the list of packages explicitly:

    $ make ADDITIONAL_PACKAGES=maven,golang,npm

For a reference what the default looks like, look at the head of [./build-vm.sh](./build-vm.sh).

## Process

[![Constructor BPMN diagram](constructor.png)](constructor.png)

## Dev Notes

Test the generated image:

    $ qemu-system-x86_64 \
        -kernel constructor/vm/vmlinuz \
        -initrd constructor/vm/initrd \
        -hda constructor/vm/disk \
        -nographic \
        -append "root=/dev/sda console=ttyS0 rw" \
        -m 1024 \
        -net user,hostfwd=tcp::22222-:22 -net nic

After building, one is able to do simple Python development by doing these steps:

    $ docker run -it --rm \
        --device /dev/kvm:/dev/kvm \
        --volume $(pwd):/work \
        --entrypoint bash \
        sarnowski/constructor
    # ln -s /work/plan-constructor.yaml /plan.yaml
    # cd work
    # constructor/construct.py    # as often as you want

To only build the final Docker image with all Python scripts but without rebuilding the disk image, use the
`constructor-image-only` target:

    $ make constructor-image-only

## License

Copyright (c) 2016, Tobias Sarnowski

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted,
provided that the above copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF
THIS SOFTWARE.
