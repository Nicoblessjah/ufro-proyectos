# scripts/crop_faces.py  (fix: guarda bien los recortes)
import os
from pathlib import Path
from PIL import Image
from facenet_pytorch import MTCNN
import torch

def ensure_dir(p): Path(p).mkdir(parents=True, exist_ok=True)

SRC_ME  = 'data/me'
SRC_NOT = 'data/not_me'
DST_ME  = 'data/cropped/me'
DST_NOT = 'data/cropped/not_me'

for d in [DST_ME, DST_NOT]:
    ensure_dir(d)

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(image_size=160, margin=14, post_process=True, device=device)

def process_dir(src, dst):
    ok, skip, err = 0, 0, 0
    for fn in os.listdir(src):
        if not fn.lower().endswith(('.jpg','.jpeg','.png')):
            continue
        path = os.path.join(src, fn)
        out  = os.path.join(dst, fn.rsplit('.',1)[0] + '.png')
        try:
            img = Image.open(path).convert('RGB')
            face = mtcnn(img, save_path=out)   # <<-- guarda el recorte correctamente
            if face is None:
                print(f"[skip] No face: {path}")
                skip += 1
            else:
                ok += 1
        except Exception as e:
            print(f"[err] {path}: {e}")
            err += 1
    print(f"[summary] {src} -> ok:{ok} skip:{skip} err:{err}")

process_dir(SRC_ME,  DST_ME)
process_dir(SRC_NOT, DST_NOT)
print('Done cropping.')
