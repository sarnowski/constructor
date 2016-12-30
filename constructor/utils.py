import subprocess
import sys


def execute_streaming(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    while process.poll() is None:
        output = process.stdout.read(4096)
        sys.stdout.buffer.write(output)

    if process.returncode is not 0:
        raise Exception("execution failed")


def execute_silently(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    stdout, stdin = process.communicate()
    if process.returncode != 0:
        sys.stdout.buffer.write(stdout)
        raise Exception("execution failed")
