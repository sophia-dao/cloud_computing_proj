# Recipe Suggestion App — Midpoint Evaluation Report

**Course:** Cloud Computing  
**Evaluation date:** October 16, 2026  
**Final project deadline:** November 13, 2026  
**Repository:** https://github.com/sophia-dao/cloud_computing_proj  
**Group number:** _Add before submission_  
**Group members:** Sophia Dao, Burhan Khokhar, Brooke Sayer, Huy Le

> **Status convention:** <br>
> **- Implemented** code or infrastructure exists <br>
> **- Verified** an observed test or check passed <br>
> **- Planned** not yet implemented. This report documents progress, not a claim that the entire application is deployed. 

## 1. Project overview

The Recipe Suggestion App aims to reduce household food waste by helping users find recipes based on ingredients they already have. Instead of searching for recipes first and then purchasing every required ingredient, users can provide their available ingredients and receive suitable suggestions. The system is designed to support food preferences, allergies, and cuisine choices.

The planned user roles are **Guest**, **Registered User**, and **Administrator**. Guests can select ingredients and explore recommendations without a permanent account. Registered users are intended to manage saved inventory, recipes, shopping lists, and profile preferences. Administrators will have additional management capabilities. Two planned recommendation modes are **AVAILABLE_ONLY** (recipes that can be made with available ingredients) and **PARTIAL_MATCH** (recipes that require some additional ingredients).

## 2. Architecture and changes from the original plan

### 2.1 Original system design

The original plan, which was documented in [`README.md`](README.md) and [`system-design.md`](docs/system-design.md), describe a **client-server application with a modular-monolith Django backend**, not a microservices architecture. The core design separates React presentation, Django business logic and authorization, Cognito identity, relational data, and media storage. The intended production technologies were:
- **React hosted on S3/CloudFront**
- **Django REST Framework in Docker on AWS**
- **PostgreSQL on Amazon RDS**
- **Amazon Cognito**
- **Amazon S3 for media**.

```mermaid
flowchart TD
    U[User / Browser] --> F[React frontend<br/>S3 + CloudFront - planned]
    F -->|HTTPS / REST / JSON| API[Django REST Framework<br/>Docker on AWS - planned]
    API --> DB[(PostgreSQL<br/>Amazon RDS - planned)]
    API --> S3[(Amazon S3<br/>Media - planned)]
    F <-->|Sign-in / tokens| C[Amazon Cognito - planned]
    API -.->|Validate identity| C
    subgraph Backend domains
      API --> D[Users / Ingredients / Recipes / Inventory<br/>Recommendations / Reviews / Shopping]
    end
```

*Figure 1. Original target application architecture. This is a design diagram, **not** a diagram of services already running in AWS.*

### 2.2 Architecture changes and design decisions

The team has **retained the original modular-monolith application architecture**. The significant changes concern the hosting choice, infrastructure provisioning, and order of integration.

| Area | Original design | Midpoint decision / actual status | Reason and trade-off |
| --- | --- | --- | --- |
| Backend compute | Dockerized backend on AWS; exact hosting method not fixed in original documents | **Amazon EC2** selected and provisioned; Docker installed | Direct control and transparent deployment steps; team must manage the host and availability |
| Infrastructure | AWS hosting and infrastructure envisioned | **CloudFormation** templates used for VPC/networking, ECR, EC2, and OIDC | Repeatable and reviewable infrastructure-as-code |
| Image distribution | Docker-based deployment planned | **Amazon ECR** repository deployed; backend image pushed | Versioned container artifacts, separate from runtime |
| Application server | Django backend specified | **Gunicorn** configured in the Docker image | More appropriate serving process than Django development server |
| Database | PostgreSQL on **Amazon RDS** | **SQLite for local prototype testing**; RDS not provisioned | Allows early API testing; not the intended persistent production database |
| Frontend hosting | **Amazon S3 + CloudFront** | React foundation developed locally; hosting not yet verified | Prioritized UI implementation before cloud integration |
| Authentication | **Amazon Cognito** identity + Django authorization | User/profile foundation tested; Cognito integration not yet verified | Authentication remains a separate integration dependency |
| CI/CD | Potential GitHub Actions integration | GitHub OIDC provider created; deployment workflow paused | Establishes a credential-free authentication foundation, but **no automated deployment yet** |

