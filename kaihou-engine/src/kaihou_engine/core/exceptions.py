"""Custom exception hierarchy for Kaihou Engine.

Only a few specialized exceptions are needed at the moment; more can be
added as the pipeline grows.
"""

class KaihouError(Exception):
    """Base class for all Kaihou Engine errors."""
    pass


class ConfigError(KaihouError):
    """Raised when a required configuration file cannot be parsed or is missing."""
    pass


class PluginError(KaihouError):
    """Raised when a plugin fails to load, initialise or execute correctly."""
    pass


class PipelineError(KaihouError):
    """Raised for unrecoverable errors inside the pipeline execution."""
    pass


__all__ = ["KaihouError", "ConfigError", "PluginError", "PipelineError"]
