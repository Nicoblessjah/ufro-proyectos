# scripts/get_negatives_lfw.py
# Descarga LFW (scikit-learn) y guarda N rostros en data/not_me/ como PNG.
# Uso:
#   python scripts/get_negatives_lfw.py --n 400 --data_home data/_skdata
#
# Requisitos: scikit-learn, pillow, numpy

import argparse, os
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.datasets import fetch_lfw_people

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=400, help="cantidad de negativos a guardar")
    parser.add_argument("--outdir", type=str, default="data/not_me", help="carpeta de salida")
    parser.add_argument("--data_home", type=str, default=None, help="cache local para LFW (opcional)")
    args = parser.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)

    # color=True para 3 canales; resize=1.0 mantiene resolución (~250x250)
    lfw = fetch_lfw_people(
        color=True,
        resize=1.0,
        funneled=True,
        download_if_missing=True,
        data_home=args.data_home
    )

    imgs = lfw.images  # shape: (n_samples, h, w, 3), dtype float (0..1) o (0..255)
    n = min(args.n, imgs.shape[0])

    saved = 0
    for i in range(n):
        arr = imgs[i]

        # --- FIX: si viene en 0..1, escalar a 0..255 ---
        maxv = float(arr.max())
        if maxv <= 1.5:
            arr = (arr * 255.0).round()

        # Asegurar rango/tipo y RGB
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        im = Image.fromarray(arr).convert("RGB")
        im.save(os.path.join(args.outdir, f"lfw_{i:04d}.png"))
        saved += 1
        if saved % 50 == 0:
            print(f"[lfw] {saved} guardadas...", flush=True)

    print(f"Guardadas {saved} imágenes en {args.outdir}")

if __name__ == "__main__":
    main()
