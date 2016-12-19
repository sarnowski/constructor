#!/usr/bin/env python3

import vm


def construct():
    v = vm.VirtualMachine()

    print('Booting VM...')
    v.start()

    print('VM booted, stopping...')
    v.kill()

    print('VM killed.')


if __name__ == "__main__":
    construct()
