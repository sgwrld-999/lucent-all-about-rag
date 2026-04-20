"""Compatibility wrapper for older imports from `utility.common`."""

try:
    from lucent.utils.common import *  # noqa: F403
except ModuleNotFoundError:
    from utils.common import *  # noqa: F403
