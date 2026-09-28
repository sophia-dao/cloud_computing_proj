# AWS Architecture

## 1. Purpose

This document describes the AWS infrastructure and deployment architecture for the Recipe Suggestion App.

The infrastructure is designed to support:

- React frontend hosting.
- Django REST API hosting.
- Docker-based backend deployment.
- PostgreSQL database hosting.
- Persistent media storage.
- User authentication.
- Container image storage.
- Application secrets.
- Logging and monitoring.
- Continuous integration and deployment.

The initial architecture intentionally prioritizes simplicity and maintainability while preserving the ability to scale later.

---

# 2. AWS Services

The initial architecture uses the following services:

| Service | Purpose |
| --- | --- |
| Amazon S3 | React frontend files and application media |
| Amazon CloudFront | Frontend content delivery |
| Amazon EC2 | Django backend hosting |
| Amazon ECR | Docker image registry |
| Amazon RDS | Managed PostgreSQL database |
| Amazon Cognito | User authentication |
| AWS Secrets Manager | Application secrets |
| Amazon CloudWatch | Logging and monitoring |

GitHub Actions may additionally be used for automated testing, builds, and deployment.

---

# 3. High-Level AWS Architecture

```text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │   CloudFront    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │       S3        │
                  │ React Frontend  │
                  └────────┬────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      Amazon Cognito                REST API
      Authentication                    │
                                        ▼
                              ┌─────────────────┐
                              │   Amazon EC2    │
                              │                 │
                              │     Docker      │
                              │       │         │
                              │       ▼         │
                              │ Django + DRF    │
                              └────────┬────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
                ┌────────────────┐          ┌──────────────┐
                │   Amazon RDS   │          │  Amazon S3   │
                │   PostgreSQL   │          │    Media     │
                └────────────────┘          └──────────────┘
```

Supporting infrastructure includes:

```text
Amazon ECR
    │
    └── Django Docker Images

AWS Secrets Manager
    │
    └── Application Secrets

Amazon CloudWatch
    │
    └── Logs / Monitoring
```

---

# 4. Frontend Hosting

The React frontend will be built into static production files.

The production build will be stored in Amazon S3.

```text
React Source
     │
     ▼
Production Build
     │
     ▼
Amazon S3
     │
     ▼
Amazon CloudFront
     │
     ▼
User
```

CloudFront acts as the frontend content-delivery layer.

This separates frontend hosting from backend application execution.

The frontend does not require an EC2 server because the compiled React application consists primarily of static assets.

---

# 5. S3 Storage Separation

The application should use logically separate S3 storage for frontend application files and persistent application media.

Conceptually:

```text
Amazon S3
│
├── Frontend Storage
│   ├── index.html
│   ├── JavaScript
│   ├── CSS
│   └── Static Assets
│
└── Media Storage
    ├── Recipe Images
    ├── User Avatars
    └── Other Supported Media
```

These resources serve different purposes and may require different access policies.

Application media shall remain independent from EC2 so uploaded files survive backend deployment, container replacement, or EC2 replacement.

---

# 6. Authentication

Amazon Cognito will provide user authentication.

Initial supported authentication methods include:

- Google sign-in.
- Email/password registration.
- Email verification.
- Login and logout.

Conceptually:

```text
User
 │
 ▼
React
 │
 ▼
Amazon Cognito
 │
 ▼
Authenticated Identity
 │
 ▼
React
 │
 │ Authenticated Request
 ▼
Django REST API
```

Cognito establishes authenticated identity.

Django remains responsible for application-specific authorization.

---

# 7. Backend Hosting

The Django REST Framework backend will run inside a Docker container hosted on Amazon EC2.

```text
Amazon EC2
     │
     ▼
Docker Engine
     │
     ▼
Django Container
     │
     ▼
Django REST API
```

The EC2 instance provides the compute environment.

Docker provides a consistent backend runtime environment between development and deployment.

Persistent application information shall not depend on the EC2 instance or Docker container filesystem.

---

# 8. Docker Image Registry

Amazon Elastic Container Registry (ECR) will store backend Docker images.

Deployment flow:

```text
Django Source
     │
     ▼
Docker Build
     │
     ▼
Docker Image
     │
     ▼
Amazon ECR
     │
     ▼
Amazon EC2
     │
     ▼
docker pull
     │
     ▼
Run Django Container
```

Using ECR provides a centralized AWS-hosted container registry for backend deployment.

---

# 9. Database

The application will use PostgreSQL hosted through Amazon RDS.

