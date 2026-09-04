import json
import pytest
from click.testing import CliRunner
from kaihou_engine.orchestrator import cli

def test_interactive_exit():
    runner = CliRunner()
    # Provide input to select "Exit" immediately
    result = runner.invoke(cli, ["translate"], input="2\n")
    assert result.exit_code == 0
    assert "Goodbye!" in result.output