The project scope remains the same. These are **implementation refinements and a staged rollout**, not a redesign of the recipe recommendation model.


#### Rationale behind the major decisions

**1. Why EC2 rather than App Runner or ECS?** The original proposal specified a Dockerized AWS backend without committing to a particular compute service. During planning, the team considered managed container hosting, including AWS App Runner and Amazon ECS, but selected a single EC2 instance for the initial deployment. EC2 makes the underlying compute, operating system, Docker installation, networking, and IAM permissions visible and configurable. This supports the course objective of explaining how cloud components interact and lets the team provision a concrete, inspectable prototype. 
>**Trade-off:** EC2 requires the team to maintain the host, manage application rollouts, and implement health monitoring and scaling separately; managed container services could reduce that operational burden. EC2 is an initial deployment choice, not evidence of high availability.

**2. Why CloudFormation instead of manually creating AWS resources?** The team chose Infrastructure as Code to describe the network, container registry, compute instance, and identity configuration in version-controlled templates. CloudFormation helps make the infrastructure reproducible, documents resource dependencies and permissions, and reduces the risk of inconsistent manual configuration between deployments. The network, ECR, and backend resources were separated into stacks so they can be updated independently. 
>**Trade-off:** Writing and troubleshooting templates adds initial work. In practice, the EC2 instance-type/Availability Zone mismatch required a network adjustment and redeployment, illustrating both the learning curve and the benefit of having the configuration recorded.

**3. Why Docker, ECR, and Gunicorn?** Docker packages Django with its runtime dependencies into an image that can be built locally and transferred to AWS. Amazon ECR stores that image separately from the EC2 instance, which supports consistent image distribution and future versioned deployments. Gunicorn was configured to serve Django inside the container instead of relying on Django's development server. 
>**Trade-off:** Containerization does not automatically handle environment variables, database migrations, secrets, process restarts, or health checks. The local HTTP 500 error before migrations demonstrated that deployment requires more than a successful image build.

**4. Why defer RDS and use SQLite temporarily?** PostgreSQL on Amazon RDS remains the intended persistent database architecture. For the midpoint, the team prioritized proving the Django API, Docker packaging, and AWS infrastructure before introducing managed database networking, configuration, and cost. SQLite was sufficient for local model migrations and API smoke tests. 
>**Trade-off:** A SQLite database inside a disposable container is not an acceptable long-term persistence strategy: data can be lost when containers are replaced, and it is unsuitable for the planned horizontally scalable backend. RDS is deferred, not removed from the design.

**5. Why separate application-specific users from Cognito authentication?** The original design assigns identity and sign-in to Amazon Cognito while Django manages user profiles, preferences, resource ownership, and permissions. This keeps authentication credentials outside the application database and preserves a clear authorization boundary. The team implemented parts of the user/profile foundation before completing Cognito integration so those domain models and APIs could be tested independently. 
>**Trade-off:** Authentication-to-user mapping and protected endpoint behavior remain integration risks and must be verified before the final release.

**6. Why use Systems Manager and GitHub OIDC?** The EC2 instance is managed through AWS Systems Manager rather than opening an inbound SSH port, reducing the administrative network exposure of the prototype. The GitHub OIDC provider prepares for short-lived, federated AWS credentials in CI/CD instead of storing permanent AWS keys in repository secrets. 
>**Trade-off:** These controls require careful IAM configuration and do not themselves constitute an operational deployment pipeline. At midpoint, SSM interactive access was verified and the OIDC provider was created, but the GitHub Actions build/deploy workflow is not implemented.

**7. Why stage the work rather than integrate every cloud service immediately?** With the midpoint evaluation approaching, the team focused on independently demonstrable milestones: functioning backend APIs, a React foundation, local Docker execution, and provisioned AWS infrastructure. This makes progress easier to test and explain while preserving the original long-term architecture. 
>**Trade-off:** The project still needs end-to-end integration, a persistent database, authentication, frontend hosting, and operational deployment before the final evaluation. The remaining integration work is a schedule risk, not a completed milestone.