```text
Django
   │
   ▼
Amazon RDS
   │
   ▼
PostgreSQL
```

RDS stores persistent relational application data including:

- Application users.
- User profiles.
- Ingredient information.
- User inventories.
- Recipes.
- Recipe ingredient relationships.
- Saved recipes.
- Reviews.
- Shopping lists.
- Allergies.
- Dietary preferences.

Database data shall remain independent of the EC2 instance.

Replacing or restarting the backend container shall not remove persistent database information.

---

# 10. Media Storage

Recipe images, avatars, and other supported media shall be stored in Amazon S3 rather than on the EC2 filesystem.

```text
Django
   │
   ├── Recipe Data ────────→ RDS
   │
   └── Recipe Image ───────→ S3
```

The database maintains the information required to associate media with application entities.

This prevents application media from being lost when containers or EC2 instances are replaced.

---

# 11. Networking

The application will use an AWS Virtual Private Cloud (VPC).

The initial networking design should remain relatively simple.

Conceptually:

```text
                    Internet
                       │
                       ▼
                 Public Access
                       │
                       ▼
                  EC2 Backend
                       │
                       │ PostgreSQL
                       ▼
                     RDS
```

The backend requires network access to the database.

The database should not require direct public access from application users.

---

# 12. Security Groups

AWS Security Groups shall restrict network access between resources.

Conceptually:

```text
Internet
   │
   │ HTTPS / required backend traffic
   ▼
EC2 Security Group
   │
   │ PostgreSQL : 5432
   ▼
RDS Security Group
```

The RDS security group should allow PostgreSQL traffic from the backend EC2 security group rather than from the entire Internet.

Conceptually:

```text
RDS PostgreSQL

Allow:
EC2 Backend Security Group
Port 5432

Do Not Allow:
0.0.0.0/0 → Port 5432
```

This prevents users on the public Internet from directly connecting to the production database.

---

# 13. Database Accessibility

Amazon RDS should not be publicly exposed for the deployed application.

Application database access should flow through the backend:

```text
User
 │
 ▼
React
 │
 ▼
Django API
 │
 ▼
RDS
```

Not:

```text
User ───────────X──────────→ RDS
```

React shall never directly communicate with PostgreSQL.

---

# 14. Secrets Management

Sensitive configuration should not be committed to GitHub or embedded directly in application source code.

Sensitive information may include:

- Database credentials.
- Django secret keys.
- External API credentials.
- Storage credentials where required.
- Other production secrets.

AWS Secrets Manager may be used to securely store production secrets.

Conceptually:

```text
Secrets Manager
      │
      ▼
EC2 / Django
      │
      ▼
Application Configuration
```

Local development may use appropriate local environment configuration.

Production secrets shall not be committed to the repository.

---

# 15. IAM

AWS Identity and Access Management (IAM) should provide AWS resources with only the permissions required for their responsibilities.

For example, the EC2 backend may require permission to:

- Pull backend images from ECR.
- Access the application's media S3 bucket.
- Retrieve required application secrets.
- Send supported logging information.

Permissions should follow the principle of least privilege.

The backend should not receive unrestricted administrative access to the AWS account.

---

# 16. Logging and Monitoring

Amazon CloudWatch may be used for backend logging and infrastructure monitoring.

Relevant information may include:

- Application logs.
- Backend errors.
- EC2 resource utilization.
- Deployment troubleshooting information.

Conceptually:

```text
Django / EC2
      │
      ▼
CloudWatch
      │
      ├── Logs
      └── Monitoring
```

Application logs should not intentionally expose passwords, authentication tokens, or other sensitive information.

---

# 17. Local Development

Developers should be able to run the application locally without requiring every request to use production AWS infrastructure.

Conceptually:

```text
Developer Computer

React
 │
 ▼
localhost

Django
 │
 ▼
localhost:8000

PostgreSQL
 │
 ▼
Local Development Database
```

Docker may be used locally for backend development where appropriate.

The same Django application can later run inside Docker on EC2.

Environment-specific configuration should determine which external resources are used.

---

# 18. Environment Configuration

Application configuration should differ between development and deployed environments without requiring major source-code changes.

Example:

```text
Development
───────────
DEBUG=true
Local PostgreSQL
Local API URL


AWS Deployment
──────────────
DEBUG=false
RDS PostgreSQL
S3 Media
Production API URL
AWS Secrets
```

Configuration should primarily be supplied through environment variables or secure configuration mechanisms.

---

# 19. Deployment Process

The initial deployment process is:

