import subprocess


def execute_streaming(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while process.poll() is None:
        output = process.stdout.read(2048).decode('utf-8')
        print(output, end='')

    if process.returncode is not 0:
        raise Exception("execution failed")