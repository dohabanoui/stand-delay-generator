"""Chargement de la configuration YAML."""
from pathlib import Path
import yaml

CONFIG_DIR = Path(__file__).parent

def load_config(path: str | Path | None = None) -> dict:
    p = Path(path) if path else CONFIG_DIR / "default.yaml"
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def load_regions() -> dict:
    import csv
    with open(CONFIG_DIR / "regions.csv", encoding="utf-8") as fh:
        return {r["state"]: r["region"] for r in csv.DictReader(fh)}
