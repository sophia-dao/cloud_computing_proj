# AWS Architecture — Recipe Suggestion App

## 1. Overview

The Recipe Suggestion App is deployed on Amazon Web Services (AWS) using a multi-tier cloud architecture. The infrastructure separates frontend delivery, backend computing, database storage, authentication, and application media.

The application uses Amazon CloudFront as its public entry point, while backend EC2 instances and the PostgreSQL database operate within private subnets.

Infrastructure resources are provisioned and managed using AWS CloudFormation.

## 2. AWS Services

| AWS Service | Purpose |
|---|---|
| Amazon CloudFront | Public HTTPS entry point for frontend and API requests |
| Amazon S3 | Private frontend assets and recipe image storage |
| Amazon EC2 | Runs the Dockerized Django backend |
| EC2 Auto Scaling | Manages backend instances across Availability Zones |
| Application Load Balancer | Distributes API requests across backend instances |
| Amazon ECR | Stores backend Docker images |
| Amazon RDS | Hosts the PostgreSQL production database |
| Amazon Cognito | Provides user authentication and Google Sign-In |
| Amazon VPC | Provides isolated networking and private subnets |
| VPC Endpoints | Provides private access to supported AWS services |
| AWS Secrets Manager | Stores sensitive application configuration |
| AWS Systems Manager | Provides EC2 management through Session Manager |
| Amazon CloudWatch | Provides infrastructure metrics and logging capabilities |
| AWS CloudFormation | Defines and deploys infrastructure resources |

## 3. High-Level Architecture

The production architecture uses CloudFront to route frontend and API requests to separate origins.

```text
                         Users
                           |
                           | HTTPS
                           v
                    Amazon CloudFront
                      /          \
                     /            \
           Frontend Requests     /api/*
                   |               |
                   v               v
              Private S3       VPC Origin
              Frontend             |
                                   v
                           Internal ALB
                                   |
                                   v
                           EC2 Auto Scaling
                            /           \
                           v             v
                      EC2 (AZ-A)     EC2 (AZ-B)
                           \             /
                            \           /
                             v         v
                         Django REST API
                           /         \
                          v           v
                     RDS PostgreSQL  S3 Media
```

Amazon Cognito independently authenticates users through its managed login service. The frontend obtains authentication tokens and includes them in protected API requests.

## 4. Frontend Hosting

The frontend is developed using React and Vite.

The production build is stored in a private Amazon S3 bucket and delivered through CloudFront.

CloudFront Origin Access Control (OAC) restricts direct access to the frontend bucket.

The frontend does not use public S3 static website hosting.

CloudFront also handles single-page application routing by returning `index.html` for supported frontend navigation paths.

## 5. Backend Hosting and Load Balancing

The Django REST Framework backend runs inside Docker containers on Amazon EC2.

The final deployment uses an EC2 Auto Scaling Group with the following configuration:

| Setting | Value |
|---|---|
| Instance type | `t3.micro` |
| Minimum capacity | 2 |
| Desired capacity | 2 |
| Maximum capacity | 3 |
| Deployment | Two private application subnets |
| Availability Zones | `us-east-1a`, `us-east-1b` |
| Container runtime | Docker with Gunicorn |

The Auto Scaling Group uses an EC2 Launch Template to configure new backend instances.

An internal Application Load Balancer distributes requests to healthy instances.

The target group forwards HTTP requests to port 80 and uses `/healthz` for health checks.

The final deployment was verified with two healthy EC2 instances registered in the target group.

## 6. CloudFront API Routing

CloudFront acts as the application's public entry point for both static frontend content and backend API requests.

| Request | Destination |
|---|---|
| Frontend pages and assets | Private S3 frontend bucket |
| `/api/*` | Internal Application Load Balancer through CloudFront VPC origin |

The VPC origin allows CloudFront to reach the internal ALB without exposing the backend instances directly to the public internet.

This design provides a unified HTTPS entry point for the application.

## 7. VPC and Networking

The application operates within a VPC using the CIDR range `10.0.0.0/16`.

### Subnet Configuration

| Subnet | CIDR | Availability Zone | Purpose |
|---|---|---|---|
| Public subnet | `10.0.2.0/24` | `us-east-1a` | NAT Gateway |
| Private application A | `10.0.5.0/24` | `us-east-1a` | Backend EC2 and internal ALB |
| Private application B | `10.0.6.0/24` | `us-east-1b` | Backend EC2 and internal ALB |

The Internet Gateway is attached to the VPC.

A NAT Gateway is deployed in the public subnet to provide outbound internet access for private resources when required.

The private application route tables contain a local VPC route and a default route to the NAT Gateway.

Backend instances do not have public IP addresses.

## 8. VPC Endpoints

VPC endpoints allow private backend instances to access supported AWS services without routing that traffic through the public internet.

The deployed endpoints include:

| Endpoint | Type |
|---|---|
| Amazon S3 | Gateway |
| Amazon ECR API | Interface |
| Amazon ECR Docker | Interface |
| AWS Systems Manager | Interface |
| SSM Messages | Interface |
| EC2 Messages | Interface |
| AWS Secrets Manager | Interface |
| Amazon CloudWatch Logs | Interface |

The backend instances retrieve container images from ECR using the ECR interface endpoints, with S3 access available through the gateway endpoint.

The S3 gateway endpoint also supports access to the private recipe media bucket.

