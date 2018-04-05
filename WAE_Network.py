import numpy as np
import utils
import matplotlib
import matplotlib.pyplot as plt
import tensorflow as tf

BATCH_SIZE = 128 # Batch size
ITERS = 100001 # How many generator iterations to train for 


class AE(object):
    def __init__(self):
        # define inputs
        self.x_hat = tf.placeholder(tf.float32, shape=[None, self.get_image_dim()], name='copy_img')
        self.x = tf.placeholder(tf.float32, shape=[None, self.get_image_dim()], name='input_img')
        self.z, self.rx = self.autoencoder(self.x_hat, self.x)
        
        # input for decoding only
        self.z_in = tf.placeholder(tf.float32, shape=[None, self.get_latent_dim()], name='latent_noise')
        self.decoded = self.decoder(self.z_in, self.get_image_dim())
        
        # optimization
        self.loss, self.train_op = self.define_loss()
        self.saver = tf.train.Saver(max_to_keep=1)
        
    def get_image_dim(self):
        return 2
    def get_latent_dim(self):
        return 2

    # Restore
    def restore_session(self, sess, checkpoint_dir = None):
        if(checkpoint_dir == None):
            checkpoint_dir = self.MODEL_DIRECTORY
            
        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
        self.saver.restore(sess, ckpt.model_checkpoint_path)
        
    # Gaussian MLP as encoder
    def gaussian_MLP_encoder(self, x, n_hidden=256, reuse=False):
        with tf.variable_scope("gaussian_MLP_encoder", reuse=reuse):
            layer_1 = tf.layers.dense(x, 256)
            layer_1 = tf.nn.relu(layer_1)
            
            layer_2 = tf.layers.dense(layer_1, 256)
            layer_2 = tf.nn.relu(layer_2)
            
            layer_3 = tf.layers.dense(layer_2, 256)
            layer_3 = tf.nn.relu(layer_3)
            
            layer_4 = tf.layers.dense(layer_3, 256)
            layer_4 = tf.nn.relu(layer_4)
            
            y = tf.layers.dense(layer_4, self.get_latent_dim())

        return y

    # Bernoulli MLP as decoder
    def bernoulli_MLP_decoder(self, z, n_hidden=256, reuse=False):
        with tf.variable_scope("bernoulli_MLP_decoder", reuse=reuse):
            # initializers
            layer_1 = tf.layers.dense(z, 256)
            layer_1 = tf.nn.relu(layer_1)
            
            layer_2 = tf.layers.dense(layer_1, 256)
            layer_2 = tf.nn.relu(layer_2)
            
            layer_3 = tf.layers.dense(layer_2, 256)
            layer_3 = tf.nn.relu(layer_3)
            
            layer_4 = tf.layers.dense(layer_3, 256)
            layer_4 = tf.nn.relu(layer_4)
            
            y = tf.layers.dense(layer_4, self.get_image_dim())

        return y
    
    # Gateway
    def autoencoder(self, x_hat, x, n_hidden=256, reuse=False):
        # encoding
        z = self.gaussian_MLP_encoder(x_hat, n_hidden, reuse) 
        #z = z + 0.1 * tf.random_normal(tf.shape(z), 0, 1, dtype=tf.float32)

        # decoding
        y = self.bernoulli_MLP_decoder(z, n_hidden, reuse)
        
        return z, y
    
    def define_loss(self):
        loss = tf.squared_difference(self.rx, self.x)
        train_op = tf.train.AdamOptimizer(1e-4).minimize(loss)
        
        return loss, train_op
        
    def decoder(self, z, dim_img, n_hidden=256):
        y = self.bernoulli_MLP_decoder(z, n_hidden, reuse=True)
        return y
    
    def test_generate(self, sess, gen, n_samples = 8192, filename='samples.png'):
        fig, ax = plt.subplots()
        
        noises = self.noise_gen((n_samples, self.get_latent_dim()))
        gen_points = sess.run(self.decoded,
                                 feed_dict={self.z_in: noises})
        
        plt.scatter(gen_points[:,0], gen_points[:,1], s=0.4, c='b', alpha=0.4)
        
        for i in range(500):
            batch, _ = next(utils.batch_gen(gen))
            rx, res = sess.run([self.rx, self.z], feed_dict={self.x_hat: batch, self.x: batch})
            plt.scatter(res[:,0], res[:,1], s=5, c='r', alpha=0.01)
        
        plt.scatter(rx[:,0], rx[:,1], s=5, c='g', alpha=1)
        
        fig.savefig(filename)
        plt.close()
        
    def train(self, sess):
        pass
        
    def noise_gen(self, noise_size):
        return np.random.normal(size=noise_size).astype('float32')

    
     
    
    
    
    
    
    
    
    
    
#########################################################################

CRITIC_ITERS = 5
from GAN_Framework import GAN

