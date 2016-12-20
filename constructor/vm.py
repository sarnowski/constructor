import subprocess

import paramiko
import scp


class ConstructionSite:
    process = None
    client = None

    resources = None

    def __init__(self, resources):
        self.resources = resources

    def open(self):
        all_output = []

        try:
            print('constructor >> Planning construction site...')
            # TODO create a copy of the disk for later reuse of the same trusted disk image
            # TODO readonly? copy-on-read?
            # TODO very long term: support other targets than x86_64 (like arm)
            qemu_config = ['qemu-system-x86_64',
                           # use our template
                           '-kernel', '/constructor/vm/vmlinuz',
                           '-initrd', '/constructor/vm/initrd',
                           '-hda', '/constructor/vm/disk',
                           # print console output to stdout
                           '-nographic',
                           '-append', 'root=/dev/sda console=ttyS0 rw',
                           # enable networking (NAT from guest to host network + SSH forwarding on localhost)
                           '-net', 'user,hostfwd=tcp::22222-:22',
                           '-net', 'nic',
                           # set up requested resources
                           '-smp', 'cpus=%s' % (self.resources['cpus'] if 'cpus' in self.resources else 1),
                           '-m', 'size=%s' % (self.resources['memory'] if 'memory' in self.resources else 1),
                           # security hardening
                           '-runas', 'vm',
                           '-chroot', '/vm',
                           #'-sandbox', 'on',  # TODO currently hangs qemu
                           ]

            self.process = subprocess.Popen(qemu_config, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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

        while not channel.exit_status_ready():
            output = channel.recv(2048)
            if output is not '':
                # TODO possible future bug when byte 2047 is in the middle of an utf-8 sequence
                print(output.decode('utf-8'), end='')

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
            print('constructor >> Construction site closed.')
