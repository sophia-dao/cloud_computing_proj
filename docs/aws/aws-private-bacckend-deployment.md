# AWS Infrastructure Migration — Public EC2 to Private Backend

**Project:** Recipe Suggestion App  
**Date:** November 5, 2026  
**Status:** Core migration completed and production routing verified

## 1. Overview

The Recipe Suggestion App was initially deployed using a single Amazon EC2 instance in a public subnet to host the Django backend. Although inbound traffic was restricted through security groups and Nginx, the instance still had a public network endpoint and represented a single point of failure.

To improve security, availability, and scalability, we migrated the backend to private subnets across two Availability Zones, introduced an internal Application Load Balancer (ALB), and deployed an Auto Scaling Group.

Amazon CloudFront now uses a VPC origin to connect to the internal ALB without requiring the backend instances to be publicly accessible.

## 2. Previous Architecture

**Request flow:**

User → CloudFront → Public EC2 → Django → RDS PostgreSQL

The React frontend was hosted on Amazon S3 and delivered through CloudFront.

API requests were forwarded by CloudFront to the public EC2 instance, where Nginx served as a reverse proxy for the containerized Django application.

**Limitations:**
- Single EC2 instance created a single point of failure.
- Backend instance had a public network endpoint.
- No automatic horizontal scaling.
- Limited fault tolerance for compute failures.

## 3. Updated Architecture

**Frontend:**

User → CloudFront → S3 (React static files)

**Backend API:**

User → CloudFront → VPC Origin → Internal ALB → Private EC2 Auto Scaling Group → RDS PostgreSQL

**Media:**

User → CloudFront → Private S3 Media Bucket

The backend now runs on two EC2 instances distributed across two Availability Zones.

An internal Application Load Balancer distributes incoming API traffic among healthy backend instances.

The Auto Scaling Group maintains the desired instance count and supports horizontal scaling.

VPC endpoints provide private access to required AWS services without relying on a NAT Gateway.

## 4. CloudFront Routing

The production CloudFront distribution uses the following routing configuration:

| Request path | Target origin |
|---|---|
| `/` and frontend routes | `S3Origin` |
| `/api/*` | `PrivateDjangoAPIOrigin` |
| `/media/*` | `MediaS3Origin` |

The original `DjangoAPIOrigin` remains configured as a rollback option but is no longer the active target for `/api/*`.

## 5. Security Improvements

- Backend EC2 instances are deployed in private subnets.
- An internal ALB replaces the public EC2 origin for API requests.
- The ALB security group restricts inbound HTTP traffic to the CloudFront VPC origin service security group.
- AWS Systems Manager supports instance administration without inbound SSH.
- AWS Secrets Manager stores database credentials.
- RDS PostgreSQL is accessed through private VPC networking.
- CloudFront provides HTTPS access for frontend and API clients.

## 6. Availability and Scalability Improvements

The backend Auto Scaling Group currently maintains two instances across separate Availability Zones.

The internal ALB performs health checks against `/healthz` and routes traffic to healthy targets.

This architecture improves backend compute availability compared with the original single-instance deployment.

However, RDS remains a single-AZ deployment, so the application is not yet fully highly available across all components.

## 7. Deployment Verification

The following checks were completed successfully:

- CloudFront frontend returned HTTP 200.
- Public recipe API requests returned HTTP 200.
- Repeated API requests succeeded.
- Recipe images loaded successfully.
- Private backend targets passed ALB health checks.
- Unauthenticated requests to protected endpoints returned the expected HTTP 403 response.
- CloudFront distribution deployment completed successfully.

These checks establish that the public application is functioning through the new architecture. Authenticated end-to-end testing remains pending.

## 8. CloudFormation Status

The live CloudFront distribution was updated successfully through the AWS CLI.

The local `frontend.yaml` CloudFormation template was updated to represent the private VPC origin and new API routing.

A CloudFormation reconciliation change set named `sync-private-vpc-origin` was created and reviewed. It proposes an in-place modification of `FrontendDistribution` without resource replacement.

**The reconciliation change set has not yet been executed.**

## 9. Remaining Infrastructure Work

- Complete CloudFormation reconciliation and verify stack synchronization.
- Rotate the previously exposed private origin header key.
- Complete final security and load testing.
- Validate the final production release.
- Retire the original public EC2 instance after rollback is no longer required.
- Consider Multi-AZ RDS and further production hardening as future improvements.

## 10. Conclusion

The migration successfully changed the backend architecture from a single public EC2 instance to a private, load-balanced, Auto Scaling deployment spanning two Availability Zones.

The application now uses CloudFront VPC origins to securely connect public API requests to private backend infrastructure.

This represents a significant improvement in network isolation, backend availability, scalability, and overall cloud architecture design.