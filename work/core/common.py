from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping


FORBIDDEN_REQUIRED_TERMS = {
    "controller",
    "serviceimpl",
    "spring",
    "springboot",
    "springmvc",
    "mybatis",
    "hibernate",
    "jpa",
    "repository",
}


def normalize_token(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def ensure_identifier(value: str, field_name: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError(f"{field_name} must be non-empty")
    return candidate


def ensure_summary(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("summary must be non-empty")
    return candidate


def ensure_kind(value: str, field_name: str = "kind") -> str:
    candidate = normalize_token(ensure_identifier(value, field_name))
    if candidate in FORBIDDEN_REQUIRED_TERMS:
        raise ValueError(f"{field_name} must remain adapter-neutral: {value}")
    return candidate


def ensure_neutral_collection(values: Iterable[str], field_name: str) -> List[str]:
    normalized: List[str] = []
    for value in values:
        token = normalize_token(value)
        if token in FORBIDDEN_REQUIRED_TERMS:
            raise ValueError(f"{field_name} contains adapter-specific term: {value}")
        normalized.append(token)
    return normalized


def stable_id(namespace: str, kind: str, name: str) -> str:
    return f"{normalize_token(namespace)}:{ensure_kind(kind)}:{normalize_token(name)}"


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


@dataclass(frozen=True)
class ExtensionMap:
    values: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in self.values:
            ensure_identifier(key, "extension key")

    def to_dict(self) -> Dict[str, Any]:
        return serialize(self.values)


@dataclass(frozen=True)
class ModelEnvelope:
    schema_version: str
    model_name: str
    generated_by: str

    def __post_init__(self) -> None:
        ensure_identifier(self.schema_version, "schema_version")
        ensure_identifier(self.model_name, "model_name")
        ensure_identifier(self.generated_by, "generated_by")

    def to_dict(self) -> Dict[str, str]:
        return {
            "schema_version": self.schema_version,
            "model_name": self.model_name,
            "generated_by": self.generated_by,
        }


def validate_required_fields(record: Mapping[str, Any], required_fields: Iterable[str]) -> None:
    missing = [field for field in required_fields if not record.get(field)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
