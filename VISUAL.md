#OIDC

External Platform                 |                Google Cloud Platform
---------------------------------|------------------------------------------
                                 |
GitHub Actions                   |  Workload Identity Pool (github-actions)
  |                              |    |
  | issues OIDC token            |    | contains
  |                              |    |
  v                              |    v
Workflow Job ----token-----> Workload Identity Provider (github)
                                 |    |
                                 |    | validates & maps attributes
                                 |    |
                                 |    v
                                 |  Service Account Impersonation
                                 |    |
                                 |    | grants temporary access
                                 |    |
                                 |    v
                                 |  GCP Resources (Cloud Run, GKE, etc.)