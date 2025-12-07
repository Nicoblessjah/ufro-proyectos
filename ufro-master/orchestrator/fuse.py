from typing import List, Optional, Tuple, Literal, Dict
Decision = Literal["identified", "ambiguous", "unknown"]

def fuse_candidates(
    candidates: List[Dict],
    margin: float,
) -> Tuple[Decision, Optional[Dict]]:
    """
    Recibe candidatos con keys: name, score, threshold.
    Aplica reglas:
      - si no hay candidatos con score válido: unknown
      - si mejor.score < mejor.threshold: unknown
      - si hay segundo y (mejor.score - segundo.score) < margin: ambiguous
      - si no: identified con mejor
    """
    valid = [c for c in candidates if c.get("score") is not None]
    if not valid:
        return "unknown", None

    valid.sort(key=lambda c: c["score"], reverse=True)
    best = valid[0]
    second = valid[1] if len(valid) > 1 else None

    if best["score"] < best["threshold"]:
        return "unknown", None

    if second is not None:
        if (best["score"] - second["score"]) < margin:
            return "ambiguous", None

    return "identified", {"name": best["name"], "score": best["score"]}
