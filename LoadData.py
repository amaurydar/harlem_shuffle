__author__ = 'Arthur'
from common import data
import pickle
import numpy as np
import time

sample_length=1
sample_step=10

class Stockage:

    def __init__(self):
        self.X=[]
        self.Y=[]
        self.hourIndex=[]
        self.timeS=[]

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

def dataSeg(segment, y=-1, hourIndex=-1, f=dataSample):

    duration=int(segment.duration)

    stockage=Stockage()

    for t in range(0, duration-sample_length, sample_step):

        sample=segment[segment.point(t):segment.point(t+sample_length)]
        sample.loadData()

        stockage.X.append(f(sample))
        stockage.Y.append(y)
        stockage.hourIndex.append(hourIndex)
        stockage.timeS.append(segment.tts-t)

    return stockage

class Info:

    def __init__(self, race='Dog', num=1):
        self.race=race
        self.num=num
        self.subject=0
        self.data=Stockage()

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

        for n,hourSeg in enumerate(self.subject.segments):
            timestamp=time.time()

            y=0
            if hourSeg.type=='preictal':
                y=1
            elif hourSeg.type=='test':
                y=-1
                break # to delete for submitions

            temp=dataSeg(hourSeg, y, n, f)

            self.data.X=self.data.X+temp.X
            self.data.Y=self.data.Y+temp.Y
            self.data.hourIndex=self.data.hourIndex+temp.hourIndex
            self.data.timeS=self.data.timeS+temp.timeS

            print "Temps hourSegment: "+str(time.time()-timestamp)+" - type = "+str(y)
