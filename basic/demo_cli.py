import os
import argparse
import json
import math
import shutil
from pprint import pprint

import tensorflow as tf
from tqdm import tqdm
import numpy as np
from IPython import embed
from basic.evaluator import F1Evaluator, Evaluator, ForwardEvaluator, MultiGPUF1Evaluator
from basic.graph_handler import GraphHandler
from basic.model import Model, get_multi_gpu_models
from basic.trainer import Trainer, MultiGPUTrainer

from basic.main import set_dirs
from basic.read_data import load_metadata, read_data, get_squad_data_filter, update_config

flags = tf.app.flags

flags.DEFINE_string("model_name", "basic", "Model name [basic]")
flags.DEFINE_string("data_dir", "data/squad", "Data dir [data/squad]")
flags.DEFINE_string("run_id", "0", "Run ID [0]")
flags.DEFINE_string("out_base_dir", "out", "out base dir [out]")

flags.DEFINE_integer("batch_size", 1, "Batch size [60]")
flags.DEFINE_float("init_lr", 0.5, "Initial learning rate [0.5]")
flags.DEFINE_integer("num_epochs", 50, "Total number of epochs for training [50]")
flags.DEFINE_integer("num_steps", 18000, "Number of steps [20000]")
flags.DEFINE_integer("eval_num_batches", 0, "eval num batches [100]")
flags.DEFINE_integer("load_step", 0, "load step [0]")
flags.DEFINE_integer("early_stop", 4, "early stop [4]")

flags.DEFINE_string("mode", "demo", "trains | test | forward [test]")
flags.DEFINE_boolean("load", True, "load saved data? [True]")
flags.DEFINE_boolean("progress", True, "Show progress? [True]")
flags.DEFINE_integer("log_period", 100, "Log period [100]")
flags.DEFINE_integer("eval_period", 1000, "Eval period [1000]")
flags.DEFINE_integer("save_period", 1000, "Save Period [1000]")
flags.DEFINE_float("decay", 0.9, "Exponential moving average decay [0.9]")
flags.DEFINE_float("var_decay", 0.999, "Exponential moving average decay [0.9]")
flags.DEFINE_boolean("load_ema", True, "Load ema")

flags.DEFINE_boolean("draft", False, "Draft for quick testing? [False]")

flags.DEFINE_integer("hidden_size", 100, "Hidden size [100]")
flags.DEFINE_integer("char_out_size", 100, "Char out size [100]")
flags.DEFINE_float("input_keep_prob", 0.8, "Input keep prob [0.8]")
flags.DEFINE_integer("char_emb_size", 8, "Char emb size [8]")
flags.DEFINE_integer("char_filter_height", 5, "Char filter height [5]")
flags.DEFINE_float("wd", 0.0, "Weight decay [0.0]")
flags.DEFINE_bool("lower_word", True, "lower word [True]")
flags.DEFINE_bool("dump_eval", True, "dump eval? [True]")
flags.DEFINE_bool("dump_answer", True, "dump answer? [True]")
flags.DEFINE_string("model", "2", "config 1 |2 [2]")
flags.DEFINE_bool("squash", False, "squash the sentences into one? [False]")
flags.DEFINE_bool("single", False, "supervise only the answer sentence? [False]")

flags.DEFINE_integer("word_count_th", 30, "word count th [100]")
flags.DEFINE_integer("char_count_th", 150, "char count th [500]")
flags.DEFINE_integer("sent_size_th", 1000, "sent size th [64]")
flags.DEFINE_integer("num_sents_th", 1000, "num sents th [8]")
flags.DEFINE_integer("ques_size_th", 100, "ques size th [32]")
flags.DEFINE_integer("word_size_th", 48, "word size th [16]")
flags.DEFINE_integer("para_size_th", 1000, "para size th [256]")

flags.DEFINE_bool("swap_memory", True, "swap memory? [True]")
flags.DEFINE_string("data_filter", "max", "max | valid | semi [max]")
flags.DEFINE_bool("finetune", False, "finetune? [False]")
flags.DEFINE_bool("feed_gt", False, "feed gt prev token during training [False]")
flags.DEFINE_bool("feed_hard", False, "feed hard argmax prev token during testing [False]")
flags.DEFINE_bool("use_glove_for_unk", True, "use glove for unk [False]")
flags.DEFINE_bool("known_if_glove", True, "consider as known if present in glove [False]")
flags.DEFINE_bool("eval", True, "eval? [True]")
flags.DEFINE_integer("highway_num_layers", 2, "highway num layers [2]")
flags.DEFINE_bool("use_word_emb", True, "use word embedding? [True]")
flags.DEFINE_bool("use_char_emb", True, "use char emb? [True]")

