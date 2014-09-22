from common import data
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pickle

n_estimators = 1000
width = 239766

number = {'Dog' : 5,
          'Patient' : 2}
for race in ('Dog', 'Patient'):
    for j in range(1, number[race]+1):
        subject = data.Subject(race, j)

        X_train = []
        y_train = []

        for segment in subject.segments:
            segment.loadData()
            i=0
            while (i+1)*width<=segment.length:
                if segment.type in ('preictal', 'interictal'):
                    X_train.append(np.abs(np.fft.rfft(segment[i*width:(i+1)*width].data, axis = 1)[:,:80].flatten()))
                    y_train.append(int(segment.type == 'preictal'))
                i += 1
            segment.data = None

        X_train = np.array(X_train)
        X_train = X_train.astype(np.float32, copy = False)

        y_train = np.array(y_train)
        y_train = y_train.astype(np.float32, copy = False)

        clf = RandomForestClassifier(n_estimators=n_estimators,
                                     n_jobs=-1,
                                     verbose=3)
        clf = clf.fit(X_train, y_train)

        pickle.dump(clf, open('pickles/rf_clf_%s_%s_%s_%s.p' % (n_estimators, width, race, j), 'w'))
        clf = None




