#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import models
import tensorflow as tf
import numpy as np
from collections import Counter
from parse import parse_sets, parse_players

def load_data(model_inputs, model_labels, sets_source, players_source):
    sets = parse_sets(sets_source)
    players = parse_players(players_source)
    data_inputs = {input_name: [] for input_name in model_inputs.keys()}
    data_labels = {label_name: [] for label_name in model_labels.keys()}
    for _set in sets:
        player0 = _set['player0']
        player1 = _set['player1']
        for input_name in model_inputs.keys():
            if input_name in ('main', 'secondary', 'floaty'):
                data_inputs[input_name].append([players[player0][input_name], players[player1][input_name]])
            else:
                print('[-] Unrecognized input name: %s.' % input_name)
        for label_name in model_labels.keys():
            if label_name == 'winner':
                data_labels['winner'] = _set['winner']
            else:
                print('[-] Unrecognized label name: %s.' % label_name)

    for input_name, data in data_inputs.items():
        data_inputs[input_name] = np.array(data)
    for label_name, data in data_labels.items():
        data_labels[label_name] = np.array(data)

    return data_inputs, data_labels

def index_generator(batch_size, data_size):
    while True:
        idxs = np.arange(0, data_size)
        np.random.shuffle(idxs)
        for batch_idx in range(0, data_size, batch_size):
            curr_idxs = idxs[batch_idx:batch_idx + batch_size]
            yield curr_idxs

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
    checkpoint_freq, report_freq = train_params['checkpoint_freq'], train_params['report_freq']

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    restore_itr = train_params.get('restore_itr', None)
    if type(restore_itr) == int:
        model.restore(sess, restore_itr, outfolder)

    data_inputs, data_labels = load_data(model.inputs, model.labels, train_params['sets_source'])
    batch_indices = index_generator(train_params['batch_size'], data_labels.values()[0].shape[0])
    for step in range(train_params['max_steps']):
        indices = next(batch_indices)
        input_feed = Counter({input_tensor: data_inputs[name][indices]
                              for name, input_tensor in model.inputs.items()})
        label_feed = Counter({label_tensor: data_labels[name][indices]
                              for name, label_tensor in model.labels.items()})
        _, loss = sess.run([model.train_step, model.loss], feed_dict=(input_feed + label_feed))
        if step % checkpoint_freq == 0:
            model.save(sess, step, outfolder)
        if step % report_freq == 0:
            print('[o] iteration %d / training loss %.3f' % (step, loss))

    print('[+] Training complete.')
