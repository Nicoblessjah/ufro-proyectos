.PHONY: setup crop embed split train eval api


setup:
python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt


crop:
python scripts/crop_faces.py


embed:
python scripts/embeddings.py


split:
python scripts/split_train_val.py


train:
python train.py


eval:
python evaluate.py


api:
FLASK_APP=api/app.py flask run -p 5000


serve:
bash scripts/run_gunicorn.sh