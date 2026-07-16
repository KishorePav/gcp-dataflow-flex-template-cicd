import argparse
import logging

import apache_beam as beam
from apache_beam.io import fileio
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions, StandardOptions
from apache_beam.transforms.window import FixedWindows

from pipeline.transforms import ParseAndValidate


def parse_args(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_subscription", required=True)
    parser.add_argument("--valid_output", required=True)
    parser.add_argument("--invalid_output", required=True)
    known, pipeline_args = parser.parse_known_args(argv)
    return known, pipeline_args


def run(argv=None):
    known, pipeline_args = parse_args(argv)
    options = PipelineOptions(pipeline_args, save_main_session=True, streaming=True)
    options.view_as(StandardOptions).streaming = True
    options.view_as(SetupOptions).save_main_session = True

    with beam.Pipeline(options=options) as pipeline:
        records = pipeline | "Read Pub/Sub" >> beam.io.ReadFromPubSub(
            subscription=known.input_subscription
        )
        results = (
            records
            | "Parse and validate" >> beam.ParDo(ParseAndValidate()).with_outputs(
                ParseAndValidate.VALID,
                ParseAndValidate.INVALID,
            )
        )
        (
            results.valid
            | "Window valid records" >> beam.WindowInto(FixedWindows(60))
            | "Write valid" >> fileio.WriteToFiles(
                path=known.valid_output,
                sink=lambda _: fileio.TextSink(),
                shards=1,
            )
        )
        (
            results.invalid
            | "Window invalid records" >> beam.WindowInto(FixedWindows(60))
            | "Write invalid" >> fileio.WriteToFiles(
                path=known.invalid_output,
                sink=lambda _: fileio.TextSink(),
                shards=1,
            )
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
