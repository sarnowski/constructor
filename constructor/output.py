import utils


def load_handler(plan):
    outputs = {
        "Docker": lambda: DockerOutput(plan)
    }

    handler = outputs[plan['type']]
    if handler is None:
        raise Exception('output handler for \'%s\' not available' % plan['type'])
    else:
        return handler()


class Output:
    plan = None

    def __init__(self, plan):
        self.plan = plan

    # downloads the source from the construction site into the trusted container (tmp is a directory for temporary storage)
    def pull(self, cs, tmp):
        raise Exception('output doesn\'t implement \'pull\'')

    # signals if this output requires some post processing within a new construction site
    def needs_cs_postprocessing(self):
        return False

    # does some postprocessing of the output in the trusted container before actually pushing to final destination
    # gets only executed if need_cs_postprocessing() returns True
    def postprocess(self, cs, tmp):
        raise Exception('output doesn\'t implement \'postprocess\'')

    # push the artifact to its final destination
    def push(self, tmp):
        raise Exception('output doesn\'t implement \'push\'')


class DockerOutput(Output):
    def pull(self, cs, tmp):
        cs.work('docker save %s > /docker-image' % self.plan['source'])
        cs.transfer_from('/docker-image', tmp)

    def push(self, tmp):
        utils.execute_streaming('ls -lR %s' % tmp)