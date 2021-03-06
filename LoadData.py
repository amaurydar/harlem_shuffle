__author__ = 'Arthur'
from common import data
import pickle
import numpy as np
import time

class Stockage:

    def __init__(self):
        self.X=np.array([[]])
        self.Y=np.array([])
        self.hourIndex=np.array([])
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

    start=True

    #stockage.X=np.empty(shape=[0, len( f(segment[:sample_points]) )])
    #stockage.Y=np.empty(shape=[0,1])

    for t in range(0, segment.length-sample_points, sample_points_steps):

        sample=segment[t:t+sample_points]
        sample.loadData()

        #stockage.X.append(f(sample))
        #stockage.Y.append(y)

        if start:
            stockage.X=np.array([f(sample)])
            stockage.Y=np.array([y])
            stockage.hourIndex=np.array([hourIndex])

            start=False
        else:
            stockage.X=np.append(stockage.X, np.array([f(sample)]), axis=0)
            stockage.Y=np.append(stockage.Y, y)
            stockage.hourIndex=np.append(stockage.hourIndex, hourIndex)

        if y==-1:
            stockage.timeS.append(0)
        else:
            stockage.timeS.append(segment.tts-segment.time(t))

    return stockage

class Info:

    def __init__(self, race='Dog', num=1):
        self.race=race
        self.num=num
        self.subject=0
        self.data=Stockage()

        self.setParam()

        self.norm_ntest=500
        self.norm_ntrain=100

    def setParam(self, sample_length=1, sample_step=10, testData=False):
        self.sample_length=sample_length
        self.sample_step_wanted=sample_step
        self.testData=testData

    def saveFile(self, name):

        f=open(name+".pkl", 'wb')
        pickle.dump(self.data, f)
        f.close()

    def loadFile(self, name):

        f=open(name+".pkl", 'rb')
        self.data=pickle.load(f)
        f.close()

    def load(self, f=dataSample, aff=False):

        self.subject=data.Subject(self.race, self.num)
        self.data=Stockage()

        self.ntest=0
        self.ntrain=0

        for seg in self.subject.segments:
            if seg.type=='test':
                self.ntest+=1
            else:
                self.ntrain+=1

        if self.testData:
            self.sample_step=1.0*self.sample_step_wanted*self.ntest/self.norm_ntest
        else:
            self.sample_step=1.0*self.sample_step_wanted*self.ntrain/self.norm_ntrain
        print "actual sample_step: " +str(self.sample_step)

        start=True

        for n,hourSeg in enumerate(self.subject.segments):
            timestamp=time.time()

            y=0
            if hourSeg.type=='preictal':
                y=1
            elif hourSeg.type=='test':
                y=-1
            else:
                y=0

            if ((self.testData==True and y==-1) or (self.testData==False and y!=-1)):

                temp=dataSeg(hourSeg, y, n, f, self.sample_length, self.sample_step)

                #self.data.X=np.concatenate((self.data.X,temp.X), axis=0)
                #self.data.Y=np.concatenate((self.data.Y,temp.Y), axis=0)
                #self.data.hourIndex=np.concatenate((self.data.hourIndex,temp.hourIndex), axis=0)
                #self.data.timeS=np.concatenate((self.data.timeS,temp.timeS), axis=0)

                #self.data.X=self.data.X+temp.X
                #self.data.Y=self.data.Y+temp.Y

                if start:
                    self.data.X=temp.X
                    self.data.Y=temp.Y
                    self.data.hourIndex=temp.hourIndex

                    start=False
                else:
                    self.data.X=np.append(self.data.X, temp.X, axis=0)
                    self.data.Y=np.append(self.data.Y, temp.Y)
                    self.data.hourIndex=np.append(self.data.hourIndex, temp.hourIndex)


                self.data.timeS=self.data.timeS+temp.timeS

                if aff:
                    print "Temps hourSegment ( "+str(n)+" ): "+str(time.time()-timestamp)+" ; type = "+str(y)+" ; npoints = "+str(len(temp.Y))
