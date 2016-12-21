import utils


def load_handler(plan):
    inputs = {
        "git": lambda: GitInput(plan)
    }

    handler = inputs[plan['type']]
    if handler is None:
        raise Exception('input handler for \'%s\' not available' % plan['type'])
    else:
        return handler()


class Input:
    plan = None

    def __init__(self, plan):
        self.plan = plan

    # downloads the source to the given target directory
    def pull(self, target):
        raise Exception('input doesn\'t implement \'pull\'')

    # does some preprocessing of the input in the construction site before the actual work gets done
    def preprocess(self, cs):
        raise Exception('input doesn\'t implement \'preprocess\'')


class GitInput(Input):
    def pull(self, target):
        utils.execute_streaming(['git', 'clone',
                                 '--quiet',
                                 '--branch', self.plan['head'],
                                 '--recursive',
                                 self.plan['source'], target])

    def preprocess(self, cs):
        pass