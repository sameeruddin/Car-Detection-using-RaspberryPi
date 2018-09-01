#importing libraries
import tensorflow as tf
import sys
import os
import RPi.GPIO as GPIO
import time
import picamera
import os.path

#Creating images directory if doesn't exist
if not os.path.exists('./images'):
    os.makedirs('images')

#Intializing Pi camera
camera = picamera.PiCamera()

# Disable tensorflow compilation warnings
os.environ['TF_CPP_MIN_LOG_LEVEL']='2'

#Intializing an empty list
result=[]

#Setting up GPIO pins mode BOARD or BCM
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#Intializing variables for LED's & a Button
button =  2
led_green = 3
led_red = 4

#Intializing LED's & Button pin setup
GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led_green, GPIO.OUT)
GPIO.setup(led_red, GPIO.OUT)

#Turning OFF Green and Red LED's
GPIO.output(led_green,GPIO.LOW)
GPIO.output(led_red,GPIO.LOW)

#Intializing a function verify the first element ina list is a car or no_car
def verify():
	if len(result[0]) != 3:
		GPIO.output(led_red,GPIO.HIGH)
		print("Not a car \n")
		time.sleep(3)
		GPIO.output(led_red,GPIO.LOW)
	else:
		GPIO.output(led_green,GPIO.HIGH)
		print("It's a car \n")
		time.sleep(3)
		GPIO.output(led_green,GPIO.LOW)

#Intializing camera to capture picture and store it in images directory with timestamp
def capture_picture():
	camera.resolution = (640, 480)
	camera.start_preview()
	time.sleep(1)
	file_name = time.strftime('%d-%m-%Y_%H_%M')
	camera.capture('./images/%s.jpg'%file_name)
	camera.stop_preview()
	filepath = './images/'+file_name+'.jpg'
	return filepath;

#Classifying capture image with our retrained TensorFlow Inception model
def classification(picture):
	image_path = picture

	# Read the image_data
	image_data = tf.gfile.FastGFile(image_path, 'rb').read()
	# Loads label file, strips off carriage return
	label_lines = [line.rstrip() for line in tf.gfile.GFile("retrained_model/retrained_labels.txt")]

	# Unpersists graph from file
	with tf.gfile.FastGFile("retrained_model/retrained_graph.pb", 'rb') as f:
		graph_def = tf.GraphDef()
		graph_def.ParseFromString(f.read())
		_ = tf.import_graph_def(graph_def, name='')

	with tf.Session() as sess:
		# Feed the image_data as input to the graph and get first prediction
		softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
		predictions = sess.run(softmax_tensor, \
				{'DecodeJpeg/contents:0': image_data})

		# Sort to show labels of first prediction in order of confidence
		top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]
		for node_id in top_k:
			human_string = label_lines[node_id]
			score = predictions[0][node_id]
			result.append(human_string)
			print('%s (score = %.5f)' % (human_string, score))

print("Press the button to start the process \n")

#Intializing a Infinity loop to run the process
try:
	while (1):
		input_state = GPIO.input(button)
		if input_state == False:
			print('Execution Started \n')
			del result[:]
			img_path = capture_picture()
			print("Image is captured & its classification started... \n")
			if os.path.isfile(img_path) and os.access(img_path, os.R_OK):
				classification(img_path)
				print('<= Image Classification completed   => \n')
				verify()
				print("Press the button to start the process again \n")
			else:
				print("Image file is missing or is not readable \n")
except KeyboardInterrupt:
	GPIO.cleanup()
	print(' process execution Terminated\n')
