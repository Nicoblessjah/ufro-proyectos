import argparse, json, os, time, mimetypes, requests, glob

def post_image(api, path):
    ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        r = requests.post(api, files={"image": (os.path.basename(path), f, ctype)}, timeout=30)
    return r

def evaluate_dir(api, dir_path, expected_is_me):
    files = []
    for ext in ("*.jpg","*.jpeg","*.png","*.JPG","*.JPEG","*.PNG"):
        files.extend(glob.glob(os.path.join(dir_path, ext)))
    ok, total, skipped, items = 0, 0, 0, []

    for p in files:
        total += 1
        try:
            r = post_image(api, p)
            if r.status_code == 200:
                data = r.json()
                pred = bool(data.get("is_me"))
                score = float(data.get("score", 0))
                ok += int(pred == expected_is_me)
                items.append({"path": p, "status":"ok", "pred_is_me": pred, "score": score})
            else:
                # 4xx/5xx: registra y sigue
                msg = ""
                try:
                    msg = r.json()
                except Exception:
                    msg = r.text
                skipped += 1
                items.append({"path": p, "status": f"skip_{r.status_code}", "message": str(msg)})
        except Exception as e:
            skipped += 1
            items.append({"path": p, "status":"skip_exc", "message": repr(e)})
    return {"ok": ok, "total": total, "skipped": skipped, "items": items}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True)
    ap.add_argument("--me_dir", required=True)
    ap.add_argument("--not_me_dir", required=True)
    ap.add_argument("--out_json", required=True)
    args = ap.parse_args()

    t0 = time.time()
    res_me = evaluate_dir(args.api, args.me_dir, True)
    res_not = evaluate_dir(args.api, args.not_me_dir, False)
    dt = (time.time() - t0) * 1000

    processed = (res_me["total"] - res_me["skipped"]) + (res_not["total"] - res_not["skipped"])
    correct = res_me["ok"] + res_not["ok"]
    acc = (correct / processed) if processed else 0.0

    summary = {
        "api": args.api,
        "timing_ms": dt,
        "me": res_me,
        "not_me": res_not,
        "processed": processed,
        "correct": correct,
        "accuracy": acc
    }
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # resumen consola
    print(f"Procesadas: {processed} | Correctas: {correct} | Acc: {acc:.3f}")
    print(f"Saltadas ME: {res_me['skipped']} | Saltadas NOT_ME: {res_not['skipped']}")

if __name__ == "__main__":
    main()
