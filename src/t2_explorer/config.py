"""Constants: endpoints, paths, guards, column maps, and the harvest query list."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"
ASSETS_DIR = ROOT / "assets"
TEMPLATES_DIR = ROOT / "templates"

API_BASE = "https://technology.nasa.gov/api/api"
USER_AGENT = "nasa-tech-explorer (github.com/RYASTRA/nasa-tech-explorer)"
DATASETS = ("patent", "patent_issued", "software", "spinoff")

SITE_BASE_URL = "https://ryastra.github.io/nasa-tech-explorer"

URL_SEGMENT = {
    "patent": "patent",
    "patent_issued": "patent-issued",
    "software": "software",
    "spinoff": "spinoff",
}
DATASET_LABELS = {
    "patent": "Patent — available for licensing",
    "patent_issued": "Issued patent",
    "software": "Software — free catalog",
    "spinoff": "Spinoff story",
}
LINK_LABELS = {
    "patent": "License this technology at technology.nasa.gov",
    "patent_issued": "View at technology.nasa.gov",
    "software": "Find it in the NASA software catalog",
    "spinoff": "Read the full spinoff story",
}

REQUEST_TIMEOUT = 30.0
REQUEST_RPS = 3.0
RETRIES = 3
MISS_LIMIT = 7
MAX_FAILED_QUERY_RATIO = 0.05
MIN_KEEP_RATIO = 0.90
MAX_SKIPPED_ROW_RATIO = 0.01
INDEX_ABSTRACT_CHARS = 300
INDEX_GZIP_BUDGET = 1_200_000

# Column positions in the API's 13-column result rows.
# Provisional (docs show a 10-column example; live rows have 13).
# Task 2 pins these against recorded fixtures — adjust there if tests fail.
_COMMON = {
    "id": 0,
    "case_number": 1,
    "title": 2,
    "abstract": 3,
    "slug_ref": 4,
    "category": 5,
    "center": 9,
}
COLUMN_MAP: dict[str, dict[str, int]] = {
    "patent": dict(_COMMON),
    "patent_issued": dict(_COMMON),
    "software": dict(_COMMON),
    # Task 2: if a spinoff column holds an http(s) URL, add "url": <index> here.
    "spinoff": dict(_COMMON),
}

# Harvest terms: the API can't enumerate, so the snapshot is the union of these
# word queries, deduped by record id. Tuned in Task 11 until marginal yield ~ 0.
QUERY_TERMS: list[str] = [
    *"abcdefghijklmnopqrstuvwxyz",
    *"0123456789",
    # T2 category vocabulary
    "aeronautics",
    "communications",
    "electronics",
    "electrical",
    "environment",
    "health",
    "medicine",
    "biotechnology",
    "instrumentation",
    "manufacturing",
    "materials",
    "coatings",
    "mechanical",
    "fluid",
    "optics",
    "power",
    "energy",
    "storage",
    "propulsion",
    "robotics",
    "automation",
    "software",
    "sensors",
    "information",
    "technology",
    # High-frequency title words (seed list; Task 11 extends from real titles)
    "system",
    "method",
    "apparatus",
    "device",
    "process",
    "composite",
    "laser",
    "sensor",
    "control",
    "data",
    "high",
    "temperature",
    "pressure",
    "advanced",
    "aircraft",
    "space",
    "thermal",
    "engine",
    "fuel",
    "water",
    "air",
    "surface",
    "structure",
    "imaging",
    "detection",
    "measurement",
    "wireless",
    "network",
    "algorithm",
    "model",
    "simulation",
    "analysis",
    "tool",
    "design",
    "test",
    "monitoring",
    "safety",
    "autonomous",
    "vehicle",
    "rocket",
    "propellant",
    "battery",
    "solar",
    "antenna",
    "radar",
    "satellite",
    "orbit",
    "flight",
    "launch",
    "crew",
    "robot",
    "polymer",
    "alloy",
    "membrane",
    "catalyst",
    "fiber",
    "nano",
    "micro",
    "plasma",
    "cryogenic",
    "valve",
    "pump",
    "turbine",
    "actuator",
    "additive",
    "welding",
    "heat",
    "shield",
    "gas",
    "liquid",
    "oxygen",
    "hydrogen",
    "carbon",
    "metal",
    "ceramic",
    "adhesive",
    "lubricant",
    "corrosion",
    "fatigue",
    "vibration",
    "acoustic",
    "optical",
    "infrared",
    "ultraviolet",
    "microwave",
    "frequency",
    "signal",
    "communication",
    "navigation",
    "guidance",
    "tracking",
    "mapping",
    "terrain",
    "lunar",
    "planetary",
    "mars",
    "earth",
    "atmosphere",
    "radiation",
    "protection",
    "life",
    "support",
    "habitat",
    "food",
    "waste",
    "recycling",
    "filtration",
    "purification",
    "sterilization",
    "medical",
    "diagnostic",
    "prosthetic",
    "implant",
    "tissue",
    "cell",
    "dna",
    "protein",
    "assay",
    "image",
    "camera",
    "lens",
    "mirror",
    "telescope",
    "spectrometer",
    "interferometer",
    "gyroscope",
    "accelerometer",
    "magnetometer",
]
