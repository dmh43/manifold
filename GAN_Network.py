import numpy as np
from GAN_Framework import WGAN
import utils
import matplotlib
import matplotlib.pyplot as plt
import tensorflow as tf


class WGAN_test(WGAN):
    def __init__(self):
        self.data_func = utils.test_2d
        self.MODEL_DIRECTORY = "./model_WGAN/test/"
        
        super(WGAN_test, self).__init__()
        
    def noise_gen(self, noise_size):
        return np.random.normal(size=noise_size).astype('float32')
    
    def test_generate(self, sess, n_samples = 64000, filename='images/samples.png'):
        fig, ax = plt.subplots()
        
        noises = self.noise_gen((n_samples,self.get_latent_dim()))
        gen_points = sess.run(self.Generator,
                                 feed_dict={self.z_in: noises})
        
        plt.scatter(gen_points[:,0], gen_points[:,1], s=0.4, c='b', alpha=0.7)
        
        fig.savefig(filename)
        plt.close()
        
    def get_latent_dim(self):
        return 2
    def get_image_dim(self):
        return 2
    
    

    
########################################################################3    
########################################################################3
########################################################################3
########################################################################3
########################################################################3

class WGAN_Swiss(WGAN):
    def __init__(self):
        self.data_func = utils.swiss_load
        self.MODEL_DIRECTORY = "./model_WGAN/Swiss/"
        
        super(WGAN_Swiss, self).__init__()
        
    def noise_gen(self, noise_size):
        return np.random.normal(size=noise_size).astype('float32')
        #return np.random.uniform(0, 10, size=noise_size).astype('float32')
    
    def build_discriminator(self, inputs, reuse = False):
        n_hidden = 256
        with tf.variable_scope("Discriminator", reuse=reuse):
            # Hidden fully connected layer with 256 neurons
            layer_1 = tf.layers.dense(inputs, n_hidden)
            layer_1 = utils.LeakyReLU(layer_1, alpha=0.01)
            
            layer_2 = tf.layers.dense(layer_1, n_hidden)
            layer_2 = utils.LeakyReLU(layer_2, alpha=0.01)
            
            output = tf.layers.dense(layer_2, 1)
        
        return tf.reshape(output, [-1])
    
    def define_learning_rate(self):
        self.train_step = tf.Variable(0)
        learning_rate = tf.train.exponential_decay(
                1e-4,  # Base learning rate.
                self.proj_step,  # Current index into the dataset.
                10000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        disc_rate = tf.train.exponential_decay(
                1e-3,  # Base learning rate.
                self.proj_step,  # Current index into the dataset.
                10000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        return learning_rate, disc_rate
    
    def test_generate(self, sess, n_samples = 64000, filename='images/samples.png'):
        fig = plt.figure()
        
        noises = self.noise_gen((n_samples,self.get_latent_dim()))
        gen_points = sess.run(self.Generator,
                                 feed_dict={self.z_in: noises})
        
        plt.scatter(gen_points[:,0], gen_points[:,1], s=0.4, c='b', alpha=0.7)
        """
        for i in range(10):
            t = i + np.linspace(0, 0.5, num=500)
            x, y = 0.1*t*np.cos(t), 0.1*t*np.sin(t)
            plt.scatter(x, y, c='r', s=0.1, alpha=0.5)
        """
        fig.savefig(filename)
        plt.close()
        
    def get_latent_dim(self):
        return 1
    def get_image_dim(self):
        return 2
    
########################################################################3    
########################################################################3
########################################################################3
########################################################################3
########################################################################3
import tensorflow.contrib.layers as layers

class WGAN_MNIST(WGAN):
    def define_default_param(self):
        self.BATCH_SIZE = 64
        self.ITERS = 50001
        self.CRITIC_ITERS = 5
        self.PROJ_ITER = 2500
        self.PROJ_BATCH_SIZE = 25
        
    def __init__(self):
        self.data_func = utils.MNIST_load
        self.MODEL_DIRECTORY = "./model_WGAN/MNIST/"
        
        super(WGAN_MNIST, self).__init__()
        
    def noise_gen(self, noise_size):
        return np.random.normal(size=noise_size).astype('float32')
        #return np.random.uniform(0, 10, size=noise_size).astype('float32')
    
    def define_learning_rate(self):
        self.train_step = tf.Variable(0)
        learning_rate = tf.train.exponential_decay(
                1e-2,  # Base learning rate.
                self.train_step,  # Current index into the dataset.
                3000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        disc_rate = tf.train.exponential_decay(
                1e-3,  # Base learning rate.
                self.train_step,  # Current index into the dataset.
                3000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        return learning_rate, disc_rate
    
    # G(z)
    def build_generator(self, z, reuse=False):
        with tf.variable_scope('Generator', reuse=reuse):
            output = tf.layers.dense(z, 6*6*self.get_latent_dim())
            output = utils.LeakyReLU(output)
            
            output = tf.reshape(output, [-1, 6, 6, self.get_latent_dim()])
            
            output = tf.layers.conv2d_transpose(output, 64, 4, strides=2)
            output = utils.LeakyReLU(output)

            output = tf.layers.conv2d_transpose(output, 1, 2, strides=2)
            output = tf.nn.sigmoid(output)
            
        return tf.reshape(output, [-1, self.get_image_dim()])

    # D(x)
    def build_discriminator(self, x, reuse=False):
        with tf.variable_scope('Discriminator', reuse=reuse):
            output = tf.reshape(x, [-1, 28, 28, 1])

            output = tf.layers.conv2d(output, 128, 5)
            output = utils.LeakyReLU(output)

            output = tf.layers.conv2d(output, 32, 5)
            output = utils.LeakyReLU(output)
            
            output = tf.layers.conv2d(output, 16, 5)
            output = utils.LeakyReLU(output)
            
            output = tf.reshape(output, [-1, 4096])
            output = tf.layers.dense(output, 256)
            
            output = utils.LeakyReLU(output)
            output = tf.layers.dense(output, 1)
            
        return tf.reshape(output, [-1])
    
    def test_generate(self, sess, n_samples = 512, filename='images/samples.png'):
        noises = self.noise_gen((n_samples,self.get_latent_dim()))
        samples = sess.run(self.Generator, feed_dict={self.z_in: noises})
        
        utils.save_images(samples.reshape(n_samples, 28, 28), filename)
        
    def get_latent_dim(self):
        return 15
    def get_image_dim(self):
        return 784
    