__author__ = 'amaury'

from common import data
import numpy as np
import pickle
import os

n_estimators = 300

number = {'Dog' : 5,
          'Patient' : 2}
with open('submission.txt','w') as f:
    f.write('clip,preictal')
    for race in ('Dog', 'Patient'):
        for j in range(1, number[race]+1):
            subject = data.Subject(race, j)

            clf = pickle.load(open('pickles/rf_clf_%s_%s_%s.p' % (n_estimators, race, j), 'r'))

            for segment in subject.segments:
                if segment.type == 'test':
                    X = []
                    segment.loadData()
                    n = segment.point(10)
                    i=0
                    while (i+1)*n<=segment.length:
                        X.append(np.abs(np.fft.rfft(segment[i*n:(i+1)*n].data, axis = 1)[:,:80].flatten()))
                        i += 1
                    segment.data = None
                    f.write('%s,%s\n' %(os.path.basename(segment.filepathes[0]), clf.predict_proba(X)[:,1].mean()))





