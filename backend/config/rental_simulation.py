"""Independent opt-in for isolated staging simulation, unrelated to recovery."""

import os


def enabled_from_env(environ=None):
    environ = os.environ if environ is None else environ
    return environ.get("RENTAL_STAGING_SIMULATION_ENABLED", "false").lower() == "true"
