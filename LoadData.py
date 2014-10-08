__author__ = 'Arthur'
from common import data
import pickle
import numpy as np
import time

class Stockage:

    def __init__(self):
        self.X=np.array([])
        self.Y=np.array([])
        self.hourIndex=[]
        self.timeS=[]

def split(data, n=2):
    r=[]
    for i in range(0, len(data)-n+1,n):
       r.append(sum(data[i:i+n])/n)

    return r

def dataSample(segment):

    x=np.array([])
    for i in range(16):
        s=segment.data[i]-np.mean(segment.data[i])
        temp=np.correlate(s, s, mode='full')
        x=np.concatenate( (x, temp[len(temp)/2:], np.log10(np.absolute(np.fft.rfft(s)[1:50]))), axis=0)

        for j in range(16):
            p=segment.data[j]-np.mean(segment.data[j])
            x=np.concatenate((x, np.correlate(s, p)), axis=0)

    return x

def dataSeg(segment, y=-1, hourIndex=-1, f=dataSample, sample_length=1, sample_step=10):

    duration=segment.duration

    stockage=Stockage()

    sample_points=int(sample_length*segment.length/segment.duration)
    sample_points_steps=int(sample_step*segment.length/segment.duration)

    stockage.X=np.empty(shape=[0, len( f(segment[:sample_points]) )])
    stockage.Y=np.empty(shape=[0,1])

    for t in range(0, segment.length-sample_points, sample_points_steps):

        sample=segment[t:t+sample_points]
        sample.loadData()

        #stockage.X.append(f(sample))
        #stockage.Y.append(y)

        stockage.X=np.append(stockage.X, f(sample), axis=0)
        stockage.Y=np.append(stockage.Y, np.array([[y]]), axis=0)

        stockage.hourIndex.append(hourIndex)
        stockage.timeS.append(segment.tts-segment.time(t))

    return stockage

class Info:

    def __init__(self, race='Dog', num=1):
        self.race=race
        self.num=num
        self.subject=0
        self.data=Stockage()

        self.setParam()

    def setParam(self, sample_length=1, sample_step=10, testData=False):
        self.sample_length=sample_length
        self.sample_step=sample_step
        self.testData=testData

    def saveFile(self, name):

        f=open(name+".pkl", 'wb')
        pickle.dump(self.data, f)
        f.close()

    def loadFile(self, name):

        f=open(name+".pkl", 'rb')
        self.data=pickle.load(f)
        f.close()

    def load(self, f=dataSample):
        self.subject=data.Subject(self.race, self.num)

        self.data=Stockage()

        self.data.X=0
        self.data.Y=0

        for n,hourSeg in enumerate(self.subject.segments):
            timestamp=time.time()

            y=0
            if hourSeg.type=='preictal':
                y=1
            elif hourSeg.type=='test':
                y=-1
                if self.testData==False:
                    break

            temp=dataSeg(hourSeg, y, n, f, self.sample_length, self.sample_step)

            #self.data.X=np.concatenate((self.data.X,temp.X), axis=0)
            #self.data.Y=np.concatenate((self.data.Y,temp.Y), axis=0)
            #self.data.hourIndex=np.concatenate((self.data.hourIndex,temp.hourIndex), axis=0)
            #self.data.timeS=np.concatenate((self.data.timeS,temp.timeS), axis=0)

            #self.data.X=self.data.X+temp.X
            #self.data.Y=self.data.Y+temp.Y

            if self.data.X==0:
                self.data.X=temp.X
                self.data.Y=temp.Y
            else:
                self.data.X=np.append(self.data.X, temp.X, axis=0)
                self.data.Y=np.append(self.data.Y, temp.Y, axis=0)

            self.data.hourIndex=self.data.hourIndex+temp.hourIndex
            self.data.timeS=self.data.timeS+temp.timeS

            print "Temps hourSegment ( "+str(n)+" ): "+str(time.time()-timestamp)+" ; type = "+str(y)+" ; npoints = "+str(len(temp.Y))
