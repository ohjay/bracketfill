#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import models

def run_debug_initial(*args, **kwargs):
    return True

def train(config, debug=False):
    if debug and not run_debug_initial(config=config):
        return  # `run_debug_initial` should return True if the program is meant to continue afterward

    train_params = config['train']
    model = getattr(models, train_params['model'])
    assert isinstance(model, type)
