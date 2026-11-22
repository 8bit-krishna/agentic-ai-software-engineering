"""Runtime contracts shared by the CLI, web app, and model adapter."""

import re
from pathlib import PurePosixPath
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

MAX_TASK_LENGTH = 4000


class InputError(ValueError):
    """A problem the user can fix without reading a traceback."""


class ProviderError(RuntimeError):
    """A safe, public error message, never the raw provider response."""


def validate_task(task: object) -> str:
    if not isinstance(task, str):
        raise InputError("Task must be text.")
    task = task.strip()
    if not task:
        raise InputError("A non-empty task is required.")
    if len(task) > MAX_TASK_LENGTH:
        raise InputError(f"Keep the task within {MAX_TASK_LENGTH:,} characters.")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", task):
        raise InputError("Remove unsupported control characters from the task.")
    return task


Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=3000)]
Notes = Annotated[list[Note], Field(min_length=1, max_length=12)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class PlanOutput(Contract):
    plan: Notes


class ArchitectureOutput(Contract):
    architecture: Notes


class GeneratedFile(Contract):
    path: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    content: Annotated[str, StringConstraints(min_length=1, max_length=20000)]

    @field_validator("path")
    @classmethod
    def safe_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        parts = value.split("/")
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        if (path.is_absolute() or "\\" in value or ":" in value
                or any(part in ("", ".", "..") or part.endswith((".", " "))
                       or part.split(".")[0].upper() in reserved for part in parts)
                or any(ord(char) < 32 or ord(char) == 127 for char in value)
                or any(char in value for char in '<>"|?*')):
            raise ValueError("Use a safe relative filename.")
        return value


class CodeOutput(Contract):
    implementation_notes: Notes
    files: Annotated[list[GeneratedFile], Field(min_length=1, max_length=8)]
    test_plan: Notes

    @field_validator("files")
    @classmethod
    def unique_paths(cls, files: list[GeneratedFile]) -> list[GeneratedFile]:
        paths = [file.path.casefold() for file in files]
        if len(paths) != len(set(paths)):
            raise ValueError("Generated filenames must be unique.")
        return files
