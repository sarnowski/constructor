#!/usr/bin/env python3

import vm


def construct():
    cs = vm.ConstructionSite()
    cs.open()

    print('> Updating construction site...')
    updated = cs.work("apt-get update && apt-get upgrade -y")
    if updated:
        print('> Construction site up-to-date')
    else:
        print('> Couldn\'t upgrade construction site.')

    cs.close()


if __name__ == "__main__":
    construct()
