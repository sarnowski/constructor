import subprocess


def execute_streaming(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    while process.poll() is None:
        output = process.stdout.read(2048).decode('utf-8')
        print(output, end='')

    if process.returncode is not 0:
        raise Exception("execution failed")


def execute_silently(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    stdout, stdin = process.communicate()
    if process.returncode != 0:
        print(stdout.decode('utf-8'))
        raise Exception("execution failed")