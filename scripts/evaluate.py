#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import utils
import models
import numpy as np
import tensorflow as tf
from parse import parse_players

def extract_player_data(tag, model_inputs, players, transform=None):
    data = {}
    try:
        for input_name in model_inputs.keys():
            if input_name == 'floaty':
                data[input_name] = players[tag.lower()][input_name] + 1
            elif input_name in ('main', 'secondary', 'ranking', 'neutral', 'patience', 'clutch'):
                _value = players[tag.lower()][input_name]
                if transform and type(transform) == list and len(transform) == 2:
                    _value = (transform[0] - _value) * transform[1]
                data[input_name] = _value
    except KeyError:
        print('[-] Data unavailable for %s.' % tag)

    return data

@utils.verbose('Initial debugging')
def run_debug_initial(*args, **kwargs):
    return True

def evaluate(config, debug=False):
    if debug and not run_debug_initial(config=config):
        return  # `run_debug_initial` should return True if the program is meant to continue afterward

    root = config['project_root']
    train_params = config['train']
    Model = getattr(models, train_params['model'])
    assert isinstance(Model, type)
    model = Model(config['inputs'], config['outputs'])
    outfolder = os.path.join(root, train_params['outfolder'])

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    restore_itr = config['eval']['restore_itr']
    assert type(restore_itr) == int
    model.restore(sess, restore_itr, outfolder)

    players = parse_players(config)
    transform = config['inputs']['ranking'].get('transform', None)

    while True:
        tag0 = raw_input('tag 0: ')
        tag1 = raw_input('tag 1: ')
        tags = {0: tag0, 1: tag1}

        data0 = extract_player_data(tag0, model.inputs, players, transform)
        data1 = extract_player_data(tag1, model.inputs, players, transform)
        if not data0 or not data1:
            print('[-] Resetting...')
            continue

        data_inputs = {}
        for input_name in data0:
            _combined = np.array([data0[input_name]] + [data1[input_name]])
            _combined /= np.linalg.norm(_combined)  # TODO: this normalization weights features of larger magnitude more heavily
            data_inputs[input_name] = np.reshape(_combined, (1, _combined.size))

        input_feed = {input_tensor: data_inputs[name] for name, input_tensor in model.inputs.items()}
        winner = model.outputs['winner']
        predicted_class, output = sess.run([winner['predicted_class'], winner['output']], feed_dict=input_feed)
        confidence = output if int(predicted_class) == 1 else 1.0 - output
        print('we expect %s to win, with %.3f confidence' % (tags[int(predicted_class)], confidence))
