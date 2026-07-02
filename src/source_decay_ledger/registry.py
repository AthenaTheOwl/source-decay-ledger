"""Registry: typed Source model + load/validate from sources.yaml."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")


class Source(BaseModel):
    slug: str = Field(min_length=3, max_length=41)
    name: str
    category: str
    fetch_kind: Literal["rss", "atom", "html", "manual"]
    fetch_target: str
    added_on: date
    verdict: Literal["keep", "probation", "drop"]
    aliases: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def slug_pattern(cls, v: str) -> str:
        if not SLUG_PATTERN.match(v):
            raise ValueError(
                f"slug {v!r} must match ^[a-z0-9][a-z0-9-]{{2,40}}$"
            )
        return v


class RegistryError(Exception):
    """Registry validation failed. Message names the offending entry."""


def load_registry(path: Path | str) -> list[Source]:
    p = Path(path)
    if not p.exists():
        raise RegistryError(f"registry file not found: {p}")
    # A directory or unreadable file surfaces as OSError from read_text, and a
    # syntactically broken YAML body as YAMLError from safe_load; convert both to
    # RegistryError so every command that loads the registry reports one clean
    # INVALID line instead of a raw traceback.
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as err:
        raise RegistryError(f"cannot read registry file {p}: {err}") from err
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as err:
        raise RegistryError(f"registry at {p} is not valid YAML: {err}") from err
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise RegistryError(
            f"registry at {p} must be a YAML list at the top level"
        )
    seen_slugs: set[str] = set()
    sources: list[Source] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            raise RegistryError(f"entry #{i} is not a mapping: {entry!r}")
        try:
            source = Source(**entry)
        except ValidationError as err:
            slug = entry.get("slug", f"<entry #{i}>")
            raise RegistryError(f"entry {slug!r} failed validation: {err}") from err
        if source.slug in seen_slugs:
            raise RegistryError(f"duplicate slug: {source.slug!r}")
        seen_slugs.add(source.slug)
        sources.append(source)
    return sources


def validate_registry(path: Path | str) -> int:
    """Return number of valid sources, or raise RegistryError."""
    sources = load_registry(path)
    return len(sources)