flags.DEFINE_string("forward_name", "single", "Forward name [single]")
flags.DEFINE_string("answer_path", "", "Answer path []")
flags.DEFINE_string("load_path", "out/basic/00/save/basic-18000", "Load path []")
flags.DEFINE_string("shared_path", "", "Shared path []")
flags.DEFINE_string("device", "/cpu:0", "default device [/cpu:0]")
flags.DEFINE_integer("num_gpus", 1, "num of gpus [1]")

flags.DEFINE_string("out_channel_dims", "100", "Out channel dims, separated by commas [100]")
flags.DEFINE_string("filter_heights", "5", "Filter heights, separated by commas [5]")

flags.DEFINE_bool("share_cnn_weights", True, "Share CNN weights [False]")
flags.DEFINE_bool("share_lstm_weights", True, "Share LSTM weights [True]")
flags.DEFINE_bool("two_prepro_layers", False, "Use two layers for preprocessing? [False]")
flags.DEFINE_bool("aug_att", False, "Augment attention layers with more features? [False]")
flags.DEFINE_integer("max_to_keep", 20, "Max recent saves to keep [20]")
flags.DEFINE_bool("vis", False, "output visualization numbers? [False]")
flags.DEFINE_bool("dump_pickle", True, "Dump pickle instead of json? [True]")
flags.DEFINE_float("keep_prob", 0.8, "keep prob [0.8]")
flags.DEFINE_string("prev_mode", "a", "prev mode gy | y | a [a]")
flags.DEFINE_string("logit_func", "tri_linear", "logit func [tri_linear]")
flags.DEFINE_bool("sh", False, "use superhighway [False]")
flags.DEFINE_string("answer_func", "linear", "answer logit func [linear]")
flags.DEFINE_bool("cluster", False, "Cluster data for faster training [False]")
flags.DEFINE_bool("len_opt", True, "Length optimization? [False]")
flags.DEFINE_bool("cpu_opt", True, "CPU optimization? GPU computation can be slower [False]")
flags.DEFINE_string("sh_logit_func", "tri_linear", "sh logit func [tri_linear]")
flags.DEFINE_bool("q2c_att", True, "question-to-context attention? [True]")
flags.DEFINE_bool("c2q_att", True, "context-to-question attention? [True]")
# flags.DEFINE_bool("static_att", True, "static attention [True]")
flags.DEFINE_bool("highway", True, "highway? [True]")
flags.DEFINE_bool("late", False, "Late fusion? [False]")
flags.DEFINE_string("device_type", "cpu", "cpu | gpu [gpu]")
flags.DEFINE_bool("dynamic_att", False, "Dynamic attention [False]")

class Demo(object):
    def __init__(self):
        config = flags.FLAGS
        config.out_dir = os.path.join(config.out_base_dir, config.model_name, str(config.run_id).zfill(2))
        config.max_sent_size = config.sent_size_th
        config.max_num_sents = config.num_sents_th
        config.max_ques_size = config.ques_size_th
        config.max_word_size = config.word_size_th
        config.max_para_size = config.para_size_th

        self.config = config
        self.test_data = None
        self.data_ready(update=True)
	

        config = self.config

        set_dirs(config)
        models = get_multi_gpu_models(config)
        self.evaluator = ForwardEvaluator(config, models[0], tensor_dict=models[0].tensor_dict if config.vis else None)

        self.sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
        self.graph_handler = GraphHandler(config, models[0])
        self.graph_handler.initialize(self.sess)
        self.config = config

    def data_ready(self, data=None, update=False):
        
        config = self.config
        config.batch_size = 1
        test_data = read_data(self.config, 'demo', True, data=data, data_set=self.test_data)

        if update:
            update_config(self.config, [test_data])
            if config.use_glove_for_unk:
                word2vec_dict = test_data.shared['lower_word2vec'] if config.lower_word else test_data.shared['word2vec']
                new_word2idx_dict = test_data.shared['new_word2idx']
                idx2vec_dict = {idx: word2vec_dict[word] for word, idx in new_word2idx_dict.items()}
                new_emb_mat = np.array([idx2vec_dict[idx] for idx in range(len(idx2vec_dict))], dtype='float32')
                config.new_emb_mat = new_emb_mat
        self.config = config
        self.test_data = test_data

    def run(self, data):
        self.data_ready(data=data)
        test_data = self.test_data
        config = self.config
        e = None
        for multi_batch in test_data.get_batches(config.batch_size, num_batches=1, cluster=config.cluster):
            ei = self.evaluator.get_evaluation(self.sess, multi_batch)
            e = ei if e is None else e + ei
            print(e)
        return (e.id2answer_dict[0])

if __name__ == "__main__":
    tf.app.run()
