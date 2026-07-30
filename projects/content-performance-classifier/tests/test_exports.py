from __future__ import annotations

from dataclasses import replace
from io import StringIO

import pandas as pd

from content_performance_classifier import (
    evaluate_at_threshold,
    predictions_to_safe_csv,
)


def test_csv_export_neutralizes_formula_strings_but_preserves_numbers(artifact) -> None:
    result = evaluate_at_threshold(artifact)
    predictions = result.predictions.head(7).copy()
    predictions["content_id"] = [
        "=SUM(A1:A2)",
        "+cmd",
        "-formula",
        "@remote",
        "\tformula",
        "  =SUM(A1:A2)",
        "ordinary",
    ]
    predictions["signed_measure"] = [-3.5, 2.0, 0.0, -1.0, 4.0, 9.0, -8.0]
    amended = replace(result, predictions=predictions)

    exported = predictions_to_safe_csv(amended)
    round_trip = pd.read_csv(StringIO(exported))

    assert round_trip["content_id"].tolist()[:6] == [
        "'=SUM(A1:A2)",
        "'+cmd",
        "'-formula",
        "'@remote",
        "'\tformula",
        "'  =SUM(A1:A2)",
    ]
    assert round_trip["signed_measure"].tolist() == [
        -3.5,
        2.0,
        0.0,
        -1.0,
        4.0,
        9.0,
        -8.0,
    ]
