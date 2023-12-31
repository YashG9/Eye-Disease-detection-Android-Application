# -*- coding: utf-8 -*-
"""mitradeep sir project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1kKeT2Eqj-DzwdoMh-wWBShw-9izp3NZO
"""

!pip install tensorflow tensorflow-gpu

!pip list

import tensorflow as tf

import os

gpus =tf.config.experimental.list_physical_devices('CPU')

#INSTRUCTING CPU TO USE ONLY NEEDED AMOUNT OF GPU
gpus = tf.config.experimental.list_physical_devices('GPU')
for gpu in gpus:
  tf.config.experimental.set_memory_growth(gpu,True)

# EXTRACTING ZIP FILE CONTENT FROM GOOGLE DRIVE
from google.colab import drive

#drive.mount('/content/drive')

# Path to Google Drive
file_path = '/content/drive/MyDrive/retina_data/data.zip'

import zipfile
zip_file_path = '/content/drive/MyDrive/retina_data/data.zip'

# EXTRACTING THE DATA TO projectdata FOLDER
extract_dir = '/content/projectdata'

# Extract the zip file
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

import cv2
import imghdr  #this will check the file extensions
from matplotlib import pyplot as plt

data_dir ='projectdata'

#os.listdir(os.path.join(data_dir ,'ODIR-5K/ODIR-5K/Testing Images'))

image_exts =['jpeg','jpg','bmp','png']

#img =cv2.imread(os.path.join('projectdata','ODIR-5K','ODIR-5K','Testing Images','1004_left.jpg'))

plt.imshow(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
plt.show()

"""**LOAD DATA**"""

tf.data.Dataset.list_files    #it allows us to build pipelines

import numpy as np

tf.keras.utils.image_dataset_from_directory('projectdata',batch_size=100)

projectdata =tf.keras.utils.image_dataset_from_directory('projectdata')

data_iterator = projectdata.as_numpy_iterator()

batch =data_iterator.next()

batch[0].shape

batch[1]

fig , ax =plt.subplots(ncols =6,figsize =(20,20))
for idx , img in enumerate(batch[0][:6]):
  ax[idx].imshow(img.astype(int))
  ax[idx].title.set_text(batch[1][idx])

from tensorflow.keras.models import Sequential   #one more model is there Functional
from tensorflow.keras.layers import Conv2D , MaxPooling2D , Dense , Flatten , Dropout

model = Sequential()

"""**MODEL STARTS**"""

import random
from tqdm import tqdm
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import pandas as pd
import numpy as np
import cv2

df = pd.read_csv("/content/projectdata/full_df.csv")
df.head(3)

def has_cataract(text):
  if "cataract" in text :
    return 1
  else :
    return 0

df["left_cataract"] = df["Left-Diagnostic Keywords"].apply(lambda x : has_cataract(x))
df["right_cataract"] = df["Right-Diagnostic Keywords"].apply(lambda x : has_cataract(x))

left_cataract = df.loc[(df.C ==1) & (df.left_cataract == 1)]["Left-Fundus"].values
left_cataract[:15]

right_cataract = df.loc[(df.C ==1) & (df.right_cataract == 1)]["Right-Fundus"].values
right_cataract[:15]

print("Number of images in left cataract: {}".format(len(left_cataract)))
print("Number of images in right cataract: {}".format(len(right_cataract)))

left_normal = df.loc[(df.C ==0) & (df["Left-Diagnostic Keywords"] == "normal fundus")]["Left-Fundus"].sample(250,random_state=42).values
right_normal = df.loc[(df.C ==0) & (df["Right-Diagnostic Keywords"] == "normal fundus")]["Right-Fundus"].sample(250,random_state=42).values
right_normal[:15]

cataract = np.concatenate((left_cataract,right_cataract),axis=0)
normal = np.concatenate((left_normal,right_normal),axis=0)

print(len(cataract),len(normal))

from tensorflow.keras.preprocessing.image import load_img,img_to_array
dataset_dir = "/content/projectdata/preprocessed_images"
image_size=224
labels = []
dataset = []
def create_dataset(image_category,label):
    for img in tqdm(image_category):
        image_path = os.path.join(dataset_dir,img)
        try:
            image = cv2.imread(image_path,cv2.IMREAD_COLOR)
            image = cv2.resize(image,(image_size,image_size))
        except:
            continue

        dataset.append([np.array(image),np.array(label)])
    random.shuffle(dataset)
    return dataset

dataset = create_dataset(cataract,1)

len(dataset)

dataset = create_dataset(normal,0)

len(dataset)

import cv2
import imghdr
plt.figure(figsize=(12,7))
for i in range(10):
    sample = random.choice(range(len(dataset)))
    image = dataset[sample][0]
    category = dataset[sample][1]
    if category== 0:
        label = "Normal"
    else:
        label = "Cataract"
    plt.subplot(2,5,i+1)
    #plt.imshow(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    plt.imshow(image)
    plt.xlabel(label)
plt.tight_layout()

"""Dividing dataset int X features and Y target"""

x = np.array([i[0] for i in dataset]).reshape(-1,image_size,image_size,3)
y = np.array([i[1] for i in dataset])

from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2)

