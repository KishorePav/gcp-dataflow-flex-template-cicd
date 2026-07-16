output "artifact_repository" {
  value = google_artifact_registry_repository.pipeline.name
}

output "pipeline_bucket" {
  value = google_storage_bucket.pipeline.name
}

output "input_subscription" {
  value = google_pubsub_subscription.events.id
}

output "worker_service_account" {
  value = google_service_account.worker.email
}

