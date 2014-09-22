__author__ = 'amaury'

import json
import os
import scipy.io
import numpy as np
import time
import ntpath
import matplotlib.pyplot as plt
import pickle


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
            self.length = mat[name][0][0][0].shape[1]
            self.n_electrodes = mat[name][0][0][0].shape[0]
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
        if self.n_electrodes == segment.n_electrodes:
            res = Segment()
            res.n_electrodes = self.n_electrodes
            res.length = self.length + segment.length
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
        else:
            raise Exception("trying to concatenate two segments with different n_electrodes")

    def point(self, time):
        return int(float(time) / self.duration * self.length)

    def time(self, point):
        return float(point) / self.length * self.duration

    def __getitem__(self, s):
        start = s.start
        stop = s.stop
        if start is None:
            start = 0
        if stop is None:
            stop = self.length

        if start<0:
            start = self.length+start
        if stop<0:
            stop = self.length+stop
        res = Segment()
        res.n_electrodes = self.n_electrodes
        res.filepathes = []
        res.slices = []
        res.seq_numbers = []

        res.duration = float(stop - start) / self.length * self.duration
        if self.data is not None:
            res.data = self.data[:,slice(start, stop)]
        else:
            res.data = None
        if self.tts is not None:
            res.tts = self.tts - float(start) / self.length * self.duration
        else:
            res.tts = None
        res.type = self.type


        for filepath, slice_, seq_number in zip(self.filepathes, self.slices, self.seq_numbers):
            if not (slice_.stop<=start or stop<=slice_.start):
                res.filepathes.append(filepath)
                start__ = max(start, 0)
                stop__ = min(stop, slice_.stop)
                res.slices.append(slice(start__, stop__))
                res.seq_numbers.append(seq_number)
            start -= slice_.stop - slice_.start
            stop -= slice_.stop - slice_.start

        res.length = sum([slice_.stop-slice_.start for slice_ in res.slices])
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
            res = 'Data loaded \n'
        res += 'Duration : %s s\n' % round(self.duration, 3)
        res += 'Length : %s \n' % self.length
        res += 'N_electrodes : %s \n' % self.n_electrodes
        res += 'Type : %s \n' % self.type
        if self.tts is not None:
            res += 'Time to seizure : %s \n' % round(self.tts, 3)
        res += 'Data origin : \n'
        res += '\n'.join(['%s, %s:%s' % (ntpath.basename(fp), s.start, s.stop) for fp, s in zip(self.filepathes, self.slices)])
        return res

    def plot(self, electrodes = None, figsize = None, linewidth = None):
        if electrodes is None:
            electrodes = range(self.n_electrodes)
        if figsize is None:
            figsize = (18, len(electrodes)*1.5)
        if linewidth is None:
            linewidth = 0.4
        if self.data is None:
            raise Exception("data must be loaded before plotting")

        fig, axs = plt.subplots(nrows=len(electrodes), ncols=1, figsize=figsize, sharex=True, sharey=True)
        fig.subplots_adjust(bottom = 0.15)
        fig.subplots_adjust(hspace=0)

        for i in electrodes:
            ax = axs[i]
            ax.plot(np.linspace(0, self.duration, self.length+1), np.concatenate((self.data[i,:], [self.data[i,self.length-1]]), axis=1), linewidth=linewidth)
            ax.set_xlim([0, self.duration])
            ax.set_ylabel(i, rotation = 'horizontal', fontweight = 'bold', fontsize = 16)


        axs[electrodes[-1]].set_xlabel('Time (s)', fontweight = 'bold', fontsize = 16)

        lim = max(abs(ax.get_ylim()[0]), abs(ax.get_ylim()[1]))
        for i in electrodes:
            axs[i].set_ylim([-lim, lim])
        plt.setp([a.get_xticklabels() for a in fig.axes[:-1]], visible=False)

        return fig, axs

class Subject(object):
    def __init__(self, race, n, forceRead = False):
        path = os.path.abspath(__file__)
        modulename = path.split('/')[-3]
        start_time = time.time()
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'LOCAL_SETTINGS.json')) as f:
                settings = json.load(f)
        self.dir = str(settings['data-dir']) + '/%s_%s' % (race, n)
        self.race = race
        self.n = n
        if not forceRead and os.path.exists(self.dir + '/%s_%s_%s.p' % (race, n, modulename)):
            obj = pickle.load(open(self.dir + '/%s_%s_%s.p' % (race, n, modulename), 'r'))
            print 'Loaded previously read %s %s in %s s' % (race, n, round(time.time()-start_time, 1))
            self.segments = obj.segments
        else:
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
                pickle.dump(self, open(self.dir + '/%s_%s_%s.p' % (self.race, self.n, modulename), 'w'))
            print 'Read %s %s : %s files into %s segments in %s s' % (self.race, self.n, filecount, len(self.segments), round(time.time()-start_time, 1))
    def __str__(self):
        stats_count = {'interictal' : 0, 'preictal' : 0, 'test' : 0}
        stats_duration = {'interictal' : {}, 'preictal' : {}, 'test' : {}}
        stats_length = {'interictal' : {}, 'preictal' : {}, 'test' : {}}
        stats_n_electrodes = {'interictal' : {}, 'preictal' : {}, 'test' : {}}
        for segment in self.segments:
            stats_count[segment.type] += 1
            if segment.duration in stats_duration[segment.type]:
                stats_duration[segment.type][segment.duration] += 1
            else:
                stats_duration[segment.type][segment.duration] = 1
            if segment.length in stats_length[segment.type]:
                stats_length[segment.type][segment.length] += 1
            else:
                stats_length[segment.type][segment.length] = 1
            if segment.n_electrodes in stats_n_electrodes[segment.type]:
                stats_n_electrodes[segment.type][segment.n_electrodes] += 1
            else:
                stats_n_electrodes[segment.type][segment.n_electrodes] = 1

        return ('%s %s \n' % (self.race, self.n) +
                '%s interictaux : duration %s, length %s, n_electrodes %s \n' % (stats_count['interictal'], str(stats_duration['interictal']), str(stats_length['interictal']), str(stats_n_electrodes['interictal'])) +
                '%s preictaux : duration %s, length %s, n_electrodes %s \n' % (stats_count['preictal'], str(stats_duration['preictal']), str(stats_length['preictal']), str(stats_n_electrodes['preictal'])) +
                '%s tests : duration %s, length %s, n_electrodes %s \n' % (stats_count['test'], str(stats_duration['test']), str(stats_length['test']), str(stats_n_electrodes['test'])))
