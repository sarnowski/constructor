#!/usr/bin/env python3
import shutil

import input
import yaml
import output
import os.path
import sys
import traceback
import vm


def discover_config():
    # simple local file
    if os.path.isfile('/config.yaml'):
        with open('/config.yaml', 'r') as stream:
            return yaml.load(stream)

    # Kubernetes metadata discovery: http://kubernetes.io/docs/user-guide/downward-api/
    # mount "downwardAPI" to "/kubernetes" with "annotations" from fieldPath "metadata.annotations"
    if os.path.isfile('/kubernetes/annotations'):
        with open('/config.yaml', 'r') as stream:
            # read key=value from /kubernetes/annotations
            # file looks like:
            #      key1="value1"
            #      key2=123
            #      key3="{\"foo\": \"bar\"}"
            # replace first = with : to make valid YAML out of it

            content = stream.read()
            content.replace('=', ': ', 1)
            annotations = yaml.load(content)

            # parse yaml from key "constructorConfig"
            return yaml.load(annotations['constructorConfig'])

    raise Exception('could not discover any plans')


def construct():
    cs = vm.ConstructionSite()

    try:
        # Step 1: discover configuration file
        print('constructor > Searching for the construction plans...')
        config = discover_config()

        # Step 2: open construction site
        print('constructor > Opening a new construction site...')
        cs.open()

        # Step 3: put all inputs in place
        if 'input' in config:
            print('constructor > Loading all inputs...')
            for input_config in config['input']:
                input_handler = input.load_handler(input_config)

                # temporary storage
                os.mkdir('/input', mode=0o700)

                input_handler.pull('/input')
                # TODO make sure target is a 'good' spot so that one cannot overwrite e.g. / with a repo that contains /bin
                cs.transfer_to('/input', input_config['target'])
                input_handler.preprocess(cs)

                # cleanup temporary storage
                shutil.rmtree('/input')

        # ---- from here on, we can't trust the construction site anymore - user can now freely execute stuff in it ----

        # Step 4: install packages
        if 'packages' in config:
            packages = ' '.join(config['packages'])
            print('constructor > Installing packages: %s' % packages)
            success = cs.work('apt-get update')
            if not success:
                raise Exception('could not update package list')
            success = cs.work('apt-get install -y %s' % packages)
            if not success:
                raise Exception('could not install packages')

        # Step 5: execute all work commands
        if 'work' in config:
            print('constructor > Executing all work commands...')
            for work_config in config['work']:
                command = work_config['command']
                print('constructor > Executing: %s' % command)

                success = cs.work('cd %s && %s' % (work_config['cwd'], command))
                # TODO how to detect if the command itself is failing or the command couldn't be invoked to begin with?
                if not success:
                    raise Exception('work command failed: %s' % command)

        # Step 6: pull all outputs from the construction site
        if 'output' in config:
            print('constructor > Publishing all outputs...')
            for output_config in config['output']:
                # get the correct handler for the output type
                output_handler = output.load_handler(output_config)
                output_handler.pull('/output')  # TODO unique deterministic directory

            # Step 6.1: close the construction site (we might need a new site for post processing of outputs)
            cs.close()

            # Step 6.2: postprocess and push outputs
            for output_config in config['output']:
                output_handler = output.load_handler(output_config)
                output_handler.postprocess('/output')  # TODO unique deterministic directory
                output_handler.push('/output')

        print('constructor > Build succeeded.')

    except Exception as err:
        cs.close()

        traceback.print_exc(file=sys.stdout)
        print('constructor > Build failed: %s' % err)

        exit(1)


if __name__ == "__main__":
    construct()
