import json

import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

from pipeline.transforms import ParseAndValidate


def without_timestamp(value: str) -> str:
    record = json.loads(value)
    record.pop("processed_at", None)
    return json.dumps(record, sort_keys=True)


def test_routes_valid_and_invalid_records():
    valid = json.dumps({"event_id": "evt-1", "event_type": "created", "payload": {"id": 7}})
    invalid = json.dumps({"event_id": "evt-2", "payload": {"id": 8}})

    with TestPipeline() as pipeline:
        output = (
            pipeline
            | beam.Create([valid, invalid])
            | beam.ParDo(ParseAndValidate()).with_outputs(
                ParseAndValidate.VALID,
                ParseAndValidate.INVALID,
            )
        )
        normalized_valid = output.valid | "Normalize valid" >> beam.Map(without_timestamp)
        normalized_invalid = output.invalid | "Normalize invalid" >> beam.Map(without_timestamp)

        assert_that(
            normalized_valid,
            equal_to([json.dumps(json.loads(valid), sort_keys=True)]),
            label="Assert valid",
        )
        assert_that(
            normalized_invalid,
            equal_to([
                json.dumps(
                    {"event_id": "evt-2", "payload": {"id": 8}, "reason": "missing fields: event_type"},
                    sort_keys=True,
                )
            ]),
            label="Assert invalid",
        )

