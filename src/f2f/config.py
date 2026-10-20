from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parents[2] / "configs" / "base.yaml"


def merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load(path: str | Path | None = None) -> dict:
    """base.yaml, overlaid with the given scenario file."""
    cfg = yaml.safe_load(BASE.read_text(encoding="utf-8"))
    if path and Path(path).resolve() != BASE:
        cfg = merge(cfg, yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {})
    return cfg
