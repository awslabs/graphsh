"""
Integration tests for Neptune Gremlin converter.

These tests verify that the converter correctly transforms Neptune Gremlin responses
into the expected GraphSh data models.
"""

import json
import pytest
from pathlib import Path

from graphsh.db.converters.neptune import NeptuneGremlinConverter
from graphsh.models.graph import dict_graph_element

# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "gremlin_converter"


def load_test_data(test_name):
    """Load test input and expected output data."""
    input_path = TEST_DATA_DIR / f"{test_name}.input"
    output_path = TEST_DATA_DIR / f"{test_name}.output"

    with open(input_path, "r") as f:
        input_data = json.load(f)

    with open(output_path, "r") as f:
        expected_output = json.load(f)

    return input_data, expected_output


@pytest.mark.parametrize(
    "test_name",
    [
        "g_V",
        "g_E",
        "g_V_properties",
        "g_V_count",
        "g_E_count",
        "g_V_elementMap",
        "g_V_group_by_label",
    ],
)
def test_neptune_gremlin_converter(test_name):
    """Test that the converter correctly transforms Neptune Gremlin responses."""
    input_data, expected_output = load_test_data(test_name)

    # Create converter instance
    converter = NeptuneGremlinConverter()

    # Convert the input data
    actual_output = converter.convert_results(input_data)

    # Convert to JSON for comparison
    actual_json = dict_graph_element(actual_output)

    # Assert that the actual output matches the expected output
    assert actual_json == expected_output, f"Conversion failed for {test_name}"