class GAN_WAE(GAN):
    def __init__(self, encoder):
        self.data = tf.placeholder(tf.float32, shape=[None, self.get_image_dim()], name='data')
        self.qz = encoder(self.data, reuse=True)
        self.pz = tf.placeholder(tf.float32, shape=[None, self.get_image_dim()], name='prior')
        
        self.Discriminator_fake = self.build_discriminator(self.qz)
        self.Discriminator_real = self.build_discriminator(self.pz, True)
        
        self.disc_params = [var for var in tf.trainable_variables() if 'Discriminator' in var.name]
        self.ae_cost, self.disc_cost, self.disc_train_op = self.define_loss()
        
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
            output = tf.sigmoid(output)
            output = tf.clip_by_value(output, 1e-4, 1 - 1e-4)
            
        return tf.reshape(output, [-1])
    
    def define_loss(self):
        disc_fake = self.Discriminator_fake
        disc_real = self.Discriminator_real
        
        ae_cost = tf.reduce_mean(tf.log(1. - disc_fake))
        disc_cost = -tf.reduce_mean(tf.log(disc_real) + tf.log(1. - disc_fake))
        
        disc_train_op = tf.train.AdamOptimizer(
            learning_rate=1e-4, 
            beta1=0.5, 
            beta2=0.9
        ).minimize(disc_cost, var_list=self.disc_params)
        return ae_cost, disc_cost, disc_train_op
    
    def get_latent_dim(self):
        return 2
    def get_image_dim(self):
        return 2
    
    def train(self, session, train_gen, noise_gen, it):
        # cache variables
        disc_cost, disc_train_op = self.disc_cost, self.disc_train_op
        
        # Train loop
        noise_size = (BATCH_SIZE, self.get_image_dim())
        
        # Run discriminator
        disc_iters = CRITIC_ITERS
        for i in range(disc_iters):
            _data, _ = next(utils.batch_gen(train_gen))
            _disc_cost, _ = session.run(
                [disc_cost, disc_train_op],
                feed_dict={
                    self.data: _data,
                    self.pz: noise_gen(noise_size)})
            
            if( it % 100 == 4 ):
                print ('at iteration : ', i, ' disc_loss : ', _disc_cost)

##########################################################    
class WAE(AE):    
    def __init__(self):
        self.data_func = utils.swiss_load
        self.MODEL_DIRECTORY = './model_WAE/TEST/'
        self.LAMBDA = 10
        
        super(WAE, self).__init__()
    
    def gan_penalty(self):
        # Pz = Qz test based on GAN in the Z space
        self.refGAN = GAN_WAE(self.gaussian_MLP_encoder)
        return self.refGAN.ae_cost
        

    def mmd_penalty(self, sample_qz, sample_pz):
        sigma2_p = 1
        n = BATCH_SIZE
        half_size = (n * n - n) / 2

        norms_pz = tf.reduce_sum(tf.square(sample_pz), axis=1, keep_dims=True)
        dotprods_pz = tf.matmul(sample_pz, sample_pz, transpose_b=True)
        distances_pz = norms_pz + tf.transpose(norms_pz) - 2. * dotprods_pz
    
        norms_qz = tf.reduce_sum(tf.square(sample_qz), axis=1, keep_dims=True)
        dotprods_qz = tf.matmul(sample_qz, sample_qz, transpose_b=True)
        distances_qz = norms_qz + tf.transpose(norms_qz) - 2. * dotprods_qz

        dotprods = tf.matmul(sample_qz, sample_pz, transpose_b=True)
        distances = norms_qz + tf.transpose(norms_pz) - 2. * dotprods

        # Median heuristic for the sigma^2 of Gaussian kernel
        sigma2_k = tf.nn.top_k(
            tf.reshape(distances, [-1]), half_size).values[half_size - 1]
        sigma2_k += tf.nn.top_k(
            tf.reshape(distances_qz, [-1]), half_size).values[half_size - 1]

        res1 = tf.exp( - distances_qz / 2. / sigma2_k)
        res1 += tf.exp( - distances_pz / 2. / sigma2_k)
        res1 = tf.multiply(res1, 1. - tf.eye(n))
        res1 = tf.reduce_sum(res1) / (n * n - n)
        res2 = tf.exp( - distances / 2. / sigma2_k)
        res2 = tf.reduce_sum(res2) * 2. / (n * n)
        stat = res1 - res2
        
        return stat
    
    def define_loss(self):
        resconstruct_loss = tf.reduce_mean(tf.squared_difference(self.rx, self.x))
        self.res_loss = resconstruct_loss
        
        # Define GAN Loss
        #matching_loss = self.gan_penalty()
        self.qz = self.z
        self.pz = tf.placeholder(tf.float32, shape=[None, self.get_latent_dim()], name='latent_noise')
        matching_loss = self.mmd_penalty(self.qz, self.pz)
        
        loss = self.LAMBDA * tf.reduce_mean(matching_loss) + resconstruct_loss
        
        self.encode_params = [var for var in tf.trainable_variables() if 'encoder' in var.name]
        self.decode_params = [var for var in tf.trainable_variables() if 'decoder' in var.name]
        
        self.global_step = tf.Variable(0)
        learning_rate = tf.train.exponential_decay(
                1e-4,  # Base learning rate.
                self.global_step,  # Current index into the dataset.
                5000,  # Decay step.
                0.95,  # Decay rate.
                staircase=True)
        ae_train_op = tf.train.AdamOptimizer(
            learning_rate=learning_rate, 
            beta1=0.5,
            beta2=0.9).minimize(loss, global_step=self.global_step)
        
        return loss, ae_train_op
        
    def train(self, sess):
        # Dataset iterator
        train_gen, _, _ = utils.load_dataset(BATCH_SIZE, self.data_func)
        
        noise_size = (BATCH_SIZE, self.get_latent_dim())
        # Train loop
        for iteration in range(ITERS):
            batch_xs, _ = next(utils.batch_gen(train_gen))
            batch_noise = batch_xs# + np.random.normal(0, 0.1, size=batch_xs.shape)

            # HAHAHAHAHA SIBALSEKKI
            #self.refGAN.train(sess, train_gen, self.noise_gen, iteration)
            
            _, res_loss = sess.run(
                    (self.train_op, self.res_loss),
                    feed_dict={self.x_hat: batch_noise, self.x: batch_xs, self.pz: self.noise_gen(noise_size), 
                              #self.refGAN.data: batch_xs
                              })

            # Calculate dev loss and generate samples every 1000 iters
            if iteration % 1000 == 10:
                print ('at iteration : ', iteration, ' loss : ', res_loss)
                self.test_generate(sess, train_gen, filename='train_samples.png')
    
    