# AWS Architecture

## 1. Purpose

This document describes the AWS cloud architecture for the Recipe Suggestion App.

The architecture supports:

- React frontend hosting.
- Django REST Framework backend hosting.
- Docker-based backend deployment.
- PostgreSQL relational data storage.
- Persistent media storage.
- Amazon Cognito authentication.
- Docker image storage.
- Secret management.
- Application logging and monitoring.
- Future horizontal scaling.

The initial architecture prioritizes simplicity and practical implementation for the current project while preserving a clear path toward future scalability.

---

# 2. AWS Service Summary

The initial architecture uses the following AWS services:

| AWS Service | Purpose |
| --- | --- |
| Amazon S3 | React static files and application media |
| Amazon CloudFront | Frontend content delivery |
| Amazon EC2 | Django REST backend hosting |
| Amazon ECR | Docker image storage |
| Amazon RDS for PostgreSQL | Persistent relational database |
| Amazon Cognito | User authentication |
| AWS Secrets Manager | Sensitive configuration and credentials |
| Amazon CloudWatch | Logging and monitoring |
| Amazon VPC | Network isolation and security boundaries |

The initial deployment does not require:

- Application Load Balancer.
- EC2 Auto Scaling Group.
- Multiple Django backend instances.
- Multi-region deployment.
- Microservices.

These may be introduced later if application traffic or availability requirements increase.

---

# 3. High-Level AWS Architecture

The initial cloud architecture is:

```text
                         Users
                           │
                           ▼
                    Amazon CloudFront
                           │
                           ▼
                       Amazon S3
                    React Frontend
                           │
                           │ HTTPS / REST
                           ▼
                     Amazon EC2
                  ┌─────────────────┐
                  │ Docker Container │
                  │                 │
                  │ Django REST API │
                  └─────────────────┘
                           │
             ┌─────────────┼─────────────┐
             │             │             │
             ▼             ▼             ▼
        Amazon RDS      Amazon S3    Amazon Cognito
        PostgreSQL        Media      Authentication
             │
             │
             ▼
      Persistent Data


Docker Deployment:
Developer / CI
      │
      ▼
 Docker Image
      │
      ▼
 Amazon ECR
      │
      ▼
 Amazon EC2


Supporting Services:

AWS Secrets Manager
        │
        ▼
   Django Backend

Amazon CloudWatch
        ▲
        │
 EC2 / Django Logs
```

---

# 4. Architecture Principles

The AWS architecture follows several core principles.

## 4.1 Separate Compute from Persistent Data

Persistent application data must remain outside the Django container.

```text
Django Container
      │
      ├── PostgreSQL → Amazon RDS
      │
      └── Media      → Amazon S3
```

This allows the backend container to be:

- Restarted.
- Replaced.
- Redeployed.
- Rebuilt.
- Scaled.

without losing application data.

---

## 4.2 Keep the Backend Stateless Where Practical

The Django backend should not depend on local server files or local memory for authoritative persistent application state.

Persistent state belongs in external AWS services.

```text
Application Data
      ↓
Amazon RDS

Media
      ↓
Amazon S3

Authentication Identity
      ↓
Amazon Cognito
```

This supports future horizontal scaling.

---

## 4.3 Separate Authentication from Application Data

Amazon Cognito manages authentication identity.

Django and PostgreSQL manage application-specific user data.

```text
Amazon Cognito
      │
      │ authenticated identity
      ▼
Django
      │
      ▼
Application User
      │
      ▼
Amazon RDS
```

Application data such as:

```text
Profiles
Inventory
Preferences
Allergies
Saved Recipes
Reviews
Shopping Lists
```

belongs in PostgreSQL rather than Cognito.

---

## 4.4 Use Managed Services Where Practical

Managed AWS services should be used for infrastructure responsibilities that do not need to be implemented manually.

Examples:

```text
Database       → Amazon RDS
Authentication → Amazon Cognito
Object Storage → Amazon S3
Image Registry → Amazon ECR
Monitoring     → Amazon CloudWatch
Secrets        → AWS Secrets Manager
```

This reduces infrastructure management complexity.

---

# 5. Frontend Architecture

The React frontend is built into static production files.

Conceptually:

```text
React Source
     │
     ▼
npm build
     │
     ▼
Static Files
     │
     ▼
Amazon S3
     │
     ▼
Amazon CloudFront
     │
     ▼
Users
```

Amazon S3 stores the built frontend assets.

Amazon CloudFront distributes those assets to users.

---

# 6. Amazon S3 Frontend Hosting

