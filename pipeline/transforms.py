import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import apache_beam as beam
from apache_beam.metrics import Metrics


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    payload: dict[str, Any]


class ParseAndValidate(beam.DoFn):
    VALID = "valid"
    INVALID = "invalid"

    def __init__(self) -> None:
        self.processed = Metrics.counter(self.__class__, "processed")
        self.valid = Metrics.counter(self.__class__, "valid")
        self.invalid = Metrics.counter(self.__class__, "invalid")

    def process(self, raw: bytes | str):
        self.processed.inc()
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        try:
            record = json.loads(text)
            result = validate(record)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            result = ValidationResult(False, {"raw": text, "reason": str(exc)})

        result.payload["processed_at"] = datetime.now(timezone.utc).isoformat()
        if result.valid:
            self.valid.inc()
            yield beam.pvalue.TaggedOutput(self.VALID, json.dumps(result.payload))
        else:
            self.invalid.inc()
            yield beam.pvalue.TaggedOutput(self.INVALID, json.dumps(result.payload))


def validate(record: Any) -> ValidationResult:
    if not isinstance(record, dict):
        return ValidationResult(False, {"record": record, "reason": "record must be an object"})

    missing = [field for field in ("event_id", "event_type", "payload") if not record.get(field)]
    if missing:
        return ValidationResult(False, {**record, "reason": f"missing fields: {','.join(missing)}"})

    return ValidationResult(True, record)

