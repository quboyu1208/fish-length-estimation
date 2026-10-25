"""Fish endpoint measurement; core functionality has no external dependencies."""
from .measurement import Measurement, measure_endpoints

__version__ = "0.3.0"
__all__ = ["Measurement", "measure_endpoints"]
