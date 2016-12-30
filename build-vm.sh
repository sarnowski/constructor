#!/bin/sh

set -e

if [ -z "$1" ]; then
    echo "Usage:  $0 <target> [additional packages]" >&2
    exit 1
fi

# used if not explicitly given on command call
# giving an own list overrides this
DEFAULT_ADDITIONAL_PACKAGES="apt-transport-https,ca-certificates,docker.io,build-essential,openjdk-8-jdk,maven,npm,python3-pip,python3-dev,python3-setuptools,libssl-dev,libffi-dev,golang"

WORK=/work
DISK=/qemu-disk
TARGET=${WORK}/$1

ADDITIONAL_PACKAGES=$2
[ -z "$ADDITIONAL_PACKAGES" ] && ADDITIONAL_PACKAGES=$DEFAULT_ADDITIONAL_PACKAGES
[ ! -z "$ADDITIONAL_PACKAGES" ] && ADDITIONAL_PACKAGES=",$ADDITIONAL_PACKAGES"

# set up a "disk"
echo "Creating disk..."
dd if=/dev/zero of=$DISK bs=1G count=2
mkfs.ext3 $DISK

# mount the disk
echo "Mounting disk..."
mkdir -p /mnt
for dev in $(seq 0 9); do
    [ ! -e /dev/loop$dev ] && mknod /dev/loop$dev -m0660 b 7 $dev
done
mount -o loop $DISK /mnt

# install bootstrap tooling
echo "Installing bootstrap tooling..."


# install base system on disk
echo "Bootstrapping disk..."
debootstrap \
    --arch=amd64 \
    --variant=minbase \
    --components=main,universe \
    --include=linux-image-generic,locales,isc-dhcp-client,net-tools,openssh-server${ADDITIONAL_PACKAGES} \
    xenial /mnt http://archive.ubuntu.com/ubuntu/

# set up package repositories
echo "Setting up base configuration..."
cat > /mnt/etc/apt/sources.list << "EOF"
deb http://archive.ubuntu.com/ubuntu/ xenial main restricted
deb http://archive.ubuntu.com/ubuntu/ xenial-updates main restricted
deb http://archive.ubuntu.com/ubuntu/ xenial universe
deb http://archive.ubuntu.com/ubuntu/ xenial-updates universe
deb http://archive.ubuntu.com/ubuntu/ xenial-security main restricted
deb http://archive.ubuntu.com/ubuntu/ xenial-security universe
EOF

# set up unprivileged user; can be used by builds
# explicitly do not add user to Docker group, else it would always have root access. Execute 'docker build' as root.
useradd --create-home worker

# setup root password for ssh access
echo "Enabling remote access for Docker container..."
password="constructor"
password_encrypted=$(perl -e 'print crypt($ARGV[0], "password")' $password)
chroot /mnt usermod -p "$password_encrypted" root

# enable SSH login
sed -i 's/PermitRootLogin .*/PermitRootLogin yes/g' /mnt/etc/ssh/sshd_config

# enable networking
cat > /mnt/etc/systemd/network/wired.network << "EOF"
[Match]
Name=ens4

[Network]
DHCP=ipv4
EOF

mkdir -p /mnt/etc/systemd/system/multi-user.target.wants/ /mnt/etc/systemd/system/sockets.target.wants/
ln -s /lib/systemd/system/systemd-networkd.service /mnt/etc/systemd/system/multi-user.target.wants/systemd-networkd.service
ln -s /lib/systemd/system/systemd-networkd.socket /mnt/etc/systemd/system/sockets.target.wants/systemd-networkd.socket

# clean this; gets copied from Docker container no boot
rm /mnt/etc/resolv.conf

echo "Cleaning up disk..."

# clean downloaded archives
chroot /mnt apt-get clean
# we only have virtio hardware, no need for binary firmware blobs
rm -rf mnt/lib/firmware/*

echo "Extracting kernel..."

# prepare target directory
mkdir -p $TARGET

# extract kernel and initramfs so we can skip bootloader
mv -v $(ls /mnt/boot/vmlinuz-*) $TARGET/vmlinuz
mv -v $(ls /mnt/boot/initrd.img-*) $TARGET/initrd

# package disk
echo "Finishing disk..."
umount /mnt
qemu-img convert -O qcow2 -c $DISK $TARGET/disk
rm $DISK

# finalize
chmod 0644 $TARGET/*

# done
echo "VM finished:"
ls -lh $TARGET