Security groups restrict access to the interface endpoints.

## 9. Database Architecture

The production database uses Amazon RDS for PostgreSQL.

The database stores persistent application information, including users, ingredients, recipes, inventory, preferences, allergies, and saved recipes.

| Setting | Configuration |
|---|---|
| Database engine | PostgreSQL |
| AWS service | Amazon RDS |
| Instance class | `db.t3.micro` |
| Public accessibility | Disabled |
| Access | Restricted through security groups |

Django connects to RDS using database credentials supplied through the deployment configuration.

The backend Docker containers do not store persistent relational data.

Multi-AZ RDS deployment was not enabled in the final configuration.

## 10. Media Storage

Application media is stored in a separate private Amazon S3 bucket.

The backend uses `django-storages` to integrate Django with S3.

Recipe images are stored independently of EC2 instances, allowing containers to be replaced without losing uploaded media.

The initial production database contains 100 recipes imported from TheMealDB, with associated images.

## 11. Authentication

Amazon Cognito User Pools manages registered-user authentication.

The application supports Google Sign-In through a configured Cognito identity provider.

The frontend uses the OAuth 2.0 Authorization Code flow with PKCE.

After authentication, React sends the Cognito access token to protected Django API endpoints.

Django validates the token and maps the Cognito identity to a local application user.

Cognito manages authentication, while Django remains responsible for application permissions, resource ownership, and authorization.

## 12. Security and Access Control

The architecture applies security controls across multiple layers.

- **CloudFront:** Provides the public HTTPS entry point.
- **Private EC2 instances:** Prevent direct public access to backend servers.
- **Internal ALB:** Accepts backend traffic through the configured VPC origin and security rules.
- **Private RDS:** Restricts database access to authorized backend resources.
- **Security groups:** Control communication between application components.
- **IAM roles:** Provide EC2 instances with required AWS service permissions.
- **Secrets Manager:** Stores sensitive credentials and configuration.
- **Cognito:** Authenticates registered users.
- **Django:** Enforces application-level permissions and resource ownership.

AWS Systems Manager Session Manager is used to access and manage EC2 instances without requiring public SSH access.

## 13. Deployment and Infrastructure Management

AWS CloudFormation manages the infrastructure through separate stacks covering:

- Networking and routing.
- VPC endpoints.
- Backend Auto Scaling and load balancing.
- Frontend S3 and CloudFront.
- RDS database.
- S3 media storage.
- Cognito authentication.

Backend Docker images are built and pushed to Amazon ECR.

EC2 instances retrieve the required image and run the Django application through Docker and Gunicorn.

The final backend image was deployed using the `final-v1` tag.

Infrastructure changes are managed through CloudFormation templates rather than relying exclusively on manual AWS Console configuration.

## 14. Monitoring and Performance Testing

Amazon CloudWatch was used to inspect EC2 and RDS resource utilization.

The final deployment was also tested using ApacheBench.

Tests included recipe listing and recipe detail API requests, using 1,000 requests at concurrency levels of 10, 50, and 100.

During the recorded monitoring period:

| Resource | Observed CPU utilization |
|---|---|
| Amazon RDS | Approximately 4.0% average, 5.7% maximum |
| EC2 instances | Approximately 0.48–0.61% average |

These measurements describe the observed test period rather than guaranteed performance under all workloads.

## 15. Architecture Decisions

### Private Backend Instead of Public EC2

The project initially used a publicly accessible backend instance.

The final deployment moved backend instances into private subnets and introduced an internal ALB accessible through CloudFront VPC origin.

This reduced direct public exposure of the backend infrastructure.

### Auto Scaling Instead of a Single Instance

The initial architecture used a single EC2 instance.

The final architecture uses an Auto Scaling Group across two Availability Zones, improving backend redundancy and supporting instance replacement.

### Managed Database Instead of Local PostgreSQL

Amazon RDS separates persistent relational data from backend compute, allowing EC2 instances to be replaced without losing database contents.

### Cognito Instead of Application-Managed Authentication

Amazon Cognito handles user authentication and Google federation, while Django retains application-specific authorization.

## 16. Challenges Encountered

### Systems Manager Connectivity After VPC Endpoint Deployment

During the deployment of VPC endpoints, the existing EC2 instance lost connectivity to AWS Systems Manager.

Private DNS redirected Systems Manager traffic to the new interface endpoints, but the endpoint security group initially permitted HTTPS connections only from the private application subnets.

The existing instance was still located in the public subnet.

**Solution:** The endpoint security group was updated to allow HTTPS traffic from the public subnet, restoring Session Manager connectivity. The corresponding CloudFormation configuration was also updated.

The legacy public EC2 instance was subsequently removed as part of the transition to the private backend architecture.

## 17. Future Improvements

Potential future enhancements include:

- Multi-AZ RDS for improved database availability.
- A second NAT Gateway to reduce single-AZ networking dependency.
- AWS WAF for additional application-layer protection.
- Expanded CloudWatch alarms and application monitoring.
- Automated CI/CD pipelines.
- Additional performance optimization and caching.

These are future improvements and are not presented as completed components of the final deployment.

## 18. Related Documentation

- [Requirements](requirements.md)
- [System Design](system-design.md)
- [Database Design](database-design.md)
- [API Design](api-design.md)
- [Main README](../README.md)