"""Regression tests: config flow must not use deprecated HA connection class constants."""

import subprocess
import sys
from pathlib import Path

import custom_components.ha_strava.config_flow as config_flow_module
from custom_components.ha_strava.config_flow import OAuth2FlowHandler


def test_flow_class_does_not_declare_connection_class() -> None:
    """The connection class is declared by iot_class in manifest.json only."""
    assert "CONNECTION_CLASS" not in vars(OAuth2FlowHandler)


def test_config_flow_source_has_no_conn_class_reference() -> None:
    """The module source must not reference any CONN_CLASS_* constant."""
    source = Path(config_flow_module.__file__).read_text(encoding="utf-8")
    assert "CONN_CLASS" not in source


def test_import_emits_no_conn_class_warning() -> None:
    """Importing the module in a fresh interpreter must not use deprecated constants."""
    code = (
        "import logging, sys, warnings\n"
        "logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)\n"
        "warnings.simplefilter('always')\n"
        "import custom_components.ha_strava.config_flow as m\n"
        "m.OAuth2FlowHandler()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(config_flow_module.__file__).parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "CONN_CLASS" not in result.stdout + result.stderr