### 2.3 Current midpoint architecture — provisioned versus running

```mermaid
flowchart TB
    subgraph LOCAL[Local development and testing]
      REACT[React frontend<br/>local development]
      DJ[Django REST API<br/>Docker / Gunicorn<br/>local API tested]
      SQL[(SQLite<br/>local test data)]
      REACT -.->|API integration in progress| DJ
      DJ --> SQL
    end
    DJ -->|Build and push image - verified| ECR
    subgraph AWS[AWS us-east-1 - provisioned infrastructure]
      ECR[(Amazon ECR<br/>recipe-app-backend)]
      OIDC[GitHub OIDC provider<br/>created]
      CF[CloudFormation<br/>network / ECR / backend]
      SSM[AWS Systems Manager<br/>session verified]
      subgraph VPC[VPC 10.0.0.0/16]
        IGW[Internet Gateway<br/>public route table]
        subgraph AZE[Public subnet 10.0.1.0/24]
          EMPTY[No backend instance]
        end
        subgraph AZA[Public subnet 10.0.2.0/24]
          EC2[EC2 t3.micro<br/>Docker installed<br/>No inbound SG rules]
        end
        IGW --- AZE
        IGW --- AZA
      end
      SSM -->|managed instance| EC2
      CF -.->|provisions| VPC
    end
    ECR -.->|Automated pull and rollout NOT implemented| EC2
    OIDC -.->|GitHub Actions workflow NOT implemented| ECR
```

*Figure 2. Verified midpoint infrastructure and local prototype. Dashed links indicate incomplete integration or provisioning relationships rather than confirmed application traffic. The EC2 host is provisioned, but Django running on EC2 and a public API endpoint have **not** been verified.*

### 2.4 Application architecture retained from the original design

The backend continues to use **domain-oriented Django modules**. The original design defines a shared canonical `Ingredient`, reusable `Tag` classifications, and separate `Allergen` entities. Both Guest and Registered User recommendation flows are designed to use the same backend `RecommendationService` with `AVAILABLE_ONLY` and `PARTIAL_MATCH` modes.

```mermaid
flowchart LR
    G[Guest selected ingredients<br/>temporary React state] --> IN[Canonical Ingredient IDs]
    R[Registered user's saved inventory<br/>planned persistent data] --> IN
    IN --> RS[RecommendationService<br/>backend - planned integration]
    FILTER[Tags / Allergens / Match mode] --> RS
    RS --> REC[Recipe results<br/>match score + missing ingredients]
    REC --> SHOP[Shopping list generation<br/>planned]
```

*Figure 3. Intended recommendation data flow from the original system design. The Ingredient API foundation has been implemented; this diagram does **not** claim that the full recommendation service is complete.*

### 2.5 Planned automated deployment workflow (not yet operational)

```mermaid
flowchart LR
    GH[GitHub main branch] --> TEST[GitHub Actions<br/>Django tests]
    TEST --> BUILD[Docker build<br/>linux/amd64]
    BUILD --> REG[Amazon ECR<br/>image by commit SHA]
    REG --> CMD[SSM Run Command]
    CMD --> EC2[EC2 Docker<br/>pull / restart / health check]
```

*Figure 4. Proposed CI/CD pipeline. The GitHub OIDC provider exists, but the GitHub Actions workflow and automated EC2 rollout are **not implemented** as of the midpoint.*

## 3. Implementation progress

### 3.1 Application code

| Component | Current progress | Evidence / limitation |
| --- | --- | --- |
| Django REST backend foundation | Implemented | Local Django server and tests have been run |
| Canonical Ingredient API | Implemented and verified | Case-insensitive search, detail lookup, validation of unsupported methods, and automated tests |
| User/profile backend | Partially implemented and tested | Recent checks passed; Cognito authentication not yet verified |
| React application foundation | Implemented | Routing, reusable components, theme, and a custom 404 page have been worked on |
| Recipes, inventory, recommendations, saved recipes | Defined in GitHub issues and system design | Do not claim completion without confirming merged implementations |
| Full frontend-to-backend integration | In progress | Requires a verified end-to-end walkthrough |

