#OIDC

```bash
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
```

## Mermaid Diagram Versions

### 1. Flowchart (LR - Left to Right)

```mermaid
flowchart LR
    subgraph GitHub ["GitHub Platform"]
        A[GitHub Actions] --> B[Workflow Job]
    end
    
    subgraph GCP ["Google Cloud Platform"]
        C[Workload Identity Pool] --> D[Workload Identity Provider]
        D --> E[Service Account Impersonation]
        E --> F[GCP Resources]
    end
    
    B -- "OIDC Token" --> D
    
    style GitHub fill:#f9f9f9,stroke:#333,stroke-width:2px
    style GCP fill:#e6f3ff,stroke:#333,stroke-width:2px
```

### 2. Sequence Diagram

```mermaid
sequenceDiagram
    participant GA as GitHub Actions
    participant WF as Workflow Job
    participant WIP as Workload Identity Pool
    participant WIPV as WI Provider
    participant SA as Service Account
    participant GCP as GCP Resources
    
    GA->>WF: Trigger workflow
    WF->>WF: Generate OIDC token
    WF->>WIPV: Present OIDC token
    WIPV->>WIP: Validate token
    WIP->>WIPV: Token valid
    WIPV->>SA: Allow impersonation
    SA->>GCP: Access resources
```

### 3. State Diagram

```mermaid
stateDiagram-v2
    [*] --> WorkflowTriggered
    WorkflowTriggered --> TokenGenerated: GitHub Actions
    TokenGenerated --> TokenPresented: Send to GCP
    TokenPresented --> TokenValidated: Workload Identity Provider
    TokenValidated --> ServiceAccountImpersonated: If valid
    ServiceAccountImpersonated --> ResourcesAccessed: Temporary credentials
    ResourcesAccessed --> [*]
    
    TokenValidated --> AuthFailed: If invalid
    AuthFailed --> [*]
```