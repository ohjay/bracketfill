#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python

import os
import tensorflow as tf
from math import log

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
            outputs_dst[output_name] = output_info
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
        saver.restore(sess, os.path.join(outfolder, iteration))
        print('[+] Model restored to iteration %d (outfolder=%s).' % (iteration, outfolder))

class LogisticRegression(Model):
    def __init__(self, inputs, outputs):
        Model.__init__(self, inputs, outputs)
        self.build_graph()

    def build_graph(self):
        input_tensors = self.inputs.values()
        _inputs = input_tensors[0] if len(input_tensors) == 1 else tf.concat(input_tensors, 1)
        total_input_size = sum([_it.get_shape().as_list()[1] for _it in input_tensors])
        dtype = self.outputs.values()[0]['dtype']

        weights = tf.get_variable('W', [total_input_size, 1], dtype=dtype)
        biases = tf.get_variable('b', [1], dtype=dtype, initializer=tf.constant_initializer(0.0, dtype=dtype))
        _linear = tf.matmul(_inputs, weights) + biases

        zero, one = tf.constant(0.0), tf.constant(1.0)
        output = tf.divide(tf.exp(_linear), tf.add(one, tf.exp(_linear)), name='output')
        predicted_class = tf.clip_by_value(tf.round(output), zero, one, name='predicted_class')

        _labels = self.labels.values()[0]
        _argument = tf.add(one, tf.exp(tf.negative(_labels * predicted_class)))
        self.loss = tf.constant(1.0 / log(2)) * tf.reduce_mean(tf.log(_argument))
