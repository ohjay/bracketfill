#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import tensorflow as tf
from math import log

"""
model.py
Model interface and graph spec
"""

class Model(object):
    def __init__(self, inputs, outputs):
        self.inputs = self.load_inputs(inputs)
        self.labels, self.outputs = self.load_outputs(outputs)
        self.loss = None
        self.train_step = None

    def load_inputs(self, inputs):
        """
        :param inputs: A dictionary providing information about the inputs.
        """
        inputs_dst = {}
        for input_name, input_info in inputs.items():
            inputs_dst[input_name] = self.load_placeholder(input_info)
        return inputs_dst

    def load_outputs(self, outputs):
        """
        :param outputs: A dictionary providing information about the outputs.
        """
        labels_dst, outputs_dst = {}, {}
        for output_name, output_info in outputs.items():
            labels_dst[output_name] = self.load_placeholder(output_info)
            outputs_dst[output_name] = {'info': output_info}
        return labels_dst, outputs_dst

    @staticmethod
    def load_placeholder(placeholder_info):
        dtype = placeholder_info['dtype']
        shape = placeholder_info['shape']
        for i in range(len(shape)):
            if type(shape[i]) == str:
                shape[i] = eval(shape[i])
        shape = [None] + shape
        return tf.placeholder(getattr(tf, dtype), shape=shape)

    @staticmethod
    def save(sess, iteration, outfolder='out'):
        if not os.path.exists(outfolder):
            os.makedirs(outfolder)
        base_filepath = os.path.join(outfolder, 'var')
        saver = tf.train.Saver()
        saver.save(sess, base_filepath, global_step=iteration, write_meta_graph=False)
        print('[+] Saving current parameters to %s-%d.index.' % (base_filepath, iteration))

    @staticmethod
    def restore(sess, iteration, outfolder='out'):
        saver = tf.train.Saver()
        saver.restore(sess, os.path.join(outfolder, 'var-%d' % iteration))
        print('[+] Model restored to iteration %d (outfolder=%s).' % (iteration, outfolder))

class LogisticRegression(Model):
    def __init__(self, inputs, outputs):
        Model.__init__(self, inputs, outputs)
        self.build_graph()

    def build_graph(self):
        input_tensors = self.inputs.values()
        _inputs = input_tensors[0] if len(input_tensors) == 1 else tf.concat(input_tensors, 1)
        total_input_size = sum([_it.get_shape().as_list()[1] for _it in input_tensors])
        dtype = self.outputs.values()[0]['info']['dtype']

        weights = tf.get_variable('W', shape=[total_input_size, 1], dtype=dtype,
                                  initializer=tf.contrib.layers.xavier_initializer())
        biases = tf.get_variable('b', shape=[1], dtype=dtype, initializer=tf.constant_initializer(0.5, dtype=dtype))
        _linear = tf.matmul(_inputs, weights) + biases

        output = tf.divide(1.0, tf.add(1.0, tf.exp(tf.negative(_linear))), name='output')
        predicted_class = tf.clip_by_value(tf.round(output), 0.0, 1.0, name='predicted_class')

        output_name = self.outputs.keys()[0]
        self.outputs[output_name]['output'] = output
        self.outputs[output_name]['predicted_class'] = predicted_class

        _labels = tf.squeeze(self.labels.values()[0])
        # self.loss = tf.losses.log_loss(_labels, output)
        _argument = tf.add(1.0, tf.exp(tf.negative(_labels * output)))
        self.loss = tf.constant(1.0 / log(2)) * tf.reduce_mean(tf.log(_argument))
