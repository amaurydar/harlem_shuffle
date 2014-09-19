__author__ = 'amaury'

import json
import os
import scipy.io
import numpy as np

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
                self.seq_numbers = [mat[name][0][0][4]]
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
                if type == 'preictal':
                    self.tts = float(settings['dog_pre_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif type == 'interictal':
                    self.tts = float(settings['dog_inter_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif type == 'test':
                    self.tts = None
            if 'Patient' in filepath:
                if type == 'preictal':
                    self.tts = float(settings['patient_pre_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif type == 'interictal':
                    self.tts = float(settings['patient_inter_time_to_seizure']) + (7 - mat[name][0][0][4][0][
                        0]) * self.duration
                elif type == 'test':
                    self.tts = None
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
        return res

    def point(self, time):
        return int(time / self.duration * (sum(slice.stop - slice.start for slice in self.slices) - 1))

    def __getitem__(self, slice):
        res = Segment()
        res.filepathes = []
        res.slices = []
        res.duration = (slice.stop - slice.start - 1) / (
        sum(slice.stop - slice.start for slice in self.slices) - 1) * self.duration
        if self.data is not None:
            res.data = self.data[slice]
        else:
            res.data = None
        if self.tts is not None:
            res.tts = self.tts - float(slice.start) / (
            sum([slice.stop - slice.start for slice in self.slices]) - 1) * self.duration
        else:
            res.tts = None

        start = slice.start
        stop = slice.stop
        for filepath, slice, seq_number in zip(self.filepathes, self.slices, self.seq_numbers):
            if len(set(range(start, stop)) & set(range(slice.start, len(slice.stop)))) > 0:
                res.filepathes.append(filepath)
                res.slices.append(slice)
                res.seq_numbers.append(seq_number)
            start -= slice.stop - slice.start
            stop -= slice.stop - slice.start


class Subject(object):
    def __init__(self, race, n):
        self.race = race
        self.n = n

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'LOCAL_SETTINGS.json')) as f:
            settings = json.load(f)
        self.dir = str(settings['data-dir']) + '/%s_%s' % (self.race, self.n)

        self.segments = []
        for type in ('preictal', 'interictal', 'test'):
            i = 1
            filepath = '%s/%s_%s_%s_segment_%04d.mat' % (self.dir, self.race, self.n, type, i)
            currentSegment = None
            previousSeq = -1
            while os.path.exists(filepath):
                print filepath
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
