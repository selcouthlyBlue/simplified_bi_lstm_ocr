import tensorflow as tf

from optimizer_enum import Optimizers
from tensorflow.contrib import rnn
from tensorflow.contrib import grid_rnn

def ctc_loss(inputs, labels, sequence_length,
             preprocess_collapse_repeated_labels=True,
             ctc_merge_repeated=True,
             inputs_are_time_major=True):
    return tf.nn.ctc_loss(inputs=inputs, labels=labels, sequence_length=sequence_length,
                          preprocess_collapse_repeated=preprocess_collapse_repeated_labels,
                          ctc_merge_repeated=ctc_merge_repeated,
                          time_major=inputs_are_time_major)

def input_data(shape, name: str = 'InputData', input_type='float32'):
    return tf.placeholder(shape=shape, dtype=_get_type(input_type), name=name)

def reshape(tensor: tf.Tensor, new_shape: list):
    return tf.reshape(tensor, new_shape, name="reshape")

def stack_bidirectional_lstm(inputs, num_hidden_list):
    lstm_fw_cells = [rnn.BasicLSTMCell(num_hidden, forget_bias=1.0) for num_hidden in num_hidden_list]
    lstm_bw_cells = [rnn.BasicLSTMCell(num_hidden, forget_bias=1.0) for num_hidden in num_hidden_list]
    return tf.contrib.rnn.stack_bidirectional_dynamic_rnn(lstm_fw_cells, lstm_bw_cells, inputs,
                                                          dtype=tf.float32)[0]
def bidirectional_grid_lstm(inputs, num_hidden):
    cell_fw = grid_rnn.Grid2LSTMCell(num_units=num_hidden)
    cell_bw = grid_rnn.Grid2LSTMCell(num_units=num_hidden)
    return tf.nn.bidirectional_dynamic_rnn(cell_fw, cell_bw, inputs, dtype=tf.float32)[0]

def decode(inputs, sequence_length, merge_repeated=True):
    decoded, log_probabilities = tf.nn.ctc_beam_search_decoder(inputs, sequence_length, merge_repeated)
    dense_decoded = tf.sparse_to_dense(tf.to_int32(decoded[0].indices),
                                       tf.to_int32(decoded[0].values),
                                       tf.to_int32(decoded[0].dense_shape),
                                       name="output")
    return dense_decoded, log_probabilities

def label_error_rate(y_pred, y_true):
    return tf.reduce_mean(tf.edit_distance(tf.cast(y_pred, tf.int32), y_true))

def optimize(loss, optimizer_name, learning_rate):
    global_step = tf.Variable(0, name='global_step', trainable=False)
    optimizer = get_optimizer(learning_rate, optimizer_name)
    return optimizer.minimize(loss, global_step=global_step)

def get_optimizer(learning_rate, optimizer_name):
    if optimizer_name == Optimizers.MOMENTUM:
        optimizer = tf.train.MomentumOptimizer(learning_rate, momentum=0.9)
    elif optimizer_name == Optimizers.ADAM:
        optimizer = tf.train.AdamOptimizer(learning_rate)
    elif optimizer_name == Optimizers.ADADELTA:
        optimizer = tf.train.AdadeltaOptimizer(learning_rate)
    else:
        optimizer = tf.train.RMSPropOptimizer(learning_rate)
    return optimizer

def sparse_input_data(input_type=tf.int32):
    return tf.sparse_placeholder(dtype=input_type)

def get_time_major(inputs, num_classes, batch_size, num_hidden_units):
    outputs = reshape(inputs, [-1, num_hidden_units])

    W = tf.Variable(tf.truncated_normal([num_hidden_units,
                                         num_classes],
                                        stddev=0.1, dtype=tf.float32), name='W')
    b = tf.Variable(tf.constant(0., dtype=tf.float32, shape=[num_classes], name='b'))

    logits = tf.matmul(outputs, W) + b
    logits = tf.reshape(logits, [batch_size, -1, num_classes])
    logits = tf.transpose(logits, (1, 0, 2))
    return logits

def _get_type(type_str):
    if type_str == 'int32':
        return tf.int32
    return tf.float32

def get_shape(tensor):
    return tf.shape(tensor)

def initialize_variable(initial_value, name, is_trainable):
    return tf.Variable(initial_value, name=name, trainable=is_trainable)

def cost(loss):
    return tf.reduce_mean(loss)

def dense_to_sparse(tensor, eos_token=0):
    indices = tf.where(tf.not_equal(tensor, tf.constant(eos_token, dtype=tensor.dtype)))
    values = tf.gather_nd(tensor, indices)
    shape = tf.shape(tensor, out_type=tf.int64)
    return tf.SparseTensor(indices, values, shape)
