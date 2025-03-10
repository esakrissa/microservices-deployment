#!/bin/bash

# Setup script for Workload Identity Federation with GitHub Actions

echo "Setting up Workload Identity Federation for GitHub Actions..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Login to gcloud if not already logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "Please login to Google Cloud:"
    gcloud auth login
fi

# Set project
echo "Enter your Google Cloud project ID:"
read PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable iamcredentials.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository
echo "Creating Artifact Registry repository..."
REGION=$(gcloud config get-value compute/region)
if [ -z "$REGION" ]; then
    echo "Enter your preferred Google Cloud region (e.g., us-central1):"
    read REGION
    gcloud config set compute/region $REGION
fi

gcloud artifacts repositories create app-images \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository for application images"

# Create service account for GitHub Actions
echo "Creating service account for GitHub Actions..."
SERVICE_ACCOUNT_NAME="github-actions-sa"
SERVICE_ACCOUNT_ID="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_ID" &>/dev/null; then
    echo "Service account $SERVICE_ACCOUNT_ID already exists."
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="GitHub Actions Service Account"
fi

# Grant permissions
echo "Granting necessary permissions to the service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID" \
    --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_ID" \
    --role="roles/redis.admin"

# Setup Workload Identity Federation
echo "Setting up Workload Identity Federation..."

# Create a workload identity pool
POOL_ID="github-actions-pool"
POOL_DISPLAY_NAME="GitHub Actions Pool"

# Check if pool already exists
if ! gcloud iam workload-identity-pools describe "$POOL_ID" --location="global" &>/dev/null; then
    gcloud iam workload-identity-pools create "$POOL_ID" \
        --location="global" \
        --display-name="$POOL_DISPLAY_NAME"
fi

# Get the GitHub repository details
echo "Enter your GitHub username or organization name:"
read GITHUB_OWNER
echo "Enter your GitHub repository name:"
read GITHUB_REPO

# Create a workload identity provider
PROVIDER_ID="github-provider"
PROVIDER_DISPLAY_NAME="GitHub Provider"

# Check if provider already exists
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
    --workload-identity-pool="$POOL_ID" \
    --location="global" &>/dev/null; then
    
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
        --workload-identity-pool="$POOL_ID" \
        --location="global" \
        --display-name="$PROVIDER_DISPLAY_NAME" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --issuer-uri="https://token.actions.githubusercontent.com"
fi

# Allow authentications from the GitHub repository
REPO_NAME="$GITHUB_OWNER/$GITHUB_REPO"
POOL_NAME="projects/$PROJECT_ID/locations/global/workloadIdentityPools/$POOL_ID/providers/$PROVIDER_ID"

gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${REPO_NAME}"

# Output the configuration values for GitHub secrets
echo ""
echo "==== GitHub Secrets Configuration ===="
echo ""
echo "Add the following secrets to your GitHub repository:"
echo ""
echo "WORKLOAD_IDENTITY_PROVIDER: projects/$PROJECT_ID/locations/global/workloadIdentityPools/$POOL_ID/providers/$PROVIDER_ID"
echo "SERVICE_ACCOUNT: $SERVICE_ACCOUNT_ID"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo "GCP_REGION: $REGION"
echo ""
echo "Setup complete!"