# -*- coding: utf-8 -*-
"""train.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zNrvELw0aAP6g3z6GPoXTXRNqBkaDYJt
"""


from numpy.core.multiarray import ndarray
import wandb
import tensorflow as tf
import time
import matplotlib.pyplot as plt
import numpy as np
import random
from keras.datasets import fashion_mnist
from keras.datasets import mnist
from sklearn.metrics import confusion_matrix

class neural_network:

  
  #-------------------------Constructor to take train_data and test_data--------
  def __init__(self,train_data,train_labels,test_data,test_labels):
    
    #-----------------------Randomize and Normalize the data----------------------------------

    train_data = np.reshape(train_data/255.0,(len(train_data),train_data.shape[1]**2))

    # combine train_data and train_label into a single array

    train_data_label = np.column_stack((train_data, train_labels))

    # shuffle the rows of the combined array in unison
    np.random.shuffle(train_data_label)

    # separate the shuffled array back into train_data and train_label
    train_data = train_data_label[:, :-1]
    train_labels = train_data_label[:, -1]
    train_labels = train_labels.astype(np.int32)
    self.test_data = np.reshape(test_data/255.0,(len(test_data),test_data.shape[1]**2))
    self.test_labels =test_labels 

    #-----------------------Split data in train/validation set(90:10)-----------

    l=int(train_data.shape[0]/100)*90
    self.train_data=train_data[0:l]
    self.train_label=train_labels[0:l]
    self.validation_data = train_data[l:]
    self.validation_label = train_labels[l:]
   
    
  #------Train function to fit neural network with different parameter----------

  def train(self,weight_init="random",hidden_layers=1,size_of_layer=4,activation="sigmoid",optimizer="sgd",learning_rate=0.1,epoch=1,batch_size=4,weight_decay=0.0,loss="cross_entropy",momentum=0.5,beta =0.5,beta1=0.5,beta2=0.5,epsilon=0.000001):
    

    #-----------------------Weight Initialization-------------------------------
    np.random.seed(42)
    self.loss = loss
    self.hi=[size_of_layer]*hidden_layers
    self.activation =activation
    if(weight_init=="Xavier"):
      self.xav()
    elif(weight_init=="random"):
      self.rndm()

    #-------------------------------------Optimizer-----------------------------
    if(optimizer=="sgd"):
      self.sgd(step_size=learning_rate,batch_size =batch_size,epoch=epoch,reg=weight_decay)
    elif(optimizer=="momentum"):
      self.mbgd(step_size=learning_rate,batch_size =batch_size,epoch=epoch,beta=momentum,reg=weight_decay)
    elif(optimizer=="nesterov"):
      self.nagd(step_size=learning_rate,batch_size =batch_size,epoch=epoch,beta=momentum,reg=weight_decay)
    elif(optimizer=="rmsprop"):
      self.rmsprop(step_size=learning_rate,batch_size =batch_size,epoch=epoch,beta=beta,reg=weight_decay)
    elif(optimizer=="adam"):
      self.adam(step_size=learning_rate,batch_size =batch_size,epoch=epoch,beta1=beta1,beta2=beta2,reg=weight_decay)
    elif(optimizer=="nadam"):
      self.nadam(step_size=learning_rate,batch_size =batch_size,epoch=epoch,beta1=beta1,beta2=beta2,reg=weight_decay)
    
    


    

  #------------------------------Xavier Initialization(W & b)-------------------

  def xav(self):
    l= self.train_data.shape[1]

    self.W =[self.xavier_init(self.hi[0],l)] 
    self.b =[self.xavier_init(1,self.hi[0])]
    for i in range(1,len(self.hi)) :
      self.W.append(self.xavier_init(self.hi[i],self.hi[i-1]))
      self.b.append(self.xavier_init(1,self.hi[i])) 
    self.W.append(self.xavier_init(10,self.hi[-1]))
    
    self.b.append(self.xavier_init(1,10))
  

  #-----------------xavier_init_function(Return Matrix of (n,m))----------------

  def xavier_init(self,n, m):
    # Calculate the Xavier initialization scale factor
    xavier_scale = np.sqrt(2.0 / (n + m))

    # Use numpy's random function to generate a matrix of shape (n, m)
    matrix = np.random.randn(n, m) * xavier_scale

    return matrix

  #-----------------------------Random Initialization(W & b)--------------------

  def rndm(self):
    l= self.train_data.shape[1]

    self.W =[np.random.randn(self.hi[0],l)] 
    self.b =[np.random.randn(1,self.hi[0])]
    for i in range(1,len(self.hi)) :
      self.W.append(np.random.randn(self.hi[i],self.hi[i-1]))
      self.b.append(np.random.randn(1,self.hi[i])) 
    self.W.append(np.random.randn(10,self.hi[-1]))
    
    self.b.append(np.random.randn(1,10))

  #--------------------------Relu Activation function---------------------------

  def relu(self,matrix):
    return np.maximum(matrix, 0) 

  #--------------------------Relu Activation Derivation function---------------

  def relu_derivative(self,matrix):
    
    # Create a copy of the input matrix and convert to float
    derivative = np.array(matrix, dtype=np.float64)
    
    # Set negative values to 0
    derivative[derivative < 0] = 0
    
    # Set positive values to 1
    derivative[derivative > 0] = 1

    return derivative

  #--------------------------Tanh Activation function---------------------------

  def tanh(self,matrix):
    
    # Avoid overflow by scaling inputs to the range [-100, 100]
    x = np.clip(matrix, -100, 100)
    
    # Apply tanh element-wise
    return np.tanh(x)

  #-------------------------Tanh Activation Derivative function-----------------
  def tanh_derivative(self,matrix):
   
    # Avoid overflow by scaling inputs to the range [-100, 100]
    x = np.clip(matrix, -100, 100)
    
    # Compute tanh element-wise
    tanh_x = np.tanh(x)
    
    # Compute derivative of tanh element-wise
    derivative = 1 - tanh_x**2
    
    
    
    return derivative

  #-------------------------calculates sigmoid for matrix-----------------------

  def sigmoid(self,x):
  
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

  #------------------------sigmoid_derivative_function--------------------------

  def sigmoid_derivative(self,matrix):
   
    shift = np.max(matrix, axis=1, keepdims=True)
    exp_matrix = np.exp(matrix - shift)
    sig = 1 / (1 + exp_matrix)
    return sig * (1 - sig)

  #-------------------------WX_plus_B function----------------------------------

  def WX_plus_B(self,W, X, b):
    
    #matrix multiply
    result = np.dot(X, W.transpose())

    
    #make b of shape result
    row_count = result.shape[0]
    row_matrix_repeated = np.tile(b, (row_count, 1))

    return result + row_matrix_repeated

  #----------------------------sum each element of column-----------------------

  def sum_columns(self,matrix):
    if isinstance(matrix, np.ndarray):
        # if matrix is a numpy array, convert it to a list
        matrix = matrix.tolist()
    
    # sum the elements of each column and store in a list
    column_sums = [sum(col) for col in zip(*matrix)]
    
    # convert the list to a 2D matrix of shape (1 x n)
    row_matrix = np.array([column_sums])
    
    return row_matrix

  #----------------softmax function for matrix----------------------------------

  def softmax(self,x):
    
    e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return e_x / np.sum(e_x, axis=1, keepdims=True)
  
  #-----------Substract Matrix (W -step_size*W_theta)---------------------------

  def subtract_matrices(self,W, W_theta, step_size):
    
    result_list = []
    for i in range(len(self.W)):
        result = W[i] - step_size * (W_theta[i])
        result_list.append(result)
    return result_list

  #------------------Mean square error function---------------------------------
  def mean_squared_error(self,y_hat, y):
    n = y_hat.shape[0]  # number of samples
    k = y.astype(int)  # convert y to integer type for indexing
    y_k = np.zeros((n, 10))  # create a one-hot encoding of y
    y_k[np.arange(n), k] = 1
    
    # Calculate mean squared error
    mse = np.mean((y_hat - y_k)**2)
    
    return mse
  
  #-------------------Mean square error Derivative function---------------------

  def mean_squared_error_derivative(self,y_hat, y):
    n = y_hat.shape[0]  # number of samples
    k = y.astype(int)  # convert y to integer type for indexing
    y_k = np.zeros((n, 10))  # create a one-hot encoding of y
    y_k[np.arange(n), k] = 1
    
    # Calculate derivative
    dMSE_dy_hat = (2/n) * (y_hat - y_k)
    
    return dMSE_dy_hat
  
  #--------------------cross_entropy_loss derivative----------------------------

  def cross_entropy_loss_derivative(self,y_hat, Y):
    ey = np.zeros((y_hat.shape[0],y_hat.shape[1]))

    for i in range(0,len(Y)):
      ey[i][Y[i]]=1
    
    return (-(ey-y_hat))

  #---------------------Predict labels for Input Data---------------------------

  def predict(self, X_test):
    A,H,y_hat =self.forward_pro(X_test,self.W,self.b)
  
    y_pred = np.argmax(y_hat, axis=1)
    return y_pred
  
  #----------------------Forward Propogation Code-------------------------------

  def forward_pro(self,X,W,b):

    
    A=[]
    H=[]
    A.append(self.WX_plus_B(W[0],X,b[0])) # a0 = WoX +bo
    
    for i in range(1,len(self.hi)):

      H.append(self.activation_fun(A[-1])) # hi = g(ai)
     
      A.append( self.WX_plus_B(W[i],H[-1],b[i])) # ai = WiX +bi

    H.append(self.activation_fun(A[-1]))         # hi  = g(ai)
    A.append(self.WX_plus_B(W[-1],H[-1],b[-1]))  # ai = WiX +bi
    
    #--------apply softmax function for final probbilities----------------------
    y_hat = self.softmax((A[-1]))

    return A,H,y_hat
  
  #----------------Back Proppogation function-----------------------------------

  def back_prop(self,X,Y,A,H,y_hat):


    W_theta , b_theta,H_theta,A_theta =[],[],[],[]
    
    L =len(A)

    #------------------------Check if loss is cross_entropy---------------------
    if(self.loss=="cross_entropy"):
      A_theta.append(self.cross_entropy_loss_derivative(y_hat,Y))
    if(self.loss=="MSE"):
      A_theta.append(self.mean_squared_error_derivative(y_hat,Y))
    
    #-------------------------W_theta , b_theta calculation---------------------

    for k in range(L-1,0,-1):
      
      W_theta.append((np.matmul(A_theta[-1].transpose(),H[k-1])+self.reg*self.W[k]) ) # athetak*h[k-1]
      b_theta.append( self.sum_columns(A_theta[-1]))                                
      H_theta.append(np.matmul(A_theta[-1],self.W[k]))
  
      A_theta.append(H_theta[-1]*self.activation_derivative(A[k-1]))

    W_theta.append((np.matmul(A_theta[-1].transpose(),X)+self.reg*self.W[0]))
    b_theta.append(self.sum_columns(A_theta[-1]))

    W_theta.reverse()
    b_theta.reverse()

    return W_theta , b_theta

  #-------------------------Accuracy Calculation--------------------------------

  def accuracy(self, X_test, y_test):
    
    # Feed forward through the network
    A,H,y_hat =self.forward_pro(X_test,self.W,self.b)
    
    y_pred = np.argmax(y_hat, axis=1)
    
    # Calculate accuracy
    acc = np.mean(y_pred == y_test)
    # Calculate accuracy
  
    return acc

  #---------------------------Cross Entropy Function----------------------------
  def cross_entropy(self,y_hat,Y):

      epsilon = 1e-9
      y_hat = np.maximum(y_hat, epsilon) # to avoid invalid divide

      sum=0.0;
      for i in range(0,len(Y)):
        sum+=(-np.log2(y_hat[i][Y[i]]))
      sum/= float(len(Y))

      return sum
  
  #-------------------------Stochastic Gradient Descent-------------------------

  def sgd(self,step_size,batch_size,epoch,reg=0.9):

    #-----------------------Number of batches-----------------------------------
    N = int(len(self.train_data)/batch_size)
    self.batch_size = batch_size
    self.reg =reg
    rate = step_size

    for e in range(0,epoch):
      step_size=rate/(e+1)        # Learning Rate Updation
      
      for k in range(0,N):

          # -------------------Create  Batch of particular size-----------------
          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #---------------Compute A,H,y_hat-------------------------------------
          A,H,y_hat=self.forward_pro(minibatch,self.W,self.b)

          #---------------Compute dW ,dw using back_propogation-----------------
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)

          #-------------------------Update W and b------------------------------
          self.b =self.subtract_matrices(self.b,db,step_size)
          self.W =self.subtract_matrices(self.W,dW,step_size)
          
      # Calculate validation Loss,validation Accuracy , Training_loss , Training Accuracy    

      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)

      #-------Update values To Wandb------

      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})

  #-------------------------Momentum based gradient descent---------------------

  def mbgd(self,step_size,batch_size,epoch,beta=0.9,reg=0.005):

    #-----------------------Number of batches-----------------------------------

    N = int(len(self.train_data)/batch_size)
    self.batch_size = batch_size
    self.reg =reg

    prev_ub , prev_uw =[],[]

    #---------------Initilalize All matrix with 0-------------------------------

    for i in range(len(self.W)):
      prev_ub.append(np.zeros((self.b[i].shape[0],self.b[i].shape[1])))
      prev_uw.append(np.zeros((self.W[i].shape[0],self.W[i].shape[1])))

    
    rate = step_size
    for e in range(0,epoch):
      step_size=rate/(e+1)
      start_time = time.time()
      beta_t=beta
      for k in range(0,N):
          ub,uw = list(prev_ub),list(prev_uw)

          #------------------------Create Minibatch data------------------------
          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #--------calculate dW ,db using forward and backword propogation------
          A,H,y_hat=self.forward_pro(minibatch,self.W,self.b)
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)

          #-----------------------weight update---------------------------------
          for i in range(len(self.W)):
            ub[i]= beta_t*prev_ub[i] + db[i]
            uw[i]= beta_t*prev_uw[i] + dW[i]
          self.b =self.subtract_matrices(self.b,ub,step_size)
          self.W =self.subtract_matrices(self.W,uw,step_size)

          prev_ub , prev_uw = list(ub),list(uw)

      # Calculate val_accuracy ,val_loss ,training accuracy ,training loss
      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      #---------Calculate perticular loss----------------
      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)

      #------------------------Update to Wandb----------------------------------
      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})

  #-------------------Nesterov Accelerated gradient descent---------------------    
  def nagd(self,step_size,batch_size,epoch,beta=0.9,reg=0.005):

    #-----------------------Number of batches-----------------------------------

    N = int(len(self.train_data)/batch_size)
    self.batch_size = batch_size
    self.reg =reg

    #---------------Initilalize All matrix with 0-------------------------------

    prev_ub , prev_uw =[],[]

    for i in range(len(self.W)):
      prev_ub.append(np.zeros((self.b[i].shape[0],self.b[i].shape[1])))
      prev_uw.append(np.zeros((self.W[i].shape[0],self.W[i].shape[1])))


    rate = step_size
    for e in range(0,epoch):
      beta_t=beta
      step_size=rate/(e+1)           #learning rate updation
      start_time = time.time()
      for k in range(0,N):
          ub,uw = list(prev_ub),list(prev_uw)
          n_w ,n_b =self.subtract_matrices(self.W,prev_uw,beta_t),self.subtract_matrices(self.b,prev_ub,beta_t)

          #------------------------Create Minibatch data------------------------

          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #--------calculate dW ,db using forward and backword propogation------
          A,H,y_hat=self.forward_pro(minibatch,n_w,n_b)
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)

          #-----------------------weight update---------------------------------

          for i in range(len(self.W)):
            ub[i]= beta_t*prev_ub[i] + db[i]
            uw[i]= beta_t*prev_uw[i] + dW[i]
          self.b =self.subtract_matrices(self.b,ub,step_size)
          self.W =self.subtract_matrices(self.W,uw,step_size)

          prev_ub , prev_uw = list(ub),list(uw)
      
      # Calculate val_accuracy ,val_loss ,training accuracy ,training loss

      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)

      #------------------------Update to Wandb----------------------------------
      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})

  def rmsprop(self,step_size,batch_size,epoch,beta=0.9,reg=0.005,epsilon=1e-10):
    
    #-----------------------Number of batches-----------------------------------

    N = int(len(self.train_data)/batch_size)

    self.batch_size = batch_size
    self.reg =reg

    ub , uw =[],[]

    #---------------Initilalize All matrix with 0-------------------------------
    for i in range(len(self.W)):
      ub.append(np.zeros((self.b[i].shape[0],self.b[i].shape[1])))
      uw.append(np.zeros((self.W[i].shape[0],self.W[i].shape[1])))


    rate = step_size
    for e in range(0,epoch):

      # Learning Rate Update
      step_size=rate/(e+1)      
      
      beta_t = beta
      for k in range(0,N):
         
          #------------------------Create Minibatch data------------------------
          
          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #--------calculate dW ,db using forward and backword propogation------
          
          A,H,y_hat=self.forward_pro(minibatch,self.W,self.b)
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)

          #-----------------------weight update---------------------------------
          
          for i in range(len(self.W)):
            ub[i]= beta_t*ub[i] + (1-beta_t)*(db[i]**2)
            uw[i]= beta_t*uw[i] + (1-beta_t)*(dW[i]**2)
          
          for i in range(len(self.W)):
            result_b = self.b[i] - step_size*db[i]/(np.sqrt(ub[i])+epsilon)
            result_w = self.W[i] - step_size*dW[i]/(np.sqrt(uw[i])+epsilon)
            self.b[i]=result_b
            self.W[i]=result_w

      #Calculate val_accuracy ,val_loss ,training accuracy ,training loss
      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      #---------Calculate perticular loss---------------------------------------
      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)
      
      #------------------------Update to Wandb----------------------------------
      
      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})
      
  
  def adam(self,step_size,batch_size,epoch,beta1=0.9,beta2=0.999,reg=0.005,epsilon=1e-4):

    #-----------------------Number of batches-----------------------------------

    N = int(len(self.train_data)/batch_size)

    self.batch_size = batch_size
    self.reg =reg
    rate = step_size
    vb , vw =[],[]

    #---------------Initilalize All matrix with 0-------------------------------

    for i in range(len(self.W)):
      vb.append(np.zeros((self.b[i].shape[0],self.b[i].shape[1])))
      vw.append(np.zeros((self.W[i].shape[0],self.W[i].shape[1])))

    mw=list(vw)
    mb=list(vb)

    
    for e in range(0,epoch):

      # update learning rate
      step_size=rate/(e+1)            
      beta1_t,beta2_t = beta1,beta2
      
      for k in range(0,N):
         
          #------------------------Create Minibatch data------------------------
          
          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #--------calculate dW ,db using forward and backword propogation------
          
          A,H,y_hat=self.forward_pro(minibatch,self.W,self.b)
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)

          #-----------------------weight update---------------------------------
          
          for i in range(len(self.W)):
            mw[i]=  beta1_t*mw[i] + (1-beta1_t)*dW[i]
            mb[i]=  beta1_t*mb[i] + (1-beta1_t)*db[i]
            vb[i]= beta2_t*vb[i] + (1-beta2_t)*db[i]**2
            vw[i]= beta2_t*vw[i] + (1-beta2_t)*dW[i]**2

            mw_hat=mw[i]/(1-np.power(beta1_t,e+1))
            mb_hat=mb[i]/(1-np.power(beta1_t,e+1))
            vw_hat=vw[i]/(1-np.power(beta2_t,e+1))
            vb_hat=vb[i]/(1-np.power(beta2_t,e+1))
          
            result_b = self.b[i] - step_size*mb_hat/(np.sqrt(vb_hat)+epsilon)
            result_w = self.W[i] - step_size*mw_hat/(np.sqrt(vw_hat)+epsilon)
            self.b[i]=result_b
            self.W[i]=result_w

      # Calculate val_accuracy ,val_loss ,training accuracy ,training loss

      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)

      #------------------------Update values to Wandb----------------------------------
      
      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})
  
  def nadam(self,step_size,batch_size,epoch,beta1=0.9,beta2=0.999,reg=0.005,epsilon=1e-4):

    #-----------------------Number of batches-----------------------------------

    N = int(len(self.train_data)/batch_size)
    self.batch_size = batch_size
    self.reg =reg
    rate = step_size
    vb , vw =[],[]

    #---------------Initilalize vb ,vw matrix with 0-------------------------------

    for i in range(len(self.W)):
      vb.append(np.zeros((self.b[i].shape[0],self.b[i].shape[1])))
      vw.append(np.zeros((self.W[i].shape[0],self.W[i].shape[1])))

    mw=list(vw)
    mb=list(vb)

    
    for e in range(0,epoch):
      step_size=rate/(e+1)            # update learning rate

      beta1_t,beta2_t = beta1,beta2
      
      for k in range(0,N):
         
          #------------------------Create Minibatch data------------------------
          
          minibatch = self.train_data[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]
          minibatch_lable=self.train_label[k*batch_size:min(k*batch_size+batch_size,len(self.train_data))]

          #--------calculate dW ,db using forward and backword propogation------
          
          A,H,y_hat=self.forward_pro(minibatch,self.W,self.b)
          dW,db = self.back_prop(minibatch,minibatch_lable,A,H,y_hat)
          
          #-----------------------weight update---------------------------------
          
          for i in range(len(self.W)):
            mw[i]=  beta1_t*mw[i] + (1-beta1_t)*dW[i]
            mb[i]=  beta1_t*mb[i] + (1-beta1_t)*db[i]
            vb[i]= beta2_t*vb[i] + (1-beta2_t)*db[i]**2
            vw[i]= beta2_t*vw[i] + (1-beta2_t)*dW[i]**2

            mw_hat=mw[i]/(1-np.power(beta1_t,e+1))
            mb_hat=mb[i]/(1-np.power(beta1_t,e+1))
            vw_hat=vw[i]/(1-np.power(beta2_t,e+1))
            vb_hat=vb[i]/(1-np.power(beta2_t,e+1))
          
            result_w = self.W[i] -(step_size/np.sqrt(vw_hat+epsilon))*(beta1_t*mw_hat+(1-beta1_t)*dW[i]/(1-beta1_t**(e+1)))
            result_b = self.b[i] -(step_size/np.sqrt(vb_hat+epsilon))*(beta1_t*mb_hat+(1-beta1_t)*db[i]/(1-beta1_t**(e+1)))
            self.b[i]=result_b
            self.W[i]=result_w
      
      # Calculate val_accuracy ,val_loss ,training accuracy ,training loss

      A,H,y_hat=self.forward_pro(self.validation_data,self.W,self.b)
      A,H,train_hat=self.forward_pro(self.train_data,self.W,self.b)

      validation_loss = 0
      train_loss=0

      if(self.loss=="cross_entropy"):
        validation_loss=self.cross_entropy(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)
      if(self.loss=="MSE"):
        validation_loss=self.mean_squared_error(y_hat,self.validation_label)
        train_loss= self.cross_entropy(train_hat,self.train_label)

      train_acc = self.accuracy(self.validation_data,self.validation_label)
      validation_accuracy =self.accuracy(self.validation_data,self.validation_label)

      #------------------------Update to Wandb----------------------------------
      
      wandb.log({"validation_accuracy": validation_accuracy})
      wandb.log({"validation_loss": validation_loss})  
      wandb.log({"train_accuracy":train_acc})
      wandb.log({"training_loss":train_loss})

  # compute matrix and return result according to activation parameter
  def activation_fun(self,matrix):

      if(self.activation=="sigmoid"):
        return self.sigmoid(matrix)

      elif(self.activation=="tanh"):
        return self.tanh(matrix)

      elif(self.activation=="ReLU"):
        return self.relu(matrix)
  
  # compute matrix and return result according to activation parameter
  def activation_derivative(self,matrix):

      if(self.activation=="sigmoid"):
        return self.sigmoid_derivative(matrix)

      elif(self.activation=="tanh"):
        return self.tanh_derivative(matrix)

      elif(self.activation=="ReLU"):
        return self.relu_derivative(matrix)



