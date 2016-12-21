import os
import subprocess
import paramiko
import scp

import utils


class ConstructionSite:
    process = None
    client = None

    resources = None

    def __init__(self, resources):
        self.resources = resources

    def open(self):
        all_output = []

        try:
            print('constructor >> Marking territory for construction site...')

            # convert to raw for performance and resizing capabilities (also creates a copy)
            qemu_img_convert_config = ['qemu-img', 'convert',
                                       '-f', 'qcow2',
                                       '-O', 'raw',
                                       '/constructor/vm/disk', '/vm.disk']
            utils.execute_silently(qemu_img_convert_config)

            # resize disk to configured value
            qemu_img_resize_config = ['qemu-img', 'resize',
                                      '-f', 'raw',
                                      '/vm.disk',
                                      self.resources['disk'] if 'disk' in self.resources else '5G']
            utils.execute_silently(qemu_img_resize_config)

            # resize filesystem to fit disk size
            ext3_resize_config = ['resize2fs', '-f', '/vm.disk']
            utils.execute_silently(ext3_resize_config)

            # start the real VM
            print('constructor >> Preparing ground for construction site...')

            # TODO very long term: support other targets than x86_64 (like arm)
            # TODO tuning https://wiki.mikejung.biz/KVM_/_Xen
            qemu_config = ['qemu-system-x86_64',
                           # use our template
                           '-kernel', '/constructor/vm/vmlinuz',
                           '-initrd', '/constructor/vm/initrd',
                           # drive setup
                           # TODO ,cache=writeback,aio=native ?
                           '-drive', 'if=none,id=vmdrive,format=raw,file=/vm.disk',
                           '-device', 'virtio-blk-pci,drive=vmdrive',
                           # print console output to stdout
                           '-nographic',
                           '-append', 'root=/dev/vda console=ttyS0 rw',
                           # enable networking (NAT from guest to host network + SSH forwarding on localhost)
                           '-netdev', 'user,id=vmnet,hostfwd=tcp::22222-:22',
                           '-device', 'virtio-net-pci,netdev=vmnet',
                           # set up requested resources
                           '-smp', '%s' % self.resources['cpus'] if 'cpus' in self.resources else 1,
                           '-m', '%s' % self.resources['memory'] if 'memory' in self.resources else 1024,
                           # security hardening
                           '-runas', 'vm',
                           '-chroot', '/vm',
                           # '-sandbox', 'on',  # TODO currently hangs qemu
                           ]

            if os.path.exists('/dev/kvm'):
                qemu_config.extend(['-enable-kvm', '-cpu', 'host'])

            self.process = subprocess.Popen(qemu_config, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
            while self.process.poll() is None:
                # TODO add timeout

                output = self.process.stdout.readline().decode('utf-8')
                all_output.append(output)

                # just some intermediate logging
                if 'Welcome to ' in output:
                    print('constructor >> Ramping up construction site...')

                # wait until SSH server is started
                if 'Started OpenBSD Secure Shell server.' in output:

                    # create SSH connection
                    print('constructor >> Requesting access to construction site...')
                    self.client = paramiko.SSHClient()
                    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.client.connect('127.0.0.1', port=22222,
                                        username='root', password='constructor',
                                        timeout=10,
                                        look_for_keys=False)

                    # verify connection
                    print('constructor >> Doing first test work in the construction site...')
                    stdin, stdout, stderr = self.client.exec_command('echo "works"')
                    test_output = stdout.readlines()
                    if 'works\n' == test_output[0]:
                        print('constructor >> Construction site opened.')
                        return
                    else:
                        raise Exception('could not execute test command, output was: {}'.format(test_output))

            raise Exception('construction site failed to open')

        except Exception as err:
            print('An error occurred while ramping up the construction site:')
            print(''.join(all_output))
            raise err

    def work(self, command):
        if self.client is None:
            raise Exception('access to construction site not established')

        channel = self.client.get_transport().open_session()
        channel.exec_command(command)

        while True:
            if channel.recv_ready():
                print(channel.recv(4096).decode('utf-8'), end='')
            if channel.recv_stderr_ready():
                print(channel.recv_stderr(4096).decode('utf-8'), end='')
            if channel.exit_status_ready():
                break

        return channel.recv_exit_status() == 0

    def transfer_to(self, source, target):
        transport = scp.SCPClient(self.client.get_transport())
        transport.put(source, target, recursive=True, preserve_times=True)

    def transfer_from(self, source, target):
        transport = scp.SCPClient(self.client.get_transport())
        transport.get(source, target, recursive=True)

    def close(self):
        if self.process is not None:
            self.process.kill()
            try:
                os.unlink('/vm.disk')
            except:
                pass
            print('constructor >> Construction site closed.')
