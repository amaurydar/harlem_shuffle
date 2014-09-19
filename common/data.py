__author__ = 'amaury'

import json
import os
import scipy.io
import numpy as np
import time
import ntpath

class Segment(object):
    def __init__(self):
        pass

    def fromFile(self, filepath):
        if os.path.exists(filepath):
            self.filepathes = [filepath]

            mat = scipy.io.loadmat(filepath)
            name = None
            for a in mat.keys():
                if not '__' in a:
                    name = a
            self.duration = float(mat[name][0][0][1][0][0])
            self.slices = [slice(0, mat[name][0][0][0].shape[1])]
            try:
                self.seq_numbers = [int(mat[name][0][0][4][0][0])]
            except:
                self.seq_numbers = [None]
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'SETTINGS.json')) as f:
                settings = json.load(f)

            if 'preictal' in filepath:
                self.type = 'preictal'
            elif 'interictal' in filepath:
                self.type = 'interictal'
            elif 'test' in filepath:
                self.type = 'test'

            if 'Dog' in filepath:
                if self.type == 'preictal':
                    self.tts = float(settings['dog_pre_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif self.type == 'interictal':
                    self.tts = float(settings['dog_inter_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif self.type == 'test':
                    self.tts = None
            if 'Patient' in filepath:
                if self.type == 'preictal':
                    self.tts = float(settings['patient_pre_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif self.type == 'interictal':
                    self.tts = float(settings['patient_inter_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif self.type == 'test':
                    self.tts = None
            self.data = None


        else:
            raise Exception("incorrect filepath")

    def __add__(self, segment):
        res = Segment()
        res.filepathes = self.filepathes + segment.filepathes
        res.duration = self.duration + segment.duration
        res.slices = self.slices + segment.slices
        res.seq_numbers = self.seq_numbers + segment.seq_numbers
        res.data = None
        if self.data is not None and segment.data is not None:
            res.data = np.concatenate((self.data, segment.data), axis=1)
        res.tts = self.tts
        if self.type == segment.type:
            res.type = self.type
        else:
            raise Exception("trying to concatenate two segments of different type")
        return res

    def point(self, time):
        return int(time / self.duration * (sum(slice.stop - slice.start for slice in self.slices)))

    def time(self, point):
        return float(point) / sum(slice.stop - slice.start for slice in self.slices) * self.duration

    def __getitem__(self, s):
        start = s.start
        stop = s.stop
        if start is None:
            start = 0
        if stop is None:
            stop = sum([slice_.stop-slice_.start for slice_ in self.slices])
        if start<0:
            start = sum([slice_.stop-slice_.start for slice_ in self.slices])+start
        if stop<0:
            stop = sum([slice_.stop-slice_.start for slice_ in self.slices])+stop
        res = Segment()
        res.filepathes = []
        res.slices = []
        res.seq_numbers = []

        res.duration = float(stop - start) / (
        sum(slice_.stop - slice_.start for slice_ in self.slices)) * self.duration
        if self.data is not None:
            res.data = self.data[slice]
        else:
            res.data = None
        if self.tts is not None:
            res.tts = self.tts - float(start) / (
            sum([slice_.stop - slice_.start for slice_ in self.slices])) * self.duration
        else:
            res.tts = None
        res.type = self.type


        for filepath, slice_, seq_number in zip(self.filepathes, self.slices, self.seq_numbers):
            if (start<=slice_.start and slice_.start<stop) or (start<=(slice_.stop-1) and (slice_.stop-1)<stop):
                res.filepathes.append(filepath)
                start__ = max(start, 0)
                stop__ = min(stop, slice_.stop)
                res.slices.append(slice(start__, stop__))
                res.seq_numbers.append(seq_number)
            start -= slice_.stop - slice_.start
            stop -= slice_.stop - slice_.start

        return res

    def loadData(self):
        start_time = time.time()
        for filepath, _slice in zip(self.filepathes, self.slices):
            mat = scipy.io.loadmat(filepath)
            name = None
            for a in mat.keys():
                if not '__' in a:
                    name = a
            if self.data is None:
                self.data = mat[name][0][0][0][:,_slice]
            else:
                self.data = np.concatenate((self.data, mat[name][0][0][0][:,_slice]), axis = 1)
        print 'Loaded segment data in %s s' % round(time.time()-start_time, 1)

    def __str__(self):
        if self.data is None:
            res = 'Data not loaded \n'
        else:
            res = 'Data shape : %s \n' + str(self.data.shape)
        res += 'Duration : %s s\n' % round(self.duration, 3)
        res += 'Type : %s \n' % self.type
        res += 'Time to seizure : %s \n' % round(self.tts, 3)
        res += 'Data origin : \n'
        res += '\n'.join(['%s, %s:%s' % (ntpath.basename(fp), s.start, s.stop) for fp, s in zip(self.filepathes, self.slices)])
        return res

class Subject(object):
    def __init__(self, race, n):
        start_time = time.time()
        self.race = race
        self.n = n

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'LOCAL_SETTINGS.json')) as f:
            settings = json.load(f)
        self.dir = str(settings['data-dir']) + '/%s_%s' % (self.race, self.n)

        self.segments = []
        filecount = 0
        for type in ('preictal', 'interictal', 'test'):
            i = 1
            filepath = '%s/%s_%s_%s_segment_%04d.mat' % (self.dir, self.race, self.n, type, i)
            currentSegment = None
            previousSeq = -1

            while os.path.exists(filepath):
                filecount += 1
                segment = Segment()
                segment.fromFile(filepath)

                if segment.seq_numbers[0] is not None and segment.seq_numbers[0] == previousSeq + 1:
                    currentSegment += segment
                else:
                    if segment.seq_numbers[0] is not None and segment.seq_numbers[0] != 1:
                        print 'data missing - seq starting at more than 1'
                    if segment.seq_numbers[0] is not None and previousSeq != 6 and currentSegment is not None:
                        print 'data missing - seq stoping at less than 1'
                    if currentSegment is not None:
                        self.segments.append(currentSegment)
                    currentSegment = segment

                previousSeq = segment.seq_numbers[0]

                i += 1
                filepath = '%s/%s_%s_%s_segment_%04d.mat' % (self.dir, self.race, self.n, type, i)
            if currentSegment is not None:
                if segment.seq_numbers[0] is not None and previousSeq != 6:
                    print 'data missing - seq stoping at less than 1'
                self.segments.append(currentSegment)
        print '%s %s : read %s files into %s segments in %s s' % (self.race, self.n, filecount, len(self.segments), round(time.time()-start_time, 1))
    def __str__(self):
        stats = {'interictal' : {}, 'preictal' : {}, 'test' : {}}
        stats2 = {'interictal' : 0, 'preictal' : 0, 'test' : 0}
        for segment in self.segments:
            stats2[segment.type] += 1
            if segment.duration in stats[segment.type]:
                stats[segment.type][segment.duration] += 1
            else:
                stats[segment.type][segment.duration] = 1

        return ('%s %s \n' % (self.race, self.n) +
                '%s interictaux :  %s \n' % (stats2['interictal'], str(stats['interictal'])) +
                '%s preictaux : %s \n' % (stats2['preictal'], str(stats['preictal'])) +
                '%s tests : %s' % (stats2['test'], str(stats['test'])))