The production React build is stored in an S3 bucket.

Typical files include:

```text
index.html
JavaScript bundles
CSS
Images
Other static assets
```

The frontend S3 bucket is intended to contain deployment artifacts rather than application database data.

CloudFront should serve as the public frontend delivery layer.

---

# 7. Amazon CloudFront

CloudFront provides frontend content delivery.

Conceptually:

```text
User
 │
 ▼
CloudFront
 │
 ▼
S3 Frontend Bucket
```

Benefits include:

- HTTPS delivery.
- Edge caching.
- Reduced direct exposure of frontend storage.
- Improved static-content delivery.
- A stable public frontend endpoint.

CloudFront is part of the initial frontend architecture.

---

# 8. Backend Architecture

The Django REST Framework backend runs inside a Docker container hosted on Amazon EC2.

```text
Amazon EC2
    │
    ▼
Docker Runtime
    │
    ▼
Django REST API
```

The initial deployment uses one EC2 backend instance.

This keeps the project deployment simple while preserving the ability to introduce additional instances later.

---

# 9. Docker Backend

The backend is packaged as a Docker image.

Conceptually:

```text
Django Source Code
       │
       ▼
    Dockerfile
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
Docker Container
```

The Docker image should contain:

- Django application code.
- Python runtime.
- Python dependencies.
- Required backend runtime configuration.

The image should not contain:

- Production database contents.
- Persistent uploaded media.
- Hardcoded production credentials.

---

# 10. Amazon ECR

Amazon Elastic Container Registry stores backend Docker images.

Deployment flow:

```text
Developer / CI
      │
      ▼
Build Docker Image
      │
      ▼
Push Image
      │
      ▼
Amazon ECR
      │
      ▼
Amazon EC2
      │
      ▼
Pull Image
      │
      ▼
Run Container
```

Using ECR provides a centralized location for backend deployment images.

EC2 should receive only the IAM permissions required to pull the appropriate images.

---

# 11. Amazon EC2

Amazon EC2 hosts the Dockerized Django backend.

Initial architecture:

```text
Amazon EC2
┌─────────────────────┐
│                     │
│   Docker Runtime    │
│         │           │
│         ▼           │
│   Django REST API   │
│                     │
└─────────────────────┘
```

The EC2 instance provides backend compute resources.

The backend communicates with:

```text
Amazon RDS
Amazon S3
Amazon Cognito
AWS Secrets Manager
Amazon CloudWatch
```

where required.

The EC2 instance should not be treated as persistent application storage.

---

# 12. Backend Deployment Flow

A typical backend deployment follows:

```text
Developer
   │
   ▼
Git Repository
   │
   ▼
Build / Test
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
Pull Updated Image
   │
   ▼
Restart / Replace Container
```

This allows the application runtime to be replaced without replacing persistent application data.

---

# 13. Database Architecture

Amazon RDS for PostgreSQL stores persistent relational application data.

```text
Django REST API
       │
       ▼
 Amazon RDS
 PostgreSQL
```

Persistent data includes:

```text
Users
User Profiles
Ingredients
Inventory Items
Recipes
Recipe Ingredients
Saved Recipes
Tags
User Preferences
Allergens
User Allergies
Reviews
Shopping Lists
Shopping List Items
```

Detailed database relationships are defined in `database-design.md`.

---

# 14. Why Amazon RDS

Amazon RDS is used instead of storing PostgreSQL directly inside the EC2 instance or Docker container.

This separates application compute from persistent relational storage.

```text
Incorrect:

EC2
 └── Docker
      ├── Django
      └── PostgreSQL


Architecture:

EC2
 └── Docker
      └── Django
           │
           ▼
        Amazon RDS
```

This provides a cleaner architecture and allows backend instances to be replaced independently of the database.

---

# 15. Database Network Access

The PostgreSQL database should not be publicly exposed to the internet.

Conceptually:

```text
Internet
   │
   ▼
Backend Entry Point
   │
   ▼
EC2 / Django
   │
   │ PostgreSQL connection
   ▼
Amazon RDS
```

RDS access should be restricted using security groups.

Conceptually:

```text
RDS Security Group

Inbound PostgreSQL:
Source → Backend EC2 Security Group
Port   → PostgreSQL database port
```

The database should not accept unrestricted internet traffic.

---

# 16. Amazon Cognito

Amazon Cognito provides authentication for Registered Users.

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
 │ Authenticate
 ▼
Authentication Token
 │
 ▼
React
 │
 │ Authenticated API Request
 ▼