The **canonical Ingredient** design is a shared foundation: inventory, recipes, and recommendations are intended to reference the same ingredient records rather than create inconsistent duplicate names.

### 3.2 AWS infrastructure and deployment preparation

| Resource / practice | Current status | Verification performed |
| --- | --- | --- |
| VPC, Internet Gateway, route table, two public subnets | Deployed | CloudFormation network stack deployed and updated |
| EC2 backend instance (`t3.micro`) | Deployed | Backend stack completed successfully |
| Docker on EC2 | Verified | Docker version and service status checked via SSM |
| AWS Systems Manager | Verified | Interactive session to EC2 established without inbound SSH |
| Amazon ECR | Deployed | `recipe-app-backend:midpoint-v1` image pushed |
| Dockerized Django | Verified locally | API returned HTTP 200 after applying migrations in test container |
| GitHub OIDC identity provider | Created and verified | Provider ARN returned by IAM CLI |
| GitHub deployment role | Template prepared; deployment verification pending | Confirm stack status and role ARN before marking verified |
| GitHub Actions deployment workflow | Not implemented | Work intentionally paused for midpoint documentation |
| Amazon RDS | Not implemented | SQLite currently used in local prototype |
| AWS-hosted React frontend | Not verified | S3/CloudFront hosting remains planned |

**Infrastructure specifics:** AWS region `us-east-1`; VPC CIDR `10.0.0.0/16`; public subnets `10.0.1.0/24` and `10.0.2.0/24`. The backend EC2 security group has no inbound rules at the midpoint, so public access to Django is not yet available. The EC2 instance uses an IAM role for SSM and scoped ECR image retrieval.

## 4. Testing and evidence

Completed checks reported during development include:

1. **Ingredient API:** Case-insensitive ingredient search succeeded. Requests for nonexistent ingredient IDs returned HTTP 404, and unsupported POST requests returned HTTP 405, as intended.
2. **Automated Django tests:** Ingredient tests and recent user/profile checks passed locally. Record the latest test count and command output before the presentation rather than relying on an older count.
3. **Docker smoke test:** A Django Docker container responded with HTTP 200 for `GET /api/ingredients/` after database migrations were applied. This also exposed an important startup dependency: a new SQLite database must be migrated before the API can serve database-backed requests.
4. **AWS provisioning:** Network, ECR, and backend EC2 CloudFormation stacks completed. Docker and Systems Manager were checked on the instance.
5. **Container registry:** A backend image was built for `linux/amd64` and pushed to Amazon ECR.
6. **OIDC identity:** AWS IAM returned the GitHub OIDC provider, establishing that the identity provider was created. This does **not** prove an end-to-end GitHub Actions deployment.

**Evidence to attach before submission:** screenshots or terminal excerpts showing the Django test summary, successful Ingredient API response, frontend UI, Docker test, CloudFormation stack status, ECR image tag, EC2 instance, and SSM connection. Remove tokens, secret values, and unnecessary personal/account information from screenshots.

## 5. Challenges and lessons learned

**Availability Zone and EC2 instance compatibility.** The first EC2 provisioning attempt failed because the selected instance type was unavailable in the initial subnet's Availability Zone. The team added a second public subnet in another Availability Zone and deployed the backend instance there. This highlighted the importance of validating region/AZ capacity and designing flexible network infrastructure.

**Database initialization in containers.** A locally built Docker container initially produced server errors because its SQLite database schema had not been migrated. Applying Django migrations resolved the API issue. This demonstrated that container startup and database lifecycle must be handled explicitly during deployment.

**Infrastructure versus application deployment.** Provisioning an EC2 instance, installing Docker, and pushing an image to ECR are separate from running a healthy application service. The team is documenting these stages individually so progress can be verified without overstating readiness.

**Scope management.** The team prioritized the foundational API, frontend structure, repeatable infrastructure, and container packaging before completing Cognito, RDS, and CI/CD. This supports a feasible midpoint prototype but leaves integration work for the final phase.