"""Model -"""

from tensorflow.keras.applications.vgg19 import VGG19
vgg = VGG19(weights="imagenet",include_top = False,input_shape=(image_size,image_size,3))

for layer in vgg.layers:
    layer.trainable = False

from tensorflow.keras import Sequential
from tensorflow.keras.layers import Flatten,Dense
model = Sequential()
model.add(vgg)
model.add(Flatten())
model.add(Dense(1,activation="sigmoid"))

model.summary()

model.compile(optimizer="adam",loss="binary_crossentropy",metrics=["accuracy"])

from tensorflow.keras.callbacks import ModelCheckpoint,EarlyStopping
checkpoint = ModelCheckpoint("vgg19.h5",monitor="val_accuracy",verbose=1,save_best_only=True,
                             save_weights_only=False,period=1)
earlystop = EarlyStopping(monitor="val_accuracy",patience=5,verbose=1)

history = model.fit(x_train,y_train,batch_size=32,epochs=100,validation_data=(x_test,y_test),
                    verbose=1,callbacks=[checkpoint,earlystop])

loss,accuracy = model.evaluate(x_test,y_test)
print("loss:",loss)
print("Accuracy:",accuracy)

from sklearn.metrics import confusion_matrix,classification_report,accuracy_score
#y_pred = model.predict_classes(x_test)
#predict_y=model.predict(x_test)
y_pred=(model.predict(x_test) > 0.5).astype("int32")

accuracy_score(y_test,y_pred)

print(classification_report(y_test,y_pred))

from mlxtend.plotting import plot_confusion_matrix
cm = confusion_matrix(y_test,y_pred)
plot_confusion_matrix(conf_mat = cm,figsize=(8,7),#class_names = ["Normal","Cataract"],
                      show_normed = True);

plt.style.use("ggplot")
fig = plt.figure(figsize=(12,6))
epochs = range(1,10)
plt.subplot(1,2,1)

plt.plot(epochs,history.history["accuracy"],"go-")
plt.plot(epochs,history.history["val_accuracy"],"ro-")
plt.title("Model Accuracy")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.legend(["Train","val"],loc = "upper left")

plt.subplot(1,2,2)
plt.plot(epochs,history.history["loss"],"go-")
plt.plot(epochs,history.history["val_loss"],"ro-")
plt.title("Model Loss")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.legend(["Train","val"],loc = "upper left")
plt.show()

plt.figure(figsize=(12,7))
for i in range(10):
    sample = random.choice(range(len(x_test)))
    image = x_test[sample]
    category = y_test[sample]
    pred_category = y_pred[sample]

    if category== 0:
        label = "Normal"
    else:
        label = "Cataract"

    if pred_category== 0:
        pred_label = "Normal"
    else:
        pred_label = "Cataract"

    plt.subplot(2,5,i+1)
    plt.imshow(image)
    plt.xlabel("Actual:{}\nPrediction:{}".format(label,pred_label))
    plt.tight_layout()

img = cv2.imread('fundus_normal.jpg')
plt.imshow(cv2.cvtColor(img , cv2.COLOR_BGR2RGB))
plt.show()

resize =tf.image.resize(img,(224,224))
plt.imshow(resize.numpy().astype(int))
plt.show()

yhat = model.predict(np.expand_dims(resize/224 ,0))

yhat

if yhat >0.5 :
  print(f'Predicted class is Cataract')
else :
  print(f'Predicted class is not Cataract')

"""**Functional API**"""

from keras.models import Model

#model = Model(inputs = x , outputs =[output1,output2])

from keras.layers import *

#x = Input(shape = (8,))

hidden1 = Dense(128 ,activation ='relu')(x)
hidden2 = Dense(64 ,activation ='relu')(hidden1)

output1 = Dense(1,activation='sigmoid')(hidden2)
output2 = Dense(1,activation='sigmoid')(hidden2)

model.summary()

from keras.utils import plot_model
plot_model(model,show_shapes= True)

def has_cataract(text):
  if "cataract" in text :
    return 1
  else :
    return 0

def has_diabetes(text):
  if "nonproliferative retinopathy" in text :
    return 1
  else :
    return 0

def has_glaucoma(text):
  if "glaucoma" in text :
    return 1
  else :
    return 0

def has_hypertension(text):
  if "hypertensive" in text :
    return 1
  else :
    return 0

