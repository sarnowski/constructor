import subprocess

import paramiko


class VirtualMachine:
    process = None
    client = None

    memory = None

    def __init__(self, memory=1024):
        self.memory = memory

    def start(self):
        all_output = []

        try:
            print('> Planning construction site...')
            self.process = subprocess.Popen(['qemu-system-x86_64',
                                             '-kernel', '/constructor/vm/vmlinuz',
                                             '-initrd', '/constructor/vm/initrd',
                                             '-hda', '/constructor/vm/disk',
                                             '-nographic',
                                             '-append', 'root=/dev/sda console=ttyS0 rw',
                                             '-net', 'user,hostfwd=tcp::22222-:22',
                                             '-net', 'nic',
                                             '-m', '{}'.format(self.memory)],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT)

            while self.process.poll() is None:
                # TODO add timeout

                output = str(self.process.stdout.readline())
                all_output.append(output)

                # just some intermediate logging
                if 'Welcome to ' in output:
                    print('> Ramping up construction site...')

                # wait until SSH server is started
                if 'Started OpenBSD Secure Shell server.' in output:

                    # create SSH connection
                    print('> Requesting access to construction site...')
                    self.client = paramiko.SSHClient()
                    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    self.client.connect('127.0.0.1', port=22222,
                                        username='root', password='constructor',
                                        timeout=10,
                                        look_for_keys=False)

                    # verify connection
                    print('> Doing first test work in the construction site...')
                    stdin, stdout, stderr = self.client.exec_command('echo "works"')
                    test_output = stdout.readlines()
                    if 'works\n' == test_output[0]:
                        print('> Construction site ramped up.')
                        return
                    else:
                        raise Exception('could not execute test command, output was: {}'.format(test_output))

            raise Exception('virtual machine failed to boot')

        except Exception as err:
            print('An error occurred while ramping up the construction site:')
            print('\n'.join(all_output))
            print(err)

    def execute(self):
        if self.client is None:
            raise Exception('access to virtual machine not established')


    def kill(self):
        if self.process is not None:
            self.process.kill()
        print('> Construction site closed.')
