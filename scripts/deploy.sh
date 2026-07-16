#!/usr/bin/env bash
set -Eeuo pipefail

required=(GCP_PROJECT_ID GCP_REGION JOB_NAME TEMPLATE_GCS_PATH INPUT_SUBSCRIPTION VALID_OUTPUT INVALID_OUTPUT SERVICE_ACCOUNT SUBNETWORK)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Required environment variable is missing: ${name}" >&2
    exit 1
  fi
done

active_job_id="$(gcloud dataflow jobs list \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --status active \
  --filter="name=${JOB_NAME}" \
  --format='value(id)' \
  --limit=1)"

if [[ -n "$active_job_id" ]]; then
  echo "Cancelling active job ${active_job_id}"
  gcloud dataflow jobs cancel "$active_job_id" \
    --project "$GCP_PROJECT_ID" \
    --region "$GCP_REGION"

  deadline=$((SECONDS + 600))
  while (( SECONDS < deadline )); do
    state="$(gcloud dataflow jobs describe "$active_job_id" \
      --project "$GCP_PROJECT_ID" \
      --region "$GCP_REGION" \
      --format='value(currentState)')"
    case "$state" in
      JOB_STATE_CANCELLED|JOB_STATE_FAILED|JOB_STATE_DRAINED|JOB_STATE_STOPPED)
        echo "Previous job reached terminal state: ${state}"
        break
        ;;
    esac
    sleep 15
  done
  if (( SECONDS >= deadline )); then
    echo "Timed out waiting for ${active_job_id} to stop" >&2
    exit 1
  fi
fi

gcloud dataflow flex-template run "$JOB_NAME" \
  --project "$GCP_PROJECT_ID" \
  --region "$GCP_REGION" \
  --template-file-gcs-location "$TEMPLATE_GCS_PATH" \
  --service-account-email "$SERVICE_ACCOUNT" \
  --subnetwork "$SUBNETWORK" \
  --disable-public-ips \
  --parameters "input_subscription=${INPUT_SUBSCRIPTION},valid_output=${VALID_OUTPUT},invalid_output=${INVALID_OUTPUT}"

