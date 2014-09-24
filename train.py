from common import data
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pickle

n_estimators = 1000

window_duration = 10
step_duration = 10


race = 'Dog'
j=1
subject = data.Subject(race, j)

X_train = []
y_train = []

n_bins = window_duration/step_duration*400

for segment in subject.segments:
    segment.loadData()
    window_npoints = segment.point(window_duration)
    step_npoints = segment.point(step_duration)
    i=0
    while i*step_npoints+window_npoints<=segment.length:
        if segment.type in ('preictal', 'interictal'):
            tff = np.abs(np.fft.rfft(segment[i*step_npoints:i*step_npoints+window_npoints].data, axis = 1))
            Xi = []
            for k in range(0,n_bins):
                Xi += list(tff[:,k*tff.shape[1]/n_bins:(k+1)*tff.shape[1]/n_bins].sum(axis=1))
            X_train.append(np.array(Xi))
            y_train.append(int(segment.type == 'preictal'))
        i += 1
    segment.data = None

X_train = np.array(X_train)
print X_train
X_train = X_train.astype(np.float32, copy = False)

y_train = np.array(y_train)
y_train = y_train.astype(np.float32, copy = False)

clf = RandomForestClassifier(n_estimators=n_estimators,
                             n_jobs=-1,
                             verbose=3)
clf = clf.fit(X_train, y_train)

pickle.dump(clf, open('pickles/rf_clf_%s_%s_%s_%s_%s.p' % (n_estimators, window_duration, step_duration, race, j), 'w'))
clf = None