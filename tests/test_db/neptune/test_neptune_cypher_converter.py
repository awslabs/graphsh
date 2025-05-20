"""
Integration tests for Neptune Cypher converter.

These tests verify that the converter correctly transforms Neptune Cypher responses
into the expected GraphSh data models.
"""

import json
import pytest
from pathlib import Path

from graphsh.db.converters.neptune import NeptuneCypherConverter
from graphsh.models.graph import dict_graph_element

# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "cypher_converter"


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
        "match_n_return_n",
        "match_n_return_count",
        "match_r_return_r",
        "match_n_return_properties",
        "match_n_return_labels",
        "match_n_return_id",
    ],
)
def test_neptune_cypher_converter(test_name):
    """Test that the converter correctly transforms Neptune Cypher responses."""
    input_data, expected_output = load_test_data(test_name)

    # Create converter instance
    converter = NeptuneCypherConverter()

    # Convert the input data
    actual_output = converter.convert_results(input_data)
    actual_json = dict_graph_element(actual_output)

    # Assert that the actual output matches the expected output
    assert actual_json == expected_output, f"Conversion failed for {test_name}"