def has_abnormality1(input):
  if "1" in input :
    return 1
  else :
    return 0

df["left_cataract"] = df["Left-Diagnostic Keywords"].apply(lambda x : has_cataract(x))
df["right_cataract"] = df["Right-Diagnostic Keywords"].apply(lambda x : has_cataract(x))

df["left_diabetes"] = df["Left-Diagnostic Keywords"].apply(lambda x : has_diabetes(x))
df["right_diabetes"] = df["Right-Diagnostic Keywords"].apply(lambda x : has_diabetes(x))

df["left_glaucoma"] = df["Left-Diagnostic Keywords"].apply(lambda x : has_glaucoma(x))
df["right_glaucoma"] = df["Right-Diagnostic Keywords"].apply(lambda x : has_glaucoma(x))

df["left_hypertension"] = df["Left-Diagnostic Keywords"].apply(lambda x : has_hypertension(x))
df["right_hypertension"] = df["Right-Diagnostic Keywords"].apply(lambda x : has_hypertension(x))

left_cataract = df.loc[(df.C ==1) & (df.left_cataract == 1)]["Left-Fundus"].values
left_cataract[:15]

right_cataract = df.loc[(df.C ==1) & (df.right_cataract == 1)]["Right-Fundus"].values
right_cataract[:15]

left_diabetes = df.loc[(df.D ==1) & (df.left_diabetes == 1)]["Left-Fundus"].values
left_diabetes[:15]

right_diabetes = df.loc[(df.D ==1) & (df.right_diabetes == 1)]["Right-Fundus"].values
right_diabetes[:15]

left_glaucoma = df.loc[(df.G ==1) & (df.left_glaucoma == 1)]["Left-Fundus"].values
left_glaucoma[:15]

right_glaucoma = df.loc[(df.G ==1) & (df.right_glaucoma == 1)]["Right-Fundus"].values
right_glaucoma[:15]

left_hypertension = df.loc[(df.H ==1) & (df.left_hypertension == 1)]["Left-Fundus"].values
left_hypertension[:15]

right_hypertension = df.loc[(df.H ==1) & (df.right_hypertension == 1)]["Right-Fundus"].values
right_hypertension[:15]

len(left_cataract), len(right_cataract)

len(left_diabetes) ,len(right_diabetes)

len(left_glaucoma) ,len(right_glaucoma)

len(left_hypertension) ,len(right_hypertension)

left_normal = df.loc[(df.C ==0) & (df["Left-Diagnostic Keywords"] == "normal fundus")]["Left-Fundus"].sample(1000,random_state=42).values
right_normal = df.loc[(df.C ==0) & (df["Right-Diagnostic Keywords"] == "normal fundus")]["Right-Fundus"].sample(1000,random_state=42).values

cataract = np.concatenate((left_cataract,right_cataract),axis=0)
glaucoma =np.concatenate((left_glaucoma ,right_glaucoma) ,axis =0)
diabetes = np.concatenate((left_diabetes,right_diabetes),axis=0)
hypertension = np.concatenate((left_hypertension,right_hypertension),axis=0)
normal = np.concatenate((left_normal,right_normal),axis=0)

from tensorflow.keras.preprocessing.image import load_img,img_to_array
dataset_dir = "/content/projectdata/preprocessed_images"
image_size=224
labels = []
dataset = []
def create_dataset(image_category,label):
    for img in tqdm(image_category):
        image_path = os.path.join(dataset_dir,img)
        try:
            image = cv2.imread(image_path,cv2.IMREAD_COLOR)
            image = cv2.resize(image,(image_size,image_size))
        except:
            continue

        dataset.append([np.array(image),np.array(label)])
    random.shuffle(dataset)
    return dataset

final_dataset = create_dataset(cataract,1)
final_dataset = create_dataset(normal,0)
final_dataset = create_dataset(diabetes,2)
final_dataset = create_dataset(glaucoma,3)
final_dataset = create_dataset(hypertension,4)

len(final_dataset)

dataset_cataract = create_dataset(cataract ,1)

len(dataset_cataract)

dataset_cataract = create_dataset(normal ,0)

len(dataset_cataract)

dataset_diabetes = create_dataset(diabetes ,2)

len(dataset_diabetes)

dataset_diabetes = create_dataset(normal ,0)

len(dataset_diabetes)

dataset_glaucoma = create_dataset(glaucoma ,3)

len(dataset_glucoma)

dataset_glaucoma = create_dataset(normal ,0)

len(dataset_glucoma)

dataset_hypertension = create_dataset(hypertension ,4)

len(dataset_hypertension)

dataset_hypertension = create_dataset(normal ,0)

len(dataset_hypertension)

