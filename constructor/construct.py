#!/usr/bin/env python3
import shutil

import input
from plan import discover_plan
import output
import os.path
import vm


def construct():
    # Step 1: discover configuration file
    print('constructor > Searching for the construction plans...')
    try:
        plan = discover_plan()
    except Exception as err:
        print(err)
        exit(1)

    # Step 2: open construction site
    cs = vm.ConstructionSite(plan['resources'] if 'resources' in plan else dict())
    try:

        print('constructor > Opening a new construction site...')
        cs.open()

        # ---- from here on, we can't trust the construction site anymore - user can now freely execute stuff in it ----

        # Step 3: put all inputs in place
        if 'input' in plan:
            print('constructor > Loading all inputs...')
            for input_plan in plan['input']:
                input_handler = input.load_handler(input_plan)

                # temporary storage
                os.mkdir('/input', mode=0o700)

                print('constructor >> Fetching %s (%s) into %s ...' %
                      (input_plan['source'], input_plan['type'], input_plan['target']))
                input_handler.pull('/input')
                cs.transfer_to('/input', input_plan['target'])
                input_handler.preprocess(cs)

                # cleanup temporary storage
                shutil.rmtree('/input')

        # Step 4: install packages
        if 'packages' in plan:
            packages = ' '.join(plan['packages'])
            print('constructor > Installing packages: %s' % packages)
            success = cs.work('apt-get update')
            if not success:
                raise Exception('could not update package list')
            success = cs.work('DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::="--force-confnew" --force-yes install --yes --no-install-recommends %s' % packages)
            if not success:
                raise Exception('could not install packages')

        # Step 5: execute all work commands
        if 'work' in plan:
            print('constructor > Executing all work commands...')
            for work_plan in plan['work']:
                command = work_plan['command']
                print('constructor >> Executing: %s' % command)

                # TODO execute as unprivileged user if not exlpicitly configured to be executed as root; requires shell escaping and 'su -c'
                success = cs.work('cd %s && %s' % (work_plan['cwd'], command))
                # TODO how to detect if the command itself is failing or the command couldn't be invoked to begin with?
                if not success:
                    raise Exception('work command failed: %s' % command)

        # Step 6: pull all outputs from the construction site
        if 'output' in plan:
            print('constructor > Publishing all outputs...')
            for output_plan in plan['output']:
                # get the correct handler for the output type
                output_handler = output.load_handler(output_plan)
                print('constructor >> Pulling %s (%s) from construction site...' % (output_plan['source'], output_plan['type']))
                output_handler.pull(cs, '/output')  # TODO unique deterministic directory

            # Step 6.1: close the construction site (we might need a new site for post processing of outputs)
            cs.close()
            cs = None

            # Step 6.2: postprocess and push outputs
            for output_plan in plan['output']:
                output_handler = output.load_handler(output_plan)
                if output_handler.needs_cs_postprocessing():
                    print('constructor >> Postprocessing %s (%s) in a new construction site...' % (output_plan['source'], output_plan['type']))
                    output_handler.postprocess('/output')  # TODO unique deterministic directory
                print('constructor >> Publishing %s (%s) as %s ...' % (output_plan['source'], output_plan['type'], output_plan['target']))
                output_handler.push('/output')

        print('constructor > Build succeeded.')

    except Exception as err:
        if cs is not None:
            cs.close()

        print('constructor > Build failed: %s' % err)

        if 'internal' in plan and 'returnZeroOnError' in plan['internal'] and plan['internal']['returnZeroOnError']:
            exit(0)
        else:
            exit(1)


if __name__ == "__main__":
    construct()
