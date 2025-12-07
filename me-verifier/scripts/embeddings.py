
# scripts/embeddings.py (versión robusta y con logs)
# Genera embeddings 512D desde data/cropped/me y data/cropped/not_me
# Uso:
#   python scripts/embeddings.py
#
# Requisitos: torch, torchvision, facenet-pytorch, pillow, pandas

import os, sys
from pathlib import Path
import pandas as pd
import torch
from PIL import Image
from torchvision import transforms
from facenet_pytorch import InceptionResnetV1

C_ME = Path('data/cropped/me')
C_NOT = Path('data/cropped/not_me')
OUT = Path('data/cropped/embeddings.csv')

def list_images(root: Path):
    exts = ('.png','.jpg','.jpeg','.PNG','.JPG','.JPEG')
    return [p for p in root.iterdir() if p.suffix in exts and p.is_file()]

def main():
    me_files = list_images(C_ME) if C_ME.exists() else []
    not_files = list_images(C_NOT) if C_NOT.exists() else []
    print(f"[emb] me files: {len(me_files)}")
    print(f"[emb] not_me files: {len(not_files)}")

    if len(me_files)+len(not_files) == 0:
        print("[emb] No hay imágenes en data/cropped. ¿Ejecutaste scripts/crop_faces.py?")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        import pandas as pd
        pd.DataFrame([]).to_csv(OUT, index=False)
        print(f"[emb] Wrote {OUT} with 0 rows")
        return

    device = torch.device('cpu')
    model = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    pre = transforms.Compose([
        transforms.Resize((160,160)),
        transforms.ToTensor(),
        transforms.Normalize([0.5,0.5,0.5],[0.5,0.5,0.5])
    ])

    rows = []
    def embed_one(path: Path, label: int):
        try:
            img = Image.open(path).convert('RGB')
            x = pre(img).unsqueeze(0).to(device)
            with torch.no_grad():
                vec = model(x).cpu().numpy().flatten()
            rows.append({
                'path': str(path).replace('\\','/'),
                'label': label,
                **{f'f{i}': float(vec[i]) for i in range(len(vec))}
            })
            return True
        except Exception as e:
            print(f"[emb][err] {path}: {e}", file=sys.stderr)
            return False

    ok = 0
    for p in me_files:
        if embed_one(p, 1): ok += 1
    for p in not_files:
        if embed_one(p, 0): ok += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    import pandas as pd
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"[emb] Wrote {OUT} with {len(rows)} rows (ok={ok}, me={len(me_files)}, not_me={len(not_files)})")

if __name__ == '__main__':
    main()
