import json, joblib, yaml
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


cfg = yaml.safe_load(open('configs/base.yaml'))
train = pd.read_csv(cfg['data']['train_csv'])
X = train[[c for c in train.columns if c.startswith('f')]]
y = train['label']


model_type = cfg['model']['type']
if model_type == 'logreg':
	clf = LogisticRegression(**cfg['model']['params'])
elif model_type == 'linear_svm':
	# Usaremos decision_function como score (convertible a pseudo-proba vía min-max en eval)
	clf = LinearSVC()
else:
	raise ValueError('model.type must be logreg or linear_svm')


pipe = Pipeline([
	('scaler', StandardScaler(with_mean=False)),
	('clf', clf)
])


pipe.fit(X, y)
joblib.dump(pipe, 'models/model.joblib')


# Métricas provisionales en train
if model_type == 'logreg':
	score = pipe.predict_proba(X)[:, 1]
else:
	score = pipe.decision_function(X)


roc_auc = roc_auc_score(y, score)
ap = average_precision_score(y, score)
f1 = f1_score(y, (score >= 0.5).astype(int))
print({'roc_auc': roc_auc, 'average_precision': ap, 'f1_at_0.5': f1})