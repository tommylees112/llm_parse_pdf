terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
}

# Configure the Google Cloud provider
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# Enable the Google Drive API
resource "google_project_service" "drive_api" {
  project = var.project_id
  service = "drive.googleapis.com"

  disable_on_destroy = false
}

# Create OAuth consent screen
resource "google_iap_brand" "project_brand" {
  support_email     = var.support_email
  application_title = "PDF Processor"
  project          = var.project_id
}

resource "google_iap_client" "project_client" {
  display_name = "PDF Processor Client"
  brand        = google_iap_brand.project_brand.name
}

# Create OAuth 2.0 Client ID
resource "google_iap_client" "oauth_client" {
  display_name = "PDF Processor OAuth Client"
  brand        = google_iap_brand.project_brand.name
}

# Create service account
resource "google_service_account" "pdf_processor_sa" {
  account_id   = "pdf-processor-sa"
  display_name = "PDF Processor Service Account"
  project      = var.project_id
}

# Create service account key
resource "google_service_account_key" "pdf_processor_sa_key" {
  service_account_id = google_service_account.pdf_processor_sa.name
}

# Grant necessary permissions to the service account
resource "google_project_iam_member" "service_account_permissions" {
  for_each = toset([
    "roles/drive.readonly",
    "roles/iam.serviceAccountUser"
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.pdf_processor_sa.email}"
}

# Output the OAuth client credentials
output "oauth_client_id" {
  value     = google_iap_client.oauth_client.client_id
  sensitive = true
}

output "oauth_client_secret" {
  value     = google_iap_client.oauth_client.secret
  sensitive = true
}

# Output service account key
output "service_account_key" {
  value     = google_service_account_key.pdf_processor_sa_key.private_key
  sensitive = true
} 