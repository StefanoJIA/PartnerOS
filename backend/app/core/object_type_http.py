"""HTTP helpers for polymorphic object_type path segments."""

from fastapi import HTTPException

from app.constants.object_type import normalize_object_type


def parse_object_type_path(raw: str) -> str:
    try:
        return normalize_object_type(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
