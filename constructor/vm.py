import subprocess


class VirtualMachine:
    process = None
    memory = None

    def __init__(self, memory=1024):
        self.memory = memory

    def start(self):
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

        all_output = []
        while self.process.poll() is None:
            output = str(self.process.stdout.readline())
            all_output.append(output)

            if 'Started OpenBSD Secure Shell server.' in output:
                return

        print('An error occurred while booting the virtual machine:')
        print('\n'.join(all_output))
        raise Exception('virtual machine failed to boot')

    def kill(self):
        if self.process is not None:
            self.process.kill()
