"""Universal file converter - conversion logic, independent of the GUI.

Importing this package registers all available converters.
"""
from . import data  # noqa: F401  (registers CSV <-> JSON)
from .registry import (
    REGISTRY,
    ConversionError,
    ConversionRequest,
    InvalidInputError,
    MissingDependencyError,
    OutputError,
    UnsupportedConversionError,
    available_targets,
    execute,
    supported_pairs,
)

__all__ = [
    "REGISTRY",
    "ConversionError",
    "ConversionRequest",
    "InvalidInputError",
    "MissingDependencyError",
    "OutputError",
    "UnsupportedConversionError",
    "available_targets",
    "execute",
    "supported_pairs",
]