Django REST API
```

Django validates authenticated identity and maps it to the corresponding application User.

---

# 17. Cognito vs. Django Responsibilities

Authentication and authorization remain separate.

```text
Amazon Cognito
      │
      └── Authentication
          "Who is this user?"


Django
      │
      └── Authorization
          "What may this user do?"
```

Cognito is responsible for:

- Authentication identity.
- Authentication credentials.
- Authentication tokens.
- Supported account authentication workflows.

Django is responsible for:

- Application User mapping.
- Resource ownership.
- User permissions.
- Administrator permissions.
- Private-data access.
- Protected API operations.

---

# 18. Application User Mapping

The authenticated Cognito identity is mapped to an application User.

```text
Cognito Identity
       │
       │ stable external identifier
       ▼
     Django
       │
       ▼
Application User
       │
       ▼
Amazon RDS
```

The application User may then be associated with:

```text
Profile
Inventory
UserPreferences
UserAllergies
SavedRecipes
Reviews
ShoppingLists
Owned Recipes
```

The application database does not need to store user passwords.

---

# 19. Media Storage

Application media is stored in Amazon S3.

Examples include:

- Recipe images.
- User profile images.

Conceptually:

```text
User / React
     │
     ▼
Django API
     │
     ▼
Amazon S3
     │
     ▼
Media Object
```

PostgreSQL stores the information required to reference the media object.

```text
Recipe
├── database fields
└── image_reference ─────→ Amazon S3


UserProfile
├── database fields
└── profile_image_reference ─────→ Amazon S3
```

Large image binaries should not be stored directly in PostgreSQL.

---

# 20. Frontend and Media S3 Separation

The application may use separate S3 buckets or appropriately separated storage locations for:

```text
Frontend Deployment Files
          │
          ▼
         S3


Application Media
          │
          ▼
         S3
```

These resources have different responsibilities and may require different access policies.

Frontend assets are deployment artifacts.

Application media is runtime application content.

---

# 21. AWS Secrets Manager

Sensitive production configuration should not be committed directly to the Git repository or hardcoded into the Docker image.

Examples include:

```text
Database credentials
Django secret values
External service credentials
Other sensitive configuration
```

Conceptually:

```text
AWS Secrets Manager
        │
        ▼
   EC2 / Django
        │
        ▼
Runtime Configuration
```

The EC2 environment should receive only the IAM permissions required to retrieve the necessary secrets.

---

# 22. Configuration Management

Application configuration should distinguish between:

```text
Local Development
AWS Development / Testing
Production
```

Non-sensitive configuration may use environment variables or deployment configuration.

Sensitive production values should use appropriate secret-management mechanisms.

Production secrets must not be committed to Git.

---

# 23. IAM

AWS Identity and Access Management controls access between AWS resources.

The architecture should follow least-privilege principles.

For example, the EC2 backend may require permission to:

```text
Pull Docker images from ECR
Access required media objects in S3
Read required Secrets Manager secrets
Write logs or metrics where configured
```

The backend should not receive unnecessary permissions to unrelated AWS resources.

---

# 24. Security Groups

Security groups provide network-level access control.

Conceptually:

```text
Internet
   │
   ▼
Backend Security Group
   │
   ▼
EC2
   │
   ▼
Database Security Group
   │
   ▼
RDS
```

The initial backend security group should allow only the network access required for application operation and administration.

The RDS security group should allow database connections from the backend security group rather than from arbitrary public IP addresses.

---

# 25. VPC Architecture

EC2 and RDS operate within an Amazon VPC.

At a high level:

```text
Amazon VPC
│
├── Backend Compute
│      └── EC2
│
└── Database
       └── RDS PostgreSQL
```

Network configuration should prevent direct public database access.

The exact subnet architecture may evolve as the deployment becomes more advanced.

For the initial project, the network should remain as simple as possible while preserving appropriate database isolation.

---

# 26. Backend Public Access

The initial deployment uses a single EC2 backend.

Therefore, the backend API may initially be reached through the EC2-hosted application endpoint.

Conceptually:

```text
React Frontend
      │
      │ HTTPS API Requests
      ▼
EC2 Backend
      │
      ▼
Django
```

This is the initial implementation architecture.

A future production-scale architecture may place an Application Load Balancer in front of EC2 instances.

---

# 27. CORS

Because the React frontend and Django backend may be hosted on different origins, Django must configure Cross-Origin Resource Sharing appropriately.

Conceptually:

```text
CloudFront Frontend
       │
       │ HTTPS API Request
       ▼
