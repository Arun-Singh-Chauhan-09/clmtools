import numpy, random, os, config

from sklearn.svm import SVR
from sklearn import preprocessing
from os import listdir
from os.path import isfile, join
from PIL import Image

data_folder = config.data_folder

def getScoring(data, mean):
	"""
	Create a logistic regression filter for scoring how close the tracking is to the face
	"""

	positives = []
	negatives = []
	
	scoringmodelWidth = 20
	scoringmodelHeight = 22

	# get how large window to crop, based on meandata
	mins = numpy.amin(mean, axis=0)
	maxs = numpy.amax(mean, axis=0)
	mean_width = int(round(maxs[0]-mins[0]))
	mean_height = int(round(maxs[1]-mins[1]))
	mins = mins+numpy.array([float(mean_width/4.5) , -float(mean_height)/12])
	maxs = maxs+numpy.array([-float(mean_width/4.5) , -float(mean_height)/6])
	
	# load positive examples
	i = 0
	print "getting positive examples from face images"
	for filename, values in data.iteritems():
		im = Image.open(join(data_folder, "cropped/", filename), "r")
		
		# convert image to grayscale
		im = im.convert("L")
		
		imins = mins + numpy.array(im.size)/2
		imaxs = maxs + numpy.array(im.size)/2
		
		p_crop = im.crop(( int(round(imins[0])), int(round(imins[1])), int(round(imaxs[0])), int(round(imaxs[1])) ))
		
		# reduce resolution 
		p_crop = p_crop.resize((scoringmodelWidth,scoringmodelHeight),Image.BILINEAR)

		# do log of images
		p_crop = numpy.log(numpy.array(p_crop, dtype=numpy.uint16)+1.0)
		#p_crop = numpy.array(p_crop)
		
		p_crop_img = Image.fromarray((normalize(p_crop)*255.).astype("uint8"))
		p_crop_img.save(join(data_folder, "pcropped/", filename+"_mask.bmp"))

		positives.append(p_crop.flatten())
						
		if i % 1000 == 0:
			print i	
		i += 1
	
	print "getting negative examples from face images"
	# get negative examples from face images
	negfiles = [f for f in listdir(join(data_folder , "images/")) if isfile(join(data_folder, "images/",f))]
	for filename in negfiles:
		if filename.endswith(".jpg") or filename.endswith(".png"):
			im = Image.open(join(data_folder, "images/", filename), "r")
			im = im.convert("L")
			ranwidth = int(round(im.size[0]*0.3))
			ranheight = int(round(im.size[1]*0.3))
			for nr in range(0,1):

				x = random.randint(0, int(round(im.size[0]-ranwidth)))
				y = random.randint(0, int(round(im.size[1]-ranheight)))
				rpoints = numpy.array([x,y])
				p_crop = im.crop((rpoints[0], rpoints[1], rpoints[0]+ranwidth, rpoints[1]+ranheight))
				# reduce resolution 
				p_crop = p_crop.resize((scoringmodelWidth,scoringmodelHeight),Image.BILINEAR)
				# do log of images
				p_crop2 = numpy.log(numpy.array(p_crop, dtype=numpy.uint16)+1)
				#p_crop2 = numpy.array(p_crop)
				
				p_crop_img = Image.fromarray((normalize(p_crop2)*255.).astype("uint8"))
				p_crop_img.save(join(data_folder, "pcropped/", "neg_"+filename+"_mask.bmp"))

				negatives.append(p_crop2.flatten())

	print "getting negative examples from landscape images"
	# get negative examples from landscape images
	negfiles = [f for f in listdir( join(data_folder, "negatives/")	 ) if isfile( join(data_folder, "negatives/",f) )]
	for filename in negfiles:
		im = Image.open( join(data_folder, "negatives/", filename) , "r")
		im = im.convert("L")
		for nr in range(0,10):
			x = random.randint(0, im.size[0]-mean_width)
			y = random.randint(0, im.size[1]-mean_height)
			rpoints = numpy.array([x,y])
			p_crop = im.crop((rpoints[0], rpoints[1], rpoints[0]+mean_width, rpoints[1]+mean_height))
			# reduce resolution 
			p_crop = p_crop.resize((scoringmodelWidth,scoringmodelHeight),Image.BILINEAR)
			# do log of images
			p_crop = numpy.log(numpy.array(p_crop, dtype=numpy.uint16)+1)
			#p_crop = numpy.array(p_crop)
			
			p_crop_img = Image.fromarray((normalize(p_crop)*255.).astype("uint8"))
			p_crop_img.save(join(data_folder, "pcropped/", "neg_"+filename+"_mask.bmp"))
				
			negatives.append(p_crop.flatten())

	# normalize image data to 0,1 interval
	
	#positives = [normalize(p) for p in positives]
	#negatives = [normalize(n) for n in negatives]
	
	positives = [preprocessing.scale(p) for p in positives]
	negatives = [preprocessing.scale(n) for n in negatives]
	
	
	# TODO : this should be set automatically?

	#testpos = positives[750:]
	#testlabels = [1.0 for p in testpos]
	#testlabels.extend([0.0 for n in negatives[700:800]])
	#testlabels = numpy.array(testlabels)
	#testfeatures = [p.flatten() for p in testpos]
	#testfeatures.extend([n.flatten() for n in negatives[700:800]])
	#testfeatures = numpy.vstack(testfeatures)

	#positives = positives[0:750]
	negatives = negatives[0:800]

	labels = [1.0 for p in positives]
	labels.extend([-1.0 for n in negatives])
	labels = numpy.array(labels)
	features = [p.flatten() for p in positives]
	features.extend([n.flatten() for n in negatives])
	features = numpy.vstack(features)
	
	# TODO : this isn't used
	# since we have more negative samples than positive samples, we need to balance the set
	weights = []
	for l in labels:
		if l == 1:
			weights.append(1.)
		else:
			weights.append(float(len(positives))/float(len(negatives))*0.5)
	
	#arr = numpy.arange(features.shape[0])
	#numpy.random.shuffle(arr)
	#from sklearn.grid_search import GridSearchCV
	#from sklearn.metrics import mean_squared_error
	#clfg = GridSearchCV(SVR(kernel="linear"), {'C':[0.001, 0.0005, 0.0001], 'epsilon' : [0.1, 0.05]}, loss_func=mean_squared_error, verbose=100)
	#clfg.fit(features[arr,:], labels[arr])
	#print "lbp best params"+str(clfg.best_params_)
	#clf = clfg.best_estimator_
	
	print "starting SVM"
	# do svm
	clf = SVR(C=0.0005, epsilon = 0.1, kernel="linear")
	clf.fit(features, labels)
	
	# optionally store filters as normalized images, for validation
	#coefficients = clf.coef_
	#coefficients = ((normalize(-(coefficients+clf.intercept_)))*255.).astype("uint8")
	#coefficients = coefficients.reshape((scoringmodelHeight,scoringmodelWidth))
	#coefImg = Image.fromarray(coefficients)
	#coefImg.save( join(data_folder, "svmImages/", "svmScoring.bmp") )

	#errors = []
	#import math
	#for f in range(0,len(testfeatures)):
		#score = numpy.sum(features[f]*clf.coef_) + clf.intercept_
	#	score = clf.predict(testfeatures[f])
	#	errors.append(math.sqrt((testlabels[f]-score)**2))
	#print "mse:"+str(numpy.mean(errors))

	scoringModel = {}
	scoringModel['bias'] = clf.intercept_.tolist()[0]
	scoringModel['coef'] = clf.coef_.flatten().tolist()
	scoringModel['size'] = [scoringmodelWidth,scoringmodelHeight]

	return scoringModel

def normalize(data):
	max_data = numpy.max(data)
	min_data = numpy.min(data)
	if numpy.isnan(max_data) or numpy.isnan(min_data):
		import pdb;pdb.set_trace()
	data = data.astype(numpy.float32)
	if max_data-min_data == 0:
		normalized_data = numpy.zeros(data.shape)
	else:
		normalized_data = (data-min_data)/(max_data-min_data)
	return normalized_data