import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sklearn.datasets
import tensorflow as tf
import utils

class GAN(object):
    def define_default_param(self):
        self.BATCH_SIZE = 128 # Batch size
        self.ITERS = 20001 # How many generator iterations to train for 
        self.CRITIC_ITERS = 10 # For WGAN and WGAN-GP, number of critic iters per gen iter
        
    def __init__(self):
        self.define_default_param()
        
        self.z_in = tf.placeholder(tf.float32, shape=[None, self.get_latent_dim()], name='latent_variable')
        self.data = tf.placeholder(tf.float32, shape=[None, self.get_image_dim()])
        
        self.Generator = self.build_generator(self.z_in)
        self.Discriminator_fake = self.build_discriminator(self.Generator)
        self.Discriminator_real = self.build_discriminator(self.data, True)
        
        self.gen_params = [var for var in tf.trainable_variables() if 'Generator' in var.name]
        self.disc_params = [var for var in tf.trainable_variables() if 'Discriminator' in var.name]
        
        self.disc_cost, self.gen_train_op, self.disc_train_op = self.define_loss()
        self.saver = tf.train.Saver(var_list=self.gen_params + self.disc_params, max_to_keep=1)

    # Restore
    def restore_session(self, sess, checkpoint_dir = None):
        if(checkpoint_dir == None):
            checkpoint_dir = self.MODEL_DIRECTORY
            
        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
        self.saver.restore(sess, ckpt.model_checkpoint_path)
        
    # Defining loss - different from gan to gan
    def define_loss(self):
        raise NotImplementedError
    def train(self, session):
        raise NotImplementedError
        
    def noise_gen(self, noise_size):
        return np.random.normal(size=noise_size).astype('float32')
        
    def test_generate(self, sess, n_samples = 128, filename='samples.png'):
        pass

    def get_image_dim(self): 
        return 0
    
    def get_latent_dim(self): 
        return 0
    
    
    #
    #
    #
    #
    #
    #
    # Default Generator - Decoder
    def build_generator(self, z = None, reuse = False):
        n_hidden = 256
        
        with tf.variable_scope("Generator", reuse=reuse):
            # initializers
            w_init = tf.contrib.layers.variance_scaling_initializer()
            b_init = tf.constant_initializer(0.01)

            # 1st hidden layer
            w0 = tf.get_variable('w0', [z.get_shape()[1], n_hidden], initializer=w_init)
            b0 = tf.get_variable('b0', [n_hidden], initializer=b_init)
            h0 = tf.matmul(z, w0) + b0
            h0 = utils.LeakyReLU(h0)

            # 2nd hidden layer
            w1 = tf.get_variable('w1', [h0.get_shape()[1], n_hidden], initializer=w_init)
            b1 = tf.get_variable('b1', [n_hidden], initializer=b_init)
            h1 = tf.matmul(h0, w1) + b1
            h1 = utils.LeakyReLU(h1)

            # output layer-mean
            l2 = tf.layers.dense(h1, n_hidden)
            l2 = utils.LeakyReLU(l2)
            
            y = tf.layers.dense(l2, self.get_image_dim())
            
        return y

    def build_discriminator(self, inputs, reuse = False):
        with tf.variable_scope("Discriminator", reuse=reuse):
            # Hidden fully connected layer with 256 neurons
            layer_1 = tf.layers.dense(inputs, 256)
            layer_1 = tf.nn.relu(layer_1)
            
            layer_2 = tf.layers.dense(layer_1, 256)
            layer_2 = tf.nn.relu(layer_2)
            
            layer_3 = tf.layers.dense(layer_2, 256)
            layer_3 = tf.nn.relu(layer_3)
            
            layer_4 = tf.layers.dense(layer_3, 256)
            layer_4 = tf.nn.relu(layer_4)
            
            output = tf.layers.dense(layer_4, 1)
        
        return tf.reshape(output, [-1])
    
    #
    #
    #
    #
    #
    #
    #
    #
    # Deferred to sub-classes
    def define_proj(self):
        self.test_x = tf.placeholder(tf.float32, shape=[self.BATCH_SIZE, self.OUTPUT_DIM])
        self.z_hat = tf.get_variable('z_hat', shape=[self.BATCH_SIZE, self.INPUT_DIM], dtype=tf.float32)
        self.out = self.build_generator(self.z_hat, True)
        
        self.proj_loss = tf.reduce_mean(tf.square(self.out - self.test_x))
        self.proj_step = tf.Variable(0)
        learning_rate = tf.train.exponential_decay(
                1e-2,  # Base learning rate.
                self.proj_step * self.CLASSIFIER_BATCH_SIZE,  # Current index into the dataset.
                PROJ_ITER,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        
        self.proj_op = tf.train.AdamOptimizer(
            learning_rate=learning_rate, 
            beta1=0.5,
            beta2=0.9
        ).minimize(self.proj_loss, var_list=self.z_hat, global_step=self.proj_step)

    def find_proj(self, sess, batch_x):
        thresh, cost, iterat = 0.005, 1.0, 0
        while( cost > thresh and iterat < 10):
            sess.run(self.proj_step.assign(0))
            sess.run(self.z_hat.assign(np.random.uniform(-1, 1, size=self.z_hat.shape.as_list())))
            for i in range(PROJ_ITER):
                _, cost = sess.run([self.proj_op, self.proj_loss], feed_dict={self.test_x:batch_x})
                if( i % 500 == 0 ):
                    print ('Projection Cost is : ', cost)
                    
            iterat = iterat + 1
            thresh = thresh + 0.001
        
            lib.save_images.save_images(
                self.out.eval().reshape((self.CLASSIFIER_BATCH_SIZE, 28, 28)), 'test_proj.png'
            )
        D = sess.run(self.grad)
        return D
        
        
""" WGAN Implementation Start """        
class WGAN(GAN):
    def __init__(self):
        self.LAMBDA = .1 # Gradient penalty lambda hyperparameter
        super(WGAN, self).__init__()
        
    def define_learning_rate(self):
        self.proj_step = tf.Variable(0)
        learning_rate = tf.train.exponential_decay(
                3e-3,  # Base learning rate.
                self.proj_step,  # Current index into the dataset.
                1000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        disc_rate = tf.train.exponential_decay(
                1e-4,  # Base learning rate.
                self.proj_step,  # Current index into the dataset.
                2000,  # Decay step.
                0.9,  # Decay rate.
                staircase=True)
        return learning_rate, disc_rate
        
    def define_loss(self):
        fake_data = self.Generator
        disc_fake = self.Discriminator_fake
        disc_real = self.Discriminator_real

        gen_cost = -tf.reduce_mean(disc_fake)
        disc_cost = tf.reduce_mean(disc_fake) - tf.reduce_mean(disc_real)

        alpha = tf.random_uniform(
            shape=[self.BATCH_SIZE,1], 
            minval=0.,
            maxval=1.
        )
        
        differences = fake_data - self.data
        interpolates = self.data + (alpha*differences)
        gradients = tf.gradients(self.build_discriminator(interpolates, True), [interpolates])[0]
        slopes = tf.sqrt(tf.reduce_sum(tf.square(gradients), reduction_indices=[1]))
        gradient_penalty = tf.reduce_mean((slopes-1.)**2)
        disc_cost += self.LAMBDA*gradient_penalty

        learning_rate, disc_rate = self.define_learning_rate()
        
        gen_train_op = tf.train.AdamOptimizer(
            learning_rate=learning_rate, 
            beta1=0.5,
            beta2=0.9
        ).minimize(gen_cost, var_list=self.gen_params, global_step=self.proj_step)
        
        disc_train_op = tf.train.AdamOptimizer(
            learning_rate=disc_rate, 
            beta1=0.5, 
            beta2=0.9
        ).minimize(disc_cost, var_list=self.disc_params)

        return disc_cost, gen_train_op, disc_train_op
    
    def train(self, session):
        # Dataset iterator
        train_gen, _, _ = utils.load_dataset(self.BATCH_SIZE, self.data_func)
        train_gen = utils.batch_gen(train_gen)
        
        # cache variables
        disc_cost, gen_train_op, disc_train_op = self.disc_cost, self.gen_train_op, self.disc_train_op
        
        # Train loop
        noise_size = (self.BATCH_SIZE, self.get_latent_dim())
        for iteration in range(self.ITERS):
            if iteration > 0:
                _ = session.run(gen_train_op, 
                                feed_dict={self.z_in: self.noise_gen(noise_size)})

            # Run discriminator
            disc_iters = self.CRITIC_ITERS
            for i in range(disc_iters):
                _data, label = next(train_gen)
                _disc_cost, _ = session.run(
                    [disc_cost, disc_train_op],
                    feed_dict={
                        self.z_in: self.noise_gen(noise_size),
                        self.data: _data}
                )
                
                if( iteration % 100 == 10 ):
                    print 'disc_cost: ', -_disc_cost

            if( iteration % 100 == 10 ):
                print '-------------------------------------'
                
            # Calculate dev loss and generate samples every 100 iters
            if iteration % 100 == 10:
                self.test_generate(session, filename='train_samples.png')

            # Checkpoint
            if( iteration % 1000 == 999 ):
                print 'Saving model...'
                self.saver.save(session, self.MODEL_DIRECTORY+'checkpoint-'+str(iteration))
                self.saver.export_meta_graph(self.MODEL_DIRECTORY+'checkpoint-'+str(iteration)+'.meta')