```text
GitHub
   │
   ▼
Tests
   │
   ├────────────────────────────┐
   │                            │
   ▼                            ▼
Frontend                    Backend
   │                            │
   ▼                            ▼
React Build                 Docker Build
   │                            │
   ▼                            ▼
S3                          Amazon ECR
   │                            │
   ▼                            ▼
CloudFront                  Amazon EC2
                                │
                                ▼
                           Pull Image
                                │
                                ▼
                         Run Container
```

The process may initially contain some manual deployment steps.

Automation can be added incrementally through GitHub Actions.

---

# 20. Continuous Integration

GitHub Actions may be used to automatically run application tests.

Conceptually:

```text
Developer
    │
    ▼
Pull Request
    │
    ▼
GitHub Actions
    │
    ├── Backend Tests
    ├── API Tests
    └── Frontend Tests
```

Changes should pass required tests before being merged where practical.

---

# 21. Continuous Deployment

Deployment automation may later extend the CI pipeline.

For example:

```text
Merge to Main
      │
      ▼
GitHub Actions
      │
      ├── Build React
      │       │
      │       ▼
      │      S3
      │       │
      │       ▼
      │   CloudFront
      │
      └── Build Docker
              │
              ▼
             ECR
              │
              ▼
             EC2
              │
              ▼
        Restart Backend
```

The initial project does not require a fully automated production deployment pipeline before basic application functionality is working.

---

# 22. Persistence Design

The backend EC2 instance and Docker container should be treated as replaceable compute resources.

Persistent state is externalized:

```text
                     EC2
                      │
                Django Container
                      │
             ┌────────┴────────┐
             ▼                 ▼
            RDS                S3
         Database             Media
```

Therefore:

```text
EC2 replaced
     │
     ▼
New EC2
     │
     ├── Connect to existing RDS
     └── Connect to existing S3
```

Application data remains available.

This design also makes future backend scaling easier.

---

# 23. Initial Scaling Strategy

The initial project will use a single EC2 backend instance.

```text
Internet
   │
   ▼
EC2
   │
   ▼
Django
```

This is sufficient for the expected project workload and keeps deployment manageable.

The system is intentionally designed so persistent application state does not depend on the EC2 instance.

---

# 24. Future Scaling

If usage increases, the backend architecture may later evolve to support multiple application instances.

For example:

```text
                  Load Balancer
                 /             \
                ▼               ▼
             EC2 #1           EC2 #2
             Django           Django
                │               │
                └───────┬───────┘
                        ▼
                  RDS + S3
```

Possible future AWS infrastructure may include:

- Application Load Balancer.
- EC2 Auto Scaling.
- Multiple backend instances.
- Database scaling.
- Caching.
- Additional CloudFront usage.

These components are not required for the initial implementation.

---

# 25. Architecture Principles

The AWS deployment should follow these principles:

1. Keep the initial infrastructure understandable and maintainable.
2. Keep persistent data outside backend containers.
3. Use RDS for relational application data.
4. Use S3 for persistent application media.
5. Use Cognito for authentication.
6. Use EC2 as the initial backend compute platform.
7. Use Docker to provide a consistent backend runtime.
8. Use ECR to store backend Docker images.
9. Do not expose PostgreSQL directly to application users.
10. Restrict AWS resource access using security groups and IAM.
11. Do not commit production secrets to GitHub.
12. Keep application-specific data in PostgreSQL rather than Cognito.
13. Design the backend so EC2 instances can eventually be replaced or scaled.
14. Add infrastructure complexity only when it solves an actual project requirement.

---

# 26. Initial vs. Future Architecture

## Initial Implementation

```text
Frontend       → S3 + CloudFront
Authentication → Cognito
Backend        → EC2 + Docker
Docker Images  → ECR
Database       → RDS PostgreSQL
Media          → S3
Secrets        → Secrets Manager
Monitoring     → CloudWatch
```

## Potential Future Architecture

```text
Frontend       → S3 + CloudFront
Authentication → Cognito

                    Load Balancer
                    /           \
                 EC2             EC2
                  │               │
                  └───────┬───────┘
                          ▼
                       RDS + S3
```

Future infrastructure should only be introduced when required by application load, availability requirements, or project objectives.

---

# 27. Related Documentation

```text
README.md
    High-level project overview

requirements.md
    Functional and non-functional requirements

system-design.md
    Application architecture and design philosophy

database-design.md
    Persistent data model

api-design.md
    Frontend-backend API contract

aws-architecture.md
    AWS infrastructure and deployment design
```