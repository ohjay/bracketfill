#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import yaml
import utils
import models
import tensorflow as tf
import numpy as np
from parse import parse_sets, parse_players

"""
train.py
Graph spec + Post-processed data in memory -> Trained, saved model
"""

def load_data(model_inputs, model_labels, config):
    sets = parse_sets(config)
    players = parse_players(config)
    data_inputs = {input_name: [] for input_name in model_inputs.keys()}
    data_labels = {label_name: [] for label_name in model_labels.keys()}
    for _set in sets:
        tag0 = _set['tag0'].lower()
        tag1 = _set['tag1'].lower()
        for input_name in model_inputs.keys():
            if input_name == 'floaty':
                data_inputs['floaty'].append([players[tag0]['floaty'] + 1, players[tag1]['floaty'] + 1])
                data_inputs['floaty'].append([players[tag1]['floaty'] + 1, players[tag0]['floaty'] + 1])
            elif input_name in ('main', 'secondary', 'ranking', 'neutral', 'patience', 'clutch'):
                _value0 = players[tag0][input_name]
                _value1 = players[tag1][input_name]
                transform = config['inputs'][input_name].get('transform', None)
                if transform:
                    if type(transform) == list and len(transform) == 2:
                        _value0 = (transform[0] - _value0) * transform[1]
                        _value1 = (transform[0] - _value1) * transform[1]
                data_inputs[input_name].append([_value0, _value1])
                data_inputs[input_name].append([_value1, _value0])
            else:
                print('[-] Unrecognized input name: %s.' % input_name)
        for label_name in model_labels.keys():
            if label_name == 'winner':
                data_labels['winner'].append(_set['winner'])
                data_labels['winner'].append(1 - _set['winner'])
            else:
                print('[-] Unrecognized label name: %s.' % label_name)

    for input_name, data in data_inputs.items():
        data = np.array(data)
        row_norms = np.linalg.norm(data, axis=1)
        data_inputs[input_name] = data / row_norms[:, None]  # same as `sklearn.preprocessing.normalize`
    for label_name, data in data_labels.items():
        data_labels[label_name] = np.array(data)

    return data_inputs, data_labels

def index_generator(batch_size, data_size):
    while True:
        indices = np.arange(0, data_size)
        np.random.shuffle(indices)
        for batch_index in range(0, data_size, batch_size):
            curr_idxs = indices[batch_index:batch_index + batch_size]
            yield curr_idxs

@utils.verbose('Initial debugging')
def run_debug_initial(*args, **kwargs):
    return True

def train(config, debug=False):
    if debug and not run_debug_initial(config=config):
        return  # `run_debug_initial` should return True if the program is meant to continue afterward

    root = config['project_root']
    train_params = config['train']
    input_params, output_params = config['inputs'], config['outputs']
    Model = getattr(models, train_params['model'])
    assert isinstance(Model, type)
    lr = train_params.get('lr', 0.1)

    model = Model(input_params, output_params)
    optimizer = tf.train.GradientDescentOptimizer(lr)
    model.train_step = optimizer.minimize(model.loss)

    outfolder = os.path.join(root, train_params['outfolder'])
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    else:
        for _, _, files in os.walk(outfolder):
            if files:
                utils.rm_rf(outfolder, require_confirmation=False)
    with open(os.path.join(outfolder, 'config_in.yaml'), 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    checkpoint_freq, report_freq = train_params['checkpoint_freq'], train_params['report_freq']

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    restore_itr = train_params.get('restore_itr', None)
    if type(restore_itr) == int:
        model.restore(sess, restore_itr, outfolder)  # TODO: this won't work, because the checkpoint was just deleted

    data_inputs, data_labels = load_data(model.inputs, model.labels, config)
    batch_indices = index_generator(train_params['batch_size'], data_labels.values()[0].shape[0])
    for step in range(train_params['max_steps'] + 1):
        indices = next(batch_indices)
        input_feed = {input_tensor: data_inputs[name][indices]
                      for name, input_tensor in model.inputs.items()}
        label_feed = {label_tensor: data_labels[name][indices]
                      for name, label_tensor in model.labels.items()}
        feed_dict = input_feed.copy()
        feed_dict.update(label_feed)
        fetches = [model.train_step, model.loss, model.outputs['winner']['output']]
        _, loss, output = sess.run(fetches, feed_dict=feed_dict)
        if step % checkpoint_freq == 0:
            model.save(sess, step, outfolder)
        if step % report_freq == 0:
            output = np.squeeze(output)
            mean, std = np.mean(output), np.std(output)  # type: float
            print('[o] iteration %d | training loss %.3f | mean %.3f | std: %.3f' % (step, loss, mean, std))

    print('[+] Training complete.')
