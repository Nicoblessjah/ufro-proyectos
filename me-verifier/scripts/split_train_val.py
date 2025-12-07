import pandas as pd
from sklearn.model_selection import train_test_split
import yaml


cfg = yaml.safe_load(open('configs/base.yaml'))
emb = pd.read_csv(cfg['data']['embeddings_csv'])
train, val = train_test_split(emb, test_size=cfg['val_size'], stratify=emb['label'], random_state=cfg['seed'])
train.to_csv(cfg['data']['train_csv'], index=False)
val.to_csv(cfg['data']['val_csv'], index=False)
print('Split done:', len(train), len(val))