Django Backend
       │
       ▼
CORS Validation
```

Production CORS configuration should allow approved frontend origins rather than unrestricted origins.

---

# 28. HTTPS

Production communication should use HTTPS.

Important communication paths include:

```text
User → CloudFront
React → Django API
React → Cognito
```

Database communication and AWS service communication should use secure supported connections where appropriate.

HTTPS protects application traffic in transit.

---

# 29. Amazon CloudWatch

Amazon CloudWatch provides application and infrastructure monitoring.

Possible monitored information includes:

```text
EC2 resource utilization
Application logs
Backend errors
Deployment problems
Database-related alarms
```

Conceptually:

```text
EC2 / Django
     │
     ▼
CloudWatch
     │
     ├── Logs
     ├── Metrics
     └── Alarms
```

CloudWatch allows the team to diagnose problems without relying only on direct EC2 terminal access.

---

# 30. Logging

Backend logs should provide useful operational information without exposing sensitive information.

Logs may include:

```text
Application errors
Request failures
Deployment problems
Authentication validation failures
Unexpected service errors
```

Logs should not intentionally expose:

```text
Passwords
Authentication tokens
Database passwords
Sensitive secret values
```

CloudWatch can serve as the centralized location for deployed backend logs.

---

# 31. Initial Deployment Architecture

The initial project deployment intentionally remains simple.

```text
                         Users
                           │
                           ▼
                       CloudFront
                           │
                           ▼
                    S3 React Frontend
                           │
                           ▼
                    Single EC2 Instance
                           │
                           ▼
                    Dockerized Django
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        RDS PostgreSQL    S3 Media     Cognito
```

Supporting services:

```text
ECR
Secrets Manager
CloudWatch
```

This architecture is sufficient for the initial application while demonstrating separation between:

- Frontend.
- Backend compute.
- Database.
- Authentication.
- Media.
- Deployment artifacts.

---

# 32. Why Start with One EC2 Instance

The initial system uses one EC2 backend instance because:

- The application is a class project.
- Initial traffic is expected to be limited.
- Deployment remains easier to understand and demonstrate.
- Infrastructure complexity remains manageable.
- Docker already provides a reproducible backend runtime.
- The architecture can be extended later without redesigning the application.

Starting with one instance does not mean the architecture is permanently limited to one instance.

---

# 33. Statelessness and Future Scaling

The backend is designed so that additional Django instances may be introduced later.

Because persistent state exists outside EC2:

```text
Database → RDS
Media    → S3
Identity → Cognito
```

a future architecture may run multiple equivalent backend instances.

```text
              Django Instance A
             /
Requests ───┼── Django Instance B
             \
              Django Instance C
                      │
                      ▼
                  Amazon RDS
```

No individual backend instance should contain authoritative persistent user data.

---

# 34. Future Application Load Balancer

If backend traffic increases, an Application Load Balancer may be introduced.

Future architecture:

```text
Clients
   │
   ▼
Application Load Balancer
   │
   ├── EC2 Instance A
   ├── EC2 Instance B
   └── EC2 Instance C
```

The load balancer distributes requests across healthy backend instances.

An ALB is a future scalability component and is not required for the initial deployment.

---

# 35. Future EC2 Auto Scaling

An EC2 Auto Scaling Group may later manage backend capacity.

Conceptually:

```text
Application Load Balancer
          │
          ▼
   Auto Scaling Group
      │    │    │
      ▼    ▼    ▼
     EC2  EC2  EC2
```

Auto Scaling may:

- Add backend instances when additional capacity is required.
- Remove instances when capacity is no longer needed.
- Replace unhealthy instances.
- Distribute instances across multiple Availability Zones.

The stateless backend architecture makes this possible.

Auto Scaling is not required for the initial project deployment.

---

# 36. Availability Zones

The initial backend may operate from a single EC2 instance.

A future higher-availability architecture may distribute backend instances across multiple Availability Zones.

```text
              Application Load Balancer
                     /          \
                    /            \
                   ▼              ▼
                AZ-A             AZ-B
                  │                │
                  ▼                ▼
             EC2 Instance    EC2 Instance
```

An Auto Scaling Group can launch instances across configured Availability Zones.

This reduces dependence on a single backend instance or Availability Zone.

---

# 37. Future Database Availability and Scaling

The initial database uses Amazon RDS for PostgreSQL.

Future requirements may justify additional RDS capabilities such as:

```text
Multi-AZ deployment
Larger database instance classes
Read replicas where appropriate
Storage scaling
Database monitoring improvements
```

These capabilities should be introduced when justified by availability or performance requirements rather than enabled only for architectural complexity.

---

# 38. Independent Scaling

The architecture separates major components so they can scale independently.

```text
Frontend
   │
   └── S3 + CloudFront