import argparse

parser = argparse.ArgumentParser(description='Training script for neural network.')

parser.add_argument('-wp', '--wandb_project', type=str, default='myprojectname', help='Project name used to track experiments in Weights & Biases dashboard')
parser.add_argument('-we', '--wandb_entity', type=str, default='myname', help='Wandb Entity used to track experiments in the Weights & Biases dashboard.')
parser.add_argument('-d', '--dataset', type=str, default='fashion_mnist', choices=['mnist', 'fashion_mnist'], help='Dataset to use for training')
parser.add_argument('-e', '--epochs', type=int, default=10, help='Number of epochs to train neural network.')
parser.add_argument('-b', '--batch_size', type=int, default=16, help='Batch size used to train neural network.')
parser.add_argument('-l', '--loss', type=str, default='cross_entropy', choices=['MSE', 'cross_entropy'], help='Loss function used to train neural network.')
parser.add_argument('-o', '--optimizer', type=str, default='nadam', choices=['sgd', 'momentum', 'nag', 'rmsprop', 'adam', 'nadam'], help='Optimizer used to train neural network.')
parser.add_argument('-lr', '--learning_rate', type=float, default=0.0001, help='Learning rate used to optimize model parameters')
parser.add_argument('-m', '--momentum', type=float, default=0.9, help='Momentum used by momentum and nag optimizers.')
parser.add_argument('-beta', '--beta', type=float, default=0.9, help='Beta used by rmsprop optimizer')
parser.add_argument('-beta1', '--beta1', type=float, default=0.9, help='Beta1 used by adam and nadam optimizers.')
parser.add_argument('-beta2', '--beta2', type=float, default=0.999, help='Beta2 used by adam and nadam optimizers.')
parser.add_argument('-eps', '--epsilon', type=float, default=0.000001, help='Epsilon used by optimizers.')
parser.add_argument('-w_d', '--weight_decay', type=float, default=0.005, help='Weight decay used by optimizers.')
parser.add_argument('-w_i', '--weight_init', type=str, default='Xavier', choices=['random', 'Xavier'], help='Weight initialization method used to initialize model parameters.')
parser.add_argument('-nhl', '--num_layers', type=int, default=5, help='Number of hidden layers used in feedforward neural network.')
parser.add_argument('-sz', '--hidden_size', type=int, default=128, help='Number of hidden neurons in a feedforward layer.')
parser.add_argument('-a', '--activation', type=str, default='tanh', choices=[ 'sigmoid', 'tanh', 'ReLU'], help='Activation function used in feedforward neural network.')

