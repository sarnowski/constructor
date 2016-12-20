VM_TARGET=constructor/vm
DOCKER_CMD?=docker

# default action
.PHONY: all
all: constructor-image

# create a Docker image with a preinstalled build environment (Docker caches based on Dockerfile.buildenv)
.PHONY: constructor-buildenv
constructor-buildenv: buildenv/Dockerfile
	$(DOCKER_CMD) build -t constructor-buildenv buildenv

# run the VM builder within the buildenv (caches based on the build script and disk image)
$(VM_TARGET)/disk: constructor-buildenv build-vm.sh
	$(DOCKER_CMD) run --tty --privileged -v $(PWD):/work constructor-buildenv /work/build-vm.sh $(VM_TARGET)

# build the final Docker image including the VM
.PHONY: constructor-image
constructor-image: $(VM_TARGET)/disk Dockerfile
	$(DOCKER_CMD) build -t sarnowski/constructor .

.PHONY: clean
clean:
	rm -rf $(TARGET)
