import json, yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve, auc


cfg = yaml.safe_load(open('configs/base.yaml'))
val = pd.read_csv(cfg['data']['val_csv'])
X = val[[c for c in val.columns if c.startswith('f')]]
y = val['label'].values


pipe = joblib.load('models/model.joblib')
# obtener score continuo
if hasattr(pipe.named_steps['clf'], 'predict_proba'):
	s = pipe.predict_proba(X)[:, 1]
else:
	s = pipe.decision_function(X)

# normalización min-max para usar como proxy de probas (solo para umbralizado)
s = (s - s.min()) / (s.max() - s.min() + 1e-9)


# búsqueda de umbral que maximiza F1
thr_grid = np.linspace(0.3, 0.9, 61)
f1s = []
from sklearn.metrics import f1_score
for t in thr_grid:
	yhat = (s >= t).astype(int)
	f1s.append(f1_score(y, yhat))


best_t = float(thr_grid[int(np.argmax(f1s))])
print({'best_threshold_f1': best_t})


# curvas
fpr, tpr, _ = roc_curve(y, s)
prec, rec, _ = precision_recall_curve(y, s)
roc_auc = auc(fpr, tpr)
print({'roc_auc': roc_auc})