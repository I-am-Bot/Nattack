import time
import pickle
import robustml
from robustml_model import Thermometer, LEVELS
from discretization_utils import discretize_uniform
import sys
import argparse
import tensorflow as tf
import numpy as np
from helpers import *
import os
import cv2


npop = 300     # population size
sigma = 0.1    # noise standard deviation
alpha = 0.008  # learning rate
# alpha = 0.001  # learning rate
boxmin = 0
boxmax = 1
boxplus = (boxmin + boxmax) / 2.
boxmul = (boxmax - boxmin) / 2.
folder = './liclipadvImages/'
epsi = 0.032

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--cifar-path', type=str, default='../cifar10_data/test_batch',
            help='path to the test_batch file from http://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz')
    parser.add_argument('--perturb', type=str, default='lid_perturb')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=100)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    test_loss = 0
    correct = 0
    total = 0
    totalImages = 0
    succImages = 0
    faillist = []



    # set up TensorFlow session

    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)


    # initialize a model
    model = Thermometer(sess)

    print(model.threat_model.targeted)
    # initialize an attack (it's a white box attack, and it's allowed to look
    # at the internals of the model in any way it wants)
    # attack = BPDA(sess, model, epsilon=model.threat_model.epsilon, debug=args.debug)
    # attack = Attack(sess, model.model, epsilon=model.threat_model.epsilon)

    # initialize a data provider for CIFAR-10 images
    provider = robustml.provider.CIFAR10(args.cifar_path)
    input_xs = tf.placeholder(tf.float32, [None, 32, 32, 3])
    start = 0
    end = 10000
    total = 0
    uniform = discretize_uniform(input_xs, levels=LEVELS, thermometer=True)
    real_logits = tf.nn.softmax(model.model(uniform))
    successlist = []
    printlist = []

    start_time = time.time()
    perturbs = os.listdir('./')
    all_dir = []
    for x in perturbs:
        if 'perturb' in x:
            all_dir.append(x)


    for y in all_dir:
      perturb_files = os.listdir(y)
      numbers = []
      totalImages = 0
      succImages = 0

      numbers = []
      for x in perturb_files:
        number = x.split('_')[-1]
        name = x.split('_')[0]
        number1 = int(number.split('.pkl')[0])
        numbers.append(number1)

      for i in numbers:
        success = False
        print('evaluating %d of [%d, %d)' % (i, start, end), file=sys.stderr)
        inputs, targets= provider[i]
        modify = np.random.randn(1,3,32,32) * 0.001
        in_pkl = y + '/' +name +'_' + str(i)+'.pkl'
        ##### thermometer encoding

        logits = sess.run(real_logits,feed_dict={input_xs: [inputs]})
        if np.argmax(logits) != targets:
            print('skip the wrong example ', i)
            continue
        totalImages += 1
        try:
            modify = pickle.load(open(in_pkl, 'rb'))
        except:
            modify = pickle.load(open(in_pkl,'rb'),encoding='bytes')
#         if 'cascade' in in_pkl:
#             modify = cv2.resize(modify[0].transpose(1, 2, 0), dsize=(32, 32), interpolation=cv2.INTER_LINEAR)
#             modify = modify.transpose(2,0,1)
#             modify = modify.reshape((1,3,32,32))
        realclipinput = modify.reshape(1,32,32,3)+0.5
        realclipdist = realclipinput - inputs
        print(np.abs(realclipdist).max())
        outputsreal = sess.run(real_logits, feed_dict={input_xs: realclipinput})
        
        outputsreal = sess.run(real_logits, feed_dict={input_xs: realclipinput})
        if (np.argmax(outputsreal) != targets) and (np.abs(realclipdist).max() <= epsi):
            succImages += 1

        success_rate = succImages / float(totalImages)
      print('name:',y)
      print('succ rate', success_rate)
      print('succ {} , total {}'.format(succImages, totalImages))


if __name__ == '__main__':
    main()