Backend
   │
   └── EC2
       └── Future Auto Scaling

Database
   │
   └── RDS

Media
   │
   └── S3

Authentication
   │
   └── Cognito
```

For example, increasing backend compute capacity does not require moving application media out of the backend because media is already stored in S3.

---

# 39. Scalability Example

Initial system:

```text
100 users
   │
   ▼
CloudFront
   │
   ▼
1 EC2 Backend
   │
   ▼
RDS
```

If usage grows:

```text
More Users
    │
    ▼
CloudFront
    │
    ▼
Application Load Balancer
    │
    ▼
Auto Scaling Group
 ┌────┼────┐
 ▼    ▼    ▼
EC2  EC2  EC2
 │    │    │
 └────┼────┘
      ▼
     RDS
```

The exact number of instances depends on measured application demand.

The architecture should scale based on observed metrics rather than fixed assumptions.

---

# 40. Recommendation Service Scaling

Recommendation logic initially runs within the Django backend.

```text
API Request
     │
     ▼
Django
     │
     ▼
RecommendationService
     │
     ▼
PostgreSQL
```

This is appropriate for the initial application.

Because RecommendationService is separated at the application layer, future optimization may include:

- Database query optimization.
- Caching.
- Additional backend instances.
- Background processing for expensive future operations.

A separate recommendation microservice is not required for the initial implementation.

---

# 41. Media Scaling

Amazon S3 provides persistent object storage independently of backend compute.

```text
Many Users
    │
    ▼
Application
    │
    ▼
Amazon S3
```

Media therefore does not need to be duplicated across EC2 instances.

This is especially important if the backend later scales horizontally.

---

# 42. Database Backup and Recovery

The RDS deployment should use appropriate database backup capabilities.

Persistent application data should not depend on EC2 disk state.

Conceptually:

```text
EC2 Failure
    │
    ▼
Backend Replaced
    │
    ▼
Reconnect to RDS
    │
    ▼
Application Data Remains
```

The exact backup retention and recovery configuration may be selected during deployment.

---

# 43. EC2 Failure Behavior

Because EC2 does not contain authoritative persistent application data, replacing the backend instance should not destroy:

```text
Users
Recipes
Inventory
Reviews
Shopping Lists
Media
```

Those resources remain in external persistent services.

```text
Failed EC2
    │
    X

Replacement EC2
    │
    ├── Pull Docker Image from ECR
    ├── Retrieve required configuration
    ├── Connect to RDS
    ├── Connect to S3
    └── Resume Django service
```

This separation improves recoverability.

---

# 44. CI/CD Direction

The architecture supports future automated deployment.

Conceptually:

```text
Developer
   │
   ▼
Git Push / Pull Request
   │
   ▼
GitHub Actions
   │
   ├── Run Tests
   │
   └── Build Docker Image
             │
             ▼
         Amazon ECR
             │
             ▼
         Amazon EC2
```

The exact deployment automation may evolve during implementation.

CI/CD should not bypass testing or expose production credentials.

---

# 45. Security Architecture

The major security controls are:

```text
Authentication
      │
      ▼
Amazon Cognito


Authorization
      │
      ▼
Django


Network Access
      │
      ▼
VPC + Security Groups


Secrets
      │
      ▼
AWS Secrets Manager


Database Isolation
      │
      ▼
RDS not publicly exposed


Media / Object Access
      │
      ▼
S3 + IAM Policies


Transport Security
      │
      ▼
HTTPS
```

Security is therefore enforced at multiple layers rather than relying on a single service.

---

# 46. Trust Boundaries

The browser is not trusted to make authoritative authorization decisions.

Conceptually:

```text
Browser / React
      │
      │ untrusted client input
      ▼
Django API
      │
      ├── Authentication Validation
      ├── Authorization
      ├── Input Validation
      └── Business Logic
      │
      ▼
AWS Resources
```

For example, React cannot securely determine that a User owns a Recipe.

Django must verify ownership before allowing modification or deletion.

---

# 47. Resource Ownership in AWS Deployment

Cognito establishes authenticated identity.

Django maps that identity to an application User and derives resource ownership.

```text
Cognito Token
     │
     ▼
Django
     │
     ▼