args = parser.parse_args()



# This will train Neural Network with best of configuration and
# give ouput y_hat for test_data

# Define best configuration from experiments
config_default={
    'weight_init':args.weight_init,
    'hidden_layers':args.num_layers,
    'size_of_layer':args.hidden_size,
    'activation':args.activation,
    'optimizer':args.optimizer,
    'learning_rate':args.learning_rate,
    'epoch':args.epochs,
    'batch_size':args.batch_size,
    'weight_decay':args.weight_decay
    }


(train_data, train_labels), (test_data, test_labels) = fashion_mnist.load_data()

if (args.dataset=="mnist"):
  (train_data, train_labels), (test_data, test_labels) = mnist.load_data()




Net = neural_network(train_data,train_labels,test_data,test_labels)

# Fit the model with perticular configuration
wandb.init(project = args.wandb_project ,name =args.wandb_entity,config=config_default)
config = wandb.config 
Net.train(epoch=config.epoch, hidden_layers=config.hidden_layers, size_of_layer=config.size_of_layer, batch_size=config.batch_size, activation=config.activation, optimizer=config.optimizer, weight_init=config.weight_init, learning_rate=config.learning_rate, weight_decay=config.weight_decay,momentum=args.momentum,beta=args.beta,beta1=args.beta1,beta2=args.beta2,epsilon=args.epsilon,loss=args.loss)


