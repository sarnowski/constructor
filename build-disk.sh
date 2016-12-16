#!/bin/sh

set -e

DISK=/work/qemu-disk

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
apt update
apt install -y debootstrap qemu-utils

# install base system on disk
echo "Bootstrapping disk..."
debootstrap \
    --arch=amd64 \
    --variant=minbase \
    --include=linux-image-generic,locales,isc-dhcp-client,net-tools,openssh-server \
    xenial /mnt http://archive.ubuntu.com/ubuntu/

# setup root password for ssh access
password="constructor"
password_encrypted=$(perl -e 'print crypt($ARGV[0], "password")' $password)
chroot /mnt usermod -p "$password_encrypted" root

# enable SSH login
echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config
echo "PermitEmptyPasswords yes" >> /mnt/etc/ssh/sshd_config

# enable networking
cat > /mnt/etc/systemd/network/wired.network << "EOF"
[Match]
Name=ens3

[Network]
DHCP=ipv4
EOF

mkdir -p /mnt/etc/systemd/system/multi-user.target.wants/ /mnt/etc/systemd/system/sockets.target.wants/
ln -s /lib/systemd/system/systemd-networkd.service /mnt/etc/systemd/system/multi-user.target.wants/systemd-networkd.service
ln -s /lib/systemd/system/systemd-networkd.socket /mnt/etc/systemd/system/sockets.target.wants/systemd-networkd.socket

# extract kernel and initramfs so we can skip bootloader
echo "Extracting kernel..."
mv -v /mnt/boot/vmlinuz-* /work
mv -v /mnt/boot/initrd.img-* /work
chmod 0644 /work/vmlinuz-* /work/initrd.img-*

# package disk
echo "Finishing disk..."
umount /mnt
qemu-img convert -O qcow2 -c $DISK ${DISK}.qcow2
rm $DISK

# done
echo "Disk finished:"
ls -lh ${DISK}* /work/vmlinuz-* /work/initrd.img-*