import cv2
import imghdr
plt.figure(figsize=(12,7))
for i in range(5):
    sample = random.choice(range(len(dataset_cataract)))
    image = dataset_cataract[sample][0]
    category = dataset_cataract[sample][1]
    if category== 0:
        label = "Normal"
    else:
        label = "Cataract"
    plt.subplot(2,5,i+1)
    #plt.imshow(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    plt.imshow(image)
    plt.xlabel(label)
    plt.tight_layout()

plt.figure(figsize=(12,7))
for i in range(5):
    sample = random.choice(range(len(dataset_diabetes)))
    image = dataset_diabetes[sample][0]
    category = dataset_diabetes[sample][1]
    if category== 0:
        label = "Normal"
    else:
        label = "Diabetes"
    plt.subplot(2,5,i+1)
    #plt.imshow(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    plt.imshow(image)
    plt.xlabel(label)
    plt.tight_layout()

plt.figure(figsize=(12,7))
for i in range(5):
    sample = random.choice(range(len(dataset_glaucoma)))
    image = dataset_glaucoma[sample][0]
    category = dataset_glaucoma[sample][1]
    if category== 0:
        label = "Normal"
    else:
        label = "Glaucoma"
    plt.subplot(2,5,i+1)
    #plt.imshow(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    plt.imshow(image)
    plt.xlabel(label)
    plt.tight_layout()

plt.figure(figsize=(12,7))
for i in range(5):
    sample = random.choice(range(len(dataset_hypertension)))
    image = dataset_hypertension[sample][0]
    category = dataset_hypertension[sample][1]
    if category== 0:
        label = "Normal"
    else:
        label = "Hypertension"
    plt.subplot(2,5,i+1)
    #plt.imshow(cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
    plt.imshow(image)
    plt.xlabel(label)
    plt.tight_layout()

combined_dataset =dataset_cataract +dataset_diabetes + dataset_glaucoma +dataset_hypertension

x = np.array([i[0] for i in final_dataset]).reshape(-1,image_size,image_size,3)

for i in final_dataset:
  if([i[1]]==1):
    y1 = np.array([i[1]])
  elif(i[1]==2):
    y2 = np.array([i[1]])
  elif(i[1]==3):
    y3 = np.array([i[1]])
  elif(i[1]==4):
    y4 = np.array([i[1]])



y =[y1 ,y2 ,y3 ,y4]

len(final_dataset) ,len(x) , len(y) ,len(y1) ,len(y2) ,len(y3) , len(y4)

y.shape , y1.shape ,y2.shape , y3.shape , y4.shape

from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.2)

x_train.shape

from keras.applications.vgg19 import VGG19
from keras.layers import *
from keras.models import Model

vggnet =VGG19(include_top=False , input_shape=( 224, 224, 3))

vggnet.trainable =False

output = vggnet.layers[-1].output

flatten =Flatten()(output)

dense1= Dense(512 , activation ='relu')(flatten)
dense2= Dense(512 , activation ='relu')(dense1)

dense3= Dense(512 , activation ='relu')(flatten)
dense4= Dense(512 , activation ='relu')(dense3)

dense5= Dense(512 , activation ='relu')(flatten)
dense6= Dense(512 , activation ='relu')(dense5)

dense7= Dense(512 , activation ='relu')(flatten)
dense8= Dense(512 , activation ='relu')(dense7)

output1 = Dense(1,activation ='sigmoid' ,name ='cataract')(dense2)
output2 = Dense(1,activation ='sigmoid' ,name ='diabetes')(dense4)
output3 = Dense(1,activation ='sigmoid' ,name ='glaucoma')(dense6)
output4 = Dense(1,activation ='sigmoid' ,name ='hypertension')(dense8)

model= Model(inputs=vggnet.input ,outputs =[output1 ,output2,output3 ,output4])

model.summary()

from keras.utils import plot_model
plot_model(model)

import tensorflow as tf
from tensorflow.keras.losses import binary_crossentropy

model.compile(optimizer='adam',loss= binary_crossentropy ,metrics={'cataract' : 'binary_crossentropy','diabetes' :' binary_crossentropy' , 'glaucoma' :' binary_crossentropy' , 'hypertension' :' binary_crossentropy'})

import tensorflow as tf
from tensorflow.keras.losses import binary_crossentropy

#from tensorflow.keras.callbacks import ModelCheckpoint,EarlyStopping
#checkpoint = ModelCheckpoint("vgg19.h5",monitor="val_accuracy",verbose=1,save_best_only=True,
 #                            save_weights_only=False,period=1)
#earlystop = EarlyStopping(monitor="val_accuracy",patience=5,verbose=1)

history = model.fit(x_train,y_train,batch_size=32,epochs=15,validation_data=(x_test,y_test),
                    verbose=1,callbacks=[checkpoint,earlystop])