# generate labels for test_data
y_pred=Net.predict(Net.test_data)  

# get true labels of test data
y_true = Net.test_labels

import plotly.graph_objs as go

# This code will plot Confusion matrix

# Define the confusion matrix and class labels
cm = confusion_matrix(y_true, y_pred)
classes = ["T-Shirt/Top","Trouser","Pullover","Dress","Shirts","Sandal","Coat","Sneaker","Bag","Ankle boot"]

if(args.dataset=='mnist'):
  classes = ["0","1","2","3","4","5","6","7","8","9"]


# Calculate the percentages
percentages = (cm / np.sum(cm)) * 100

# Define the text for each cell
cell_text = []
for i in range(len(classes)):
    row_text = []
    for j in range(len(classes)):

        txt = "Total "+f'{cm[i, j]}<br>Per. ({percentages[i, j]:.3f})'
        if(i==j):
          txt ="Correcty Predicted " +classes[i]+"<br>"+txt
        if(i!=j):
          txt ="Predicted " +classes[j]+" For "+classes[i]+"<br>"+txt
        row_text.append(txt)
    cell_text.append(row_text)

# Define the trace
trace = go.Heatmap(z=percentages,
                   x=classes,
                   y=classes,
                   colorscale='Blues',
                   colorbar=dict(title='Percentage'),
                   hovertemplate='%{text}%<extra></extra>',
                   text=cell_text,
                   )

# Define the layout
layout = go.Layout(title='Confusion Matrix',
                   xaxis=dict(title='Predicted Classes'),
                   yaxis=dict(title='True Classes'),
                   )

# Plot the figure
fig = go.Figure(data=[trace], layout=layout)
wandb.log({'confusion_matrix': (fig)})