Application User
     │
     ├── Recipe.owner
     ├── InventoryItem.user
     ├── SavedRecipe.user
     ├── Review.user
     └── ShoppingList.user
```

The frontend shall not be trusted to determine these ownership relationships.

This matches the authorization model defined in `api-design.md` and `system-design.md`.

---

# 48. Data Location Summary

| Data | Location |
| --- | --- |
| React production build | Amazon S3 |
| Frontend delivery/cache | Amazon CloudFront |
| Django application runtime | Amazon EC2 |
| Docker images | Amazon ECR |
| Relational application data | Amazon RDS PostgreSQL |
| Recipe images | Amazon S3 |
| Profile images | Amazon S3 |
| Authentication identity | Amazon Cognito |
| Sensitive production configuration | AWS Secrets Manager |
| Application/infrastructure logs | Amazon CloudWatch |
| Temporary Guest state | Browser / application runtime |
| Recommendation results | Dynamically calculated; not persistently stored initially |

---

# 49. Initial vs. Future Architecture

## Initial

```text
Frontend
S3 + CloudFront

Backend
1 EC2 instance
Dockerized Django

Docker Images
ECR

Database
RDS PostgreSQL

Authentication
Cognito

Media
S3

Secrets
Secrets Manager

Monitoring
CloudWatch
```

## Future, If Required

```text
Application Load Balancer
        │
        ▼
EC2 Auto Scaling Group
        │
   ┌────┼────┐
   ▼    ▼    ▼
  EC2  EC2  EC2
        │
        ▼
   RDS PostgreSQL
```

Potential future improvements include:

- Multiple Availability Zones.
- RDS Multi-AZ.
- Additional monitoring.
- Caching.
- More advanced deployment automation.
- Additional backend instances.
- More advanced recovery strategies.

These are scalability paths, not requirements for the initial implementation.

---

# 50. Core AWS Architecture Rules

The implementation should follow these rules:

1. React production files are hosted separately from Django.
2. Django runs inside Docker on EC2.
3. Docker images are stored in ECR.
4. PostgreSQL runs in RDS rather than inside the backend container.
5. Persistent media is stored in S3 rather than on EC2.
6. Cognito handles authentication identity.
7. Django handles application authorization and ownership.
8. Application-specific user data remains in PostgreSQL.
9. Production secrets shall not be committed to Git.
10. RDS shall not be publicly exposed.
11. AWS permissions should follow least-privilege principles.
12. Backend containers should remain replaceable.
13. Persistent application state should remain outside individual backend instances.
14. The initial deployment uses one EC2 backend instance.
15. ALB and Auto Scaling are future scalability options rather than initial requirements.
16. Future backend instances may span multiple Availability Zones.
17. Frontend, backend, database, media, and authentication should remain independently manageable.
18. Infrastructure complexity should be introduced only when justified by application requirements.

---

# 51. Final Architecture Summary

The initial production architecture is:

```text
                              Users
                                │
                                ▼
                        Amazon CloudFront
                                │
                                ▼
                         Amazon S3
                       React Frontend
                                │
                                │ HTTPS / REST
                                ▼
                         Amazon EC2
                    ┌─────────────────────┐
                    │   Docker Container  │
                    │                     │
                    │   Django REST API   │
                    └─────────────────────┘
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
             ▼                  ▼                  ▼
        Amazon RDS          Amazon S3         Amazon Cognito
        PostgreSQL            Media           Authentication
             │
             ▼
     Persistent App Data


Deployment:

Git / Developer
      │
      ▼
 Docker Build
      │
      ▼
 Amazon ECR
      │
      ▼
 Amazon EC2


Operations:

Secrets Manager ─────→ Django

Django / EC2 ────────→ CloudWatch
```

The future scalable architecture becomes:

```text
                         Users
                           │
                           ▼
                      CloudFront
                           │
                           ▼
                     React Frontend
                           │
                           ▼
                Application Load Balancer
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
                   EC2    EC2    EC2
                    │      │      │
                    └──────┼──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
             RDS          S3         Cognito
```

The application therefore begins with a simple single-instance backend while preserving the separation of compute, persistent data, media, authentication, and deployment artifacts required for future scaling.

---

# 52. Related Documentation

```text
requirements.md
    ↓
Defines application requirements

database-design.md
    ↓
Defines persistent relational data

api-design.md
    ↓
Defines frontend/backend contracts

system-design.md
    ↓
Defines software architecture and service responsibilities

aws-architecture.md
    ↓
Defines cloud deployment and infrastructure
```