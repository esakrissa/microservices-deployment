#!/bin/bash

# Setup script for the deployment project

echo "Setting up deployment project..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Error: Terraform is not installed. Please install it first."
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install it first."
    exit 1
fi

# Login to gcloud
echo "Please login to Google Cloud:"
gcloud auth login
gcloud auth application-default login

# Set project
echo "Enter your Google Cloud project ID:"
read PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable compute.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create service account for GitHub Actions
echo "Creating service account for GitHub Actions..."
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

echo "Service account key saved to key.json. Use this for GitHub Actions."

# Initialize Terraform
echo "Initializing Terraform..."
cd terraform
terraform init

echo "Setup complete! Next steps:"
echo "1. Create a GitHub repository and push this code"
echo "2. Set up GitHub Secrets as described in the README"
echo "3. Run 'terraform apply' to deploy the infrastructure"
echo "4. Update GitHub Secrets with the outputs from Terraform"