from datetime import date

from health_report.report.semiannual import build_semi_annual_reviews


def test_semiannual_reviews_with_data():
    data = [
        {
            "test_code": "A1C",
            "test_name": "Hemoglobin A1c",
            "value": 6.2,
            "unit": "%",
            "ref_low": None,
            "ref_high": 5.6,
            "measured_at": "2023-02-15",
        },
        {
            "test_code": "HDL",
            "test_name": "HDL Cholesterol",
            "value": 55,
            "unit": "mg/dL",
            "ref_low": 40,
            "ref_high": 80,
            "measured_at": "2023-05-10",
        },
        {
            "test_code": "LDL",
            "test_name": "LDL Cholesterol",
            "value": 150,
            "unit": "mg/dL",
            "ref_low": None,
            "ref_high": 130,
            "measured_at": "2023-08-20",
        },
        {
            "test_code": "LDL",
            "test_name": "LDL Cholesterol",
            "value": 142,
            "unit": "mg/dL",
            "ref_low": None,
            "ref_high": 130,
            "measured_at": "2023-11-15",
        },
    ]

    reviews = build_semi_annual_reviews(data, today=date(2024, 1, 1))

    assert len(reviews) == 2
    june_review = reviews[0]
    december_review = reviews[1]

    assert june_review["label"] == "June 2023 Semiannual Review"
    assert june_review["metrics"]["measurements"] == 2
    assert june_review["metrics"]["status"]["high"] == 1
    assert any(h["test_code"] == "A1C" for h in june_review["highlights"])

    assert december_review["label"] == "December 2023 Semiannual Review"
    assert december_review["metrics"]["measurements"] == 2
    assert december_review["metrics"]["status"]["high"] == 2


def test_semiannual_reviews_without_data():
    reviews = build_semi_annual_reviews([], today=date(2023, 1, 1))

    assert len(reviews) == 2
    june_review = reviews[0]

    assert june_review["label"] == "June 2023 Semiannual Review"
    assert june_review["metrics"]["measurements"] == 0
    assert "No lab results were recorded" in june_review["summary"]
