locals {
  name = "portfolio-dataflow-${var.environment}"
}

resource "google_project_service" "services" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "dataflow.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "pipeline" {
  location      = var.region
  repository_id = local.name
  format        = "DOCKER"
  depends_on    = [google_project_service.services]
}

resource "google_storage_bucket" "pipeline" {
  name                        = "${var.project_id}-${local.name}"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_pubsub_topic" "events" {
  name       = "${local.name}-events"
  depends_on = [google_project_service.services]
}

resource "google_pubsub_subscription" "events" {
  name  = "${local.name}-events-sub"
  topic = google_pubsub_topic.events.id
}

resource "google_service_account" "worker" {
  account_id   = "dataflow-${var.environment}"
  display_name = "Portfolio Dataflow worker"
}

resource "google_project_iam_member" "worker_roles" {
  for_each = toset([
    "roles/dataflow.worker",
    "roles/pubsub.subscriber",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.worker.email}"
}
