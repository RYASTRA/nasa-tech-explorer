"""TechRecord dataclass and (de)serialization."""

from dataclasses import asdict, dataclass


@dataclass
class TechRecord:  # pylint: disable=too-many-instance-attributes  # it's a record type
    """One normalized T2 catalog entry plus mirror bookkeeping."""

    dataset: str
    id: str
    case_number: str
    title: str
    abstract: str
    category: str
    center: str
    url: str
    slug: str
    raw: list
    first_seen: str
    last_seen: str
    miss_count: int = 0

    def to_dict(self) -> dict:
        """Plain-dict form for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "TechRecord":
        """Rebuild a record from its to_dict() form."""
        return cls(**d)
