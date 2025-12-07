import json, datetime, pathlib, sys

src = pathlib.Path("reports/eval_summary.json")
if not src.exists():
    sys.exit("No existe reports/eval_summary.json. Ejecuta primero scripts/evaluate.py con --out_json.")

with open(src, "r", encoding="utf-8") as f:
    d = json.load(f)

ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def g(key, default="N/A"):
    return d.get(key, default)

md = f"""# Reporte de Evaluación – Me Verifier

- Fecha: {ts}
- API: http://127.0.0.1:5000/verify

## Métricas
- Imágenes procesadas: {g('processed')}
- Correctas: {g('correct')}
- **Accuracy**: {g('accuracy', 0):.3f}
- Saltadas ME: {g('skipped_me')}
- Saltadas NOT_ME: {g('skipped_not_me')}

## Notas
- Las imágenes “saltadas” suelen deberse a que no se detecta rostro, formato no soportado o archivos corruptos.
- Umbral usado (`threshold`): {g('threshold')}
"""

out = pathlib.Path("reports/README_eval.md")
out.write_text(md, encoding="utf-8")
print(f"Generado: {out}")