## 6. Security and scalability

### Security practices already present

- AWS IAM roles are used for the backend instance and GitHub OIDC deployment preparation, rather than embedding long-lived credentials in source code.
- Systems Manager provides administrative access to EC2 without opening inbound SSH.
- The backend EC2 security group currently has no inbound rules.
- The backend ECR repository uses immutable image tags and image scanning on push.
- The EC2 root EBS volume is encrypted, and IMDSv2 is required.
- Sensitive runtime settings are intended to come from environment configuration rather than hard-coded production secrets.

### Current limits and planned improvements

The current architecture has **one EC2 instance**, so it is not highly available and does not automatically scale application compute. Two public subnets exist, but multiple subnets alone do not provide failover. Before final delivery, the team should evaluate an Application Load Balancer, EC2 Auto Scaling across Availability Zones, managed relational storage (RDS), HTTPS, health checks, and basic monitoring. These are **proposed improvements**, not midpoint achievements.

To address the course's scalability requirement, the final evaluation should include measurable results, such as requests per second, response-time percentiles, error rates, and resource usage under a repeatable test workload. No benchmark results are claimed at midpoint.

## 7. Remaining work and risks

| Remaining task | Main risk | Proposed next action |
| --- | --- | --- |
| Integrate frontend and Django APIs | Inconsistent API contracts or unfinished UI flows | Verify one complete user journey and fix integration issues |
| Complete recipes, inventory, and recommendation flows | Shared data/model dependencies | Prioritize an end-to-end available-ingredients recommendation |
| Integrate and verify Cognito authentication | Authorization and profile mapping complexity | Test login, protected endpoints, and role behavior |
| Run Django container on EC2 | Runtime configuration, migrations, service health | Deploy an image, apply migrations, and run a local-on-instance health check |
| Implement persistent cloud storage | SQLite data loss or deployment coupling | Add and test an appropriate persistent database strategy |
| Deploy React frontend | Hosting, routing, CORS, and HTTPS | Configure hosting and test API connectivity |
| Complete GitHub Actions CI/CD | IAM permissions, safe secret handling, failed rollouts | Finish OIDC verification and implement tested build/push/deploy stages |
| Measure scalability and security | Insufficient evidence for professor's criteria | Run load tests and document protections and limitations |
| Record final demo and update documentation | Schedule and integration delays | Freeze demo scope and verify a repeatable demonstration |

## 8. Plan through final submission

**Midpoint — October 16:** Present the locally working prototype, tested APIs, Docker image, and deployed AWS foundation. Show actual logs and screenshots, with pending integrations clearly labeled.

**Next phase:** Complete a minimum end-to-end recipe recommendation journey; verify authentication and user data flows; run Django on EC2; connect frontend and backend; introduce persistent data storage.

**Finalization — by November 13:** Implement or finalize deployment automation, strengthen security and monitoring, collect scalability measurements, run regression tests, update diagrams and documentation, and record the final demonstration.

## 9. Midpoint conclusion

The project has progressed from an initial application proposal to a structured Django/React codebase, a tested Ingredient API, local Docker execution, and provisioned AWS networking, compute, registry, and management resources. The architecture was refined during implementation to favor EC2-hosted Docker and CloudFormation-managed infrastructure. These changes helped the team establish a concrete deployment foundation and identify practical integration challenges.

The main remaining objective is to connect the existing pieces into a working cloud-hosted application, while finishing user-facing recipe workflows, authentication, persistence, automation, and measurable scalability testing. The midpoint demonstrates **partial functionality and infrastructure progress**, not a finished production system.

---

### Final review checklist (remove before submission)

- [ ] Add group number and member names.
- [ ] Confirm the GitHub OIDC CloudFormation stack and IAM role status.
- [ ] Verify which teammate features have actually been merged into `main`.
- [ ] Update exact test count and capture fresh test output.
- [ ] Attach screenshots and an accurate AWS architecture diagram.
- [ ] Confirm the demo reflects the same implementation state as the report.
