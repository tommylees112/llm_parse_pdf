# Google Cloud PDF Processor Setup

This Terraform configuration sets up the necessary Google Cloud resources for the PDF processor application, including:
- A new Google Cloud project
- Google Drive API enabled
- OAuth 2.0 credentials
- Service account with necessary permissions

## Prerequisites

1. Install [Terraform](https://www.terraform.io/downloads.html)
2. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
3. Have a Google Cloud billing account
4. Python 3.9 (required for Google Cloud SDK compatibility)
   ```bash
   # Install Python 3.9 if not already installed
   brew install python@3.9
   
   # Create and activate virtual environment
   python3.9 -m venv .venv
   source .venv/bin/activate
   
   # Reinstall Google Cloud SDK in the virtual environment
   brew uninstall --cask google-cloud-sdk
   brew install --cask google-cloud-sdk
   ```

5. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

## Setup

1. Edit `terraform.tfvars` with your configuration:
   ```hcl
   project_id         = "your-project-id"  # e.g., "gemini-pdf-api"
   project_name       = "PDF Processor"     # e.g., "PDF Processor Project"
   region            = "us-central1"       # e.g., "us-central1"
   billing_account_id = "your-billing-id"   # e.g., "012345-ABCDEF-GHIJKL"
   support_email     = "your-email@example.com"  # e.g., "support@yourdomain.com"
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Review the planned changes:
   ```bash
   terraform plan
   ```

4. Apply the changes:
   ```bash
   terraform apply
   ```

5. After successful application, Terraform will output:
   - OAuth client ID
   - OAuth client secret
   - Service account key

6. Create a `credentials.json` file with the OAuth client credentials:
   ```json
   {
     "web": {
       "client_id": "YOUR_CLIENT_ID",
       "project_id": "YOUR_PROJECT_ID",
       "auth_uri": "https://accounts.google.com/o/oauth2/auth",
       "token_uri": "https://oauth2.googleapis.com/token",
       "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
       "client_secret": "YOUR_CLIENT_SECRET",
       "redirect_uris": ["http://localhost"]
     }
   }
   ```

## Cleanup

To remove all created resources:
```bash
terraform destroy
```

## Notes

- The project ID must be globally unique
- The billing account ID can be found in the Google Cloud Console
- The support email will be used for OAuth consent screen
- Make sure to keep the credentials.json and terraform.tfvars files secure and never commit them to version control
- Add `terraform.tfvars` to your `.gitignore` file to prevent accidental commits
- Python 3.9 is required for Google Cloud SDK compatibility. Using newer Python versions may cause issues with the `imp` module
