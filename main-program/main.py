import cv2
import numpy as np
import scipy
from scipy.misc import imread
import cPickle as pickle
import random
import os
import matplotlib.pyplot as plt

def extract_features(image_path, vector_size=32):
    image = imread(image_path, mode="RGB")
    try:
        # descriptor KAZE karena sudah tersedia di dalam pustaka OpenCV
        alg = cv2.KAZE_create()
        # binding image keypoints
        kps = alg.detect(image)
        # sorting based on keypoint response value (bigger is better)
        kps = sorted(kps, key=lambda x: -x.response)[:vector_size]
        # computing descriptors vector
        kps, dsc = alg.compute(image, kps)
        # flatten all of them in one big vector - our feature vector
        dsc = dsc.flatten()
        # making descriptor of same size 32x64=2048
        needed_size = (vector_size * 64)
        if dsc.size < needed_size:
            # if we have less the 32 descriptors then just adding zeros at the
            # end of our feature vector
            dsc = np.concatenate([dsc, np.zeros(needed_size - dsc.size)])
    except cv2.error as e:
        print 'Error: ', e
        return None

    return dsc

def batch_extractor(images_path, pickled_db_path="features.pck"):
    files = [os.path.join(images_path, p) for p in sorted(os.listdir(images_path))]

    result = {}
    for f in files:
        print 'Extracting features from image %s' % f
        name = f.split('/')[-1].lower()
        result[name] = extract_features(f)
    
    # saving all our feature vectors in pickled file
    with open(pickled_db_path, 'w') as fp:
        pickle.dump(result, fp)

class Matcher(object):

    def __init__(self, pickled_db_path="features.pck"):
        with open(pickled_db_path) as fp:
            self.data = pickle.load(fp)
        self.names = []
        self.matrix = []
        for k, v in self.data.iteritems():
            self.names.append(k)
            self.matrix.append(v)
        self.matrix = np.array(self.matrix)
        self.names = np.array(self.names)

    def cos_cdist(self, vector):
        # getting cosine distance between search image and images database
        v = vector.reshape(1, -1)
        return scipy.spatial.distance.cdist(self.matrix, v, 'cosine').reshape(-1)

    def match(self, image_path, topn=10):
        features = extract_features(image_path)
        img_distances = self.cos_cdist(features)
        # getting top 10 records
        nearest_ids = np.argsort(img_distances)[:topn].tolist()
        nearest_img_paths = self.names[nearest_ids].tolist()

        return nearest_img_paths, img_distances[nearest_ids].tolist()

    def euclidean_distance(x, y):
        distance = math.sqrt(sum([(a - b) ** 2 for a, b in zip(x, y)]))
        return distance

    def cosine_similarity(x, y):
        similarity = sum([(a * b) for a, b in zip(x, y)]) / (math.sqrt(sum([a ** 2 for a in x])) * math.sqrt(sum([b ** 2 for b in y])))
        return similarity

def show_img(path):
    img = imread(path, mode="RGB")
    plt.imshow(img)
    plt.show()
    
def run():
    images_path = '../resources/images/'
    files = [os.path.join(images_path, p) for p in sorted(os.listdir(images_path))]
    # getting 1 random images
    sample = random.sample(files, 1)

    # extraxt images from resources
    #batch_extractor(images_path)

    ma = Matcher('features.pck')
    
    for s in sample:
        print 'Query image =========================================='
        show_img(s)
        names, match = ma.match(s, topn=10)
        print 'Result images ========================================'
        for i in range(10):
            # we got cosine distance, less cosine distance between vectors
            # more they similar, thus we subtruct it from 1 to get match value
            print 'Match %s' % (1-match[i])
            show_img(os.path.join(images_path, names[i]))

run()