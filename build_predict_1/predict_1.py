# Copyright 2016 Niek Temme. 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Predict a handwritten integer (MNIST beginners).

Script requires
1) saved model (model.ckpt file) in the same location as the script is run from.
(requried a model created in the MNIST beginners tutorial)
2) one argument (png file location of a handwritten integer)

Documentation at:
http://niektemme.com/ @@to do
"""

#import modules
import sys
import tensorflow as tf
from PIL import Image,ImageFilter
import os
import datetime
from flask import Flask, request
import flask
from werkzeug import secure_filename
import logging

log = logging.getLogger()
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

def predictint(imvalue):
    """
    This function returns the predicted integer.
    The input is the pixel values from the imageprepare() function.
    """
    
    # Define the model (same as when creating the model file)
    x = tf.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))
    y = tf.nn.softmax(tf.matmul(x, W) + b)

    init_op = tf.global_variables_initializer()
    saver = tf.train.Saver()
    
    """
    Load the model.ckpt file
    file is stored in the same directory as this python script is started
    Use the model to predict the integer. Integer is returend as list.

    Based on the documentatoin at
    https://www.tensorflow.org/versions/master/how_tos/variables/index.html
    """
    with tf.Session() as sess:
        sess.run(init_op)
        saver.restore(sess, app.root_path + "/model.ckpt")
        #print ("Model restored.")
   
        prediction=tf.argmax(y,1)
        return prediction.eval(feed_dict={x: [imvalue]}, session=sess)

def imageprepare(argv):
    """
    This function returns the pixel values.
    The imput is a png file location.
    """
    im = Image.open(argv).convert('L')
    width = float(im.size[0])
    height = float(im.size[1])
    newImage = Image.new('L', (28, 28), (255)) #creates white canvas of 28x28 pixels
    
    if width > height: #check which dimension is bigger
        #Width is bigger. Width becomes 20 pixels.
        nheight = int(round((20.0/width*height),0)) #resize height according to ratio width
        if (nheight == 0): #rare case but minimum is 1 pixel
            nheight = 1
        # resize and sharpen
        img = im.resize((20,nheight), Image.ANTIALIAS).filter(ImageFilter.SHARPEN)
        wtop = int(round(((28 - nheight)/2),0)) #caculate horizontal pozition
        newImage.paste(img, (4, wtop)) #paste resized image on white canvas
    else:
        #Height is bigger. Heigth becomes 20 pixels. 
        nwidth = int(round((20.0/height*width),0)) #resize width according to ratio height
        if (nwidth == 0): #rare case but minimum is 1 pixel
            nwidth = 1
         # resize and sharpen
        img = im.resize((nwidth,20), Image.ANTIALIAS).filter(ImageFilter.SHARPEN)
        wleft = int(round(((28 - nwidth)/2),0)) #caculate vertical pozition
        newImage.paste(img, (wleft, 4)) #paste resized image on white canvas
    
    #newImage.save("sample.png")

    tv = list(newImage.getdata()) #get pixel values
    
    #normalize pixels to 0 and 1. 0 is pure white, 1 is pure black.
    tva = [ (255-x)*1.0/255.0 for x in tv] 
    return tva
    #print(tva)

def predict(argv):
    """
    Main function.
    """
    imvalue = imageprepare(argv)
    predint = predictint(imvalue)
    return predint[0] #first value in list

KEYSPACE = "mnist"

def createKeySpace():
    """
    The container of Cassandra is located at '172.17.0.2:9042'.
    the program acesses the Cassandra container and records information in the Cassandra.
    """
    # connect to the container
    cluster = Cluster(contact_points=['172.17.0.2'],port=9042)
    session = cluster.connect()

    log.info("Creating keyspace...")
    try:
        # create keyspace mnist
        session.execute("""
           CREATE KEYSPACE %s
           WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' }
           """ % KEYSPACE)

        log.info("setting keyspace...")
        session.set_keyspace(KEYSPACE)

        # create table mnist_predict
        log.info("creating table...")
        session.execute("""
           CREATE TABLE mnist_predict (
               file_name text,
               upload_time timestamp,
               prediction int,
               PRIMARY KEY (file_name)
           )
           """)

    except Exception as e:
       log.error("Unable to create keyspace")
       log.error(e)

createKeySpace();

def insertData(name, time, prediction):
    """
    Insert data to the table.
    """
    # access to the keyspace mnist
    cluster = Cluster(contact_points=['172.17.0.2'],port=9042)
    session = cluster.connect("mnist")

    try:
        # insert data
        log.info("insertData...")
        session.execute("""
               INSERT INTO mnist_predict (file_name, upload_time, prediction)
               VALUES (%s, %s, %s);
           """ % (name, time, prediction))

    except Exception as e:
        log.error("Unable to insert data")
        log.error(e)

app = Flask(__name__)
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bmp'])
app.config['UPLOAD_FOLDER'] = 'upload'
def allowed_file(filename):
    # judge whether the user submits the image format
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/mnist", methods=["POST"]) 
def mnist():
    """
    when users submit pictures to '0.0.0.0:8000/mnist',
    the program retruns users predictions and records them on Cassandra
    """
    req_time = datetime.datetime.now()

    if request.method == "POST":
        file = request.files['file']
        if file and allowed_file(file.filename):

            # get the upload time, the filename, the filepath and the prediction
            upload_filename = secure_filename((file).filename)
            save_filename = str(req_time).rsplit('.',1)[0] + ' ' + upload_filename
            save_filepath = os.path.join(app.root_path, save_filename)
            file.save(save_filepath)
            mnist_result = str(predict(save_filepath))

            insert_filename = '\'' + upload_filename + '\''
            insert_time = '\'' + str(req_time).rsplit('.',1)[0] + '\''
            
            # insert data to the Cassandra
            insertData(insert_filename, insert_time, mnist_result)

    # return the user with the information
    return ("%s%s%s%s%s%s%s%s%s" % ("Upload File Name: ", upload_filename, "\n", 
                                "Upload Time: ", req_time, "\n",
                                "Prediction: ", mnist_result, "\n"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
