import utils


def load_handler(config):
    inputs = {
        "git": lambda: GitInput(config)
    }

    handler = inputs[config['type']]
    if handler is None:
        raise Exception('input handler for \'%s\' not available' % config['type'])
    else:
        return handler()


class Input:
    config = None

    def __init__(self, config):
        self.config = config

    # downloads the source to the given target directory
    def pull(self, target):
        raise Exception('input doesn\'t implement \'pull\'')

    # does some preprocessing of the input in the construction site before the actual work gets done
    def preprocess(self, cs):
        raise Exception('input doesn\'t implement \'preprocess\'')


class GitInput(Input):
    def pull(self, target):
        print('constructor >> Cloning %s ...' % self.config['source'])
        utils.execute_streaming(['git', 'clone',
                                 '--branch', self.config['head'],
                                 '--recursive',
                                 self.config['source'], target])

    def preprocess(self, cs):
        pass