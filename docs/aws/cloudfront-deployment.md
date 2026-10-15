# AWS CloudFront Deployment and Troubleshooting

**Project:** Recipe Suggestion App  
**Environment:** AWS — us-east-1  
**Deployment method:** AWS CloudFormation  
**Status:** Deployed and verified  
**Last updated:** October 14, 2026

## 1. Overview

The Recipe Suggestion App uses Amazon CloudFront as the public entry point for both the React frontend and Django REST API.

The frontend is stored in a private Amazon S3 bucket, while the Django backend runs inside a Docker container on an Amazon EC2 instance.

CloudFront serves the React application over HTTPS and forwards requests matching `/api/*` to the backend through an Nginx reverse proxy.

This configuration provides a single public domain for the application and eliminates the need for the frontend to call a separate backend domain.

### Deployed resources

| Resource | Configuration |
|---|---|
| AWS Region | us-east-1 |
| CloudFormation frontend stack | `recipe-app-frontend` |
| CloudFront distribution | `E2YMECNRA0V5YR` |
| CloudFront URL | `https://d1q0iv2raorz8j.cloudfront.net` |
| S3 frontend bucket | `recipe-app-frontend-frontendbucket-yhbrd6afosjk` |
| Backend EC2 instance | `i-0f80e33afb9d7dd0a` |
| Backend Elastic IP | `3.214.51.24` |
| Backend origin DNS | `ec2-3-214-51-24.compute-1.amazonaws.com` |
| Backend application | Django REST Framework |
| Backend container | Docker |
| Reverse proxy | Nginx |
| Infrastructure template | `infrastructure/cloudformation/frontend.yaml` |

## 2. Deployment Architecture

The request flow is:

```text
                    Internet
                       |
                       v
               Amazon CloudFront
                 HTTPS endpoint
                       |
              +--------+---------+
              |                  |
              v                  v
       Default behavior      /api/* behavior
              |                  |
              v                  v
         Amazon S3          EC2 public origin
       Private bucket       HTTP port 80
              |                  |
              v                  v
        React frontend         Nginx
                                 |
                                 v
                           127.0.0.1:8000
                                 |
                                 v
                           Docker container
                                 |
                                 v
                           Django REST API
                                 |
                                 v
                         SQLite database
```

CloudFront selects the origin based on the request path.

- Requests for `/`, JavaScript, CSS, and other frontend assets are sent to S3.
- Requests matching `/api/*` are sent to the EC2 backend.
- CloudFront accepts HTTPS requests from users.
- The CloudFront-to-EC2 connection currently uses HTTP and requires further security improvements.

## 3. Initial Frontend Hosting Configuration

Before adding backend routing, the frontend was already deployed using Amazon S3 and CloudFront.

### 3.1 Private S3 bucket

The S3 bucket stores the production build of the React application.

Public access is blocked, and the bucket uses server-side encryption with Amazon S3-managed keys (SSE-S3).

### 3.2 CloudFront Origin Access Control

CloudFront uses Origin Access Control (OAC) to access the private S3 bucket.

The bucket policy grants read access to the CloudFront service principal, restricted to the specific distribution ARN.

This allows users to access frontend files through CloudFront without exposing the S3 bucket publicly.

### 3.3 Single-page application routing

The initial distribution used custom error responses to serve `/index.html` when S3 returned HTTP 403 or 404.

This supports client-side React routes such as `/profile` or `/dashboard`.

However, these error responses are configured at the distribution level and can also affect backend API responses.

This limitation remains unresolved and is documented in Section 9.

## 4. Adding Django API Routing to CloudFront

To connect the frontend and backend under one domain, we updated the existing CloudFront distribution through CloudFormation.

### 4.1 New backend origin

A second origin was added to the distribution.

```yaml
- Id: DjangoAPIOrigin
  DomainName: ec2-3-214-51-24.compute-1.amazonaws.com
  CustomOriginConfig:
    HTTPPort: 80
    OriginProtocolPolicy: http-only
    OriginReadTimeout: 30
```

The backend uses an EC2 Elastic IP to maintain a stable public address.

The origin DNS name points to that Elastic IP.

### 4.2 API cache behavior

A new cache behavior was created for `/api/*`.

```yaml
CacheBehaviors:
  - PathPattern: /api/*
    TargetOriginId: DjangoAPIOrigin
    ViewerProtocolPolicy: redirect-to-https
    AllowedMethods:
      - GET
      - HEAD
      - OPTIONS
      - PUT
      - PATCH
      - POST
      - DELETE
    CachedMethods:
      - GET
      - HEAD
    Compress: true
    CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
    OriginRequestPolicyId: b689b0a8-53d0-40ab-baf2-68738e2966ac
```

The selected AWS-managed policies are:

| Policy | Purpose |
|---|---|
| `Managed-CachingDisabled` | Prevents CloudFront from caching API responses |
| `Managed-AllViewerExceptHostHeader` | Forwards viewer request information while using the origin hostname as the Host header |

Disabling caching simplifies API behavior during development and avoids serving stale or user-specific responses from CloudFront's cache.

### 4.3 Private origin header

A custom header was configured between CloudFront and Nginx.

```yaml
Parameters:
  BackendOriginKey:
    Type: String
    NoEcho: true
    MinLength: 32
    Description: Private header value shared by CloudFront and Nginx
```

CloudFront includes the header in origin requests:

```yaml
OriginCustomHeaders:
  - HeaderName: X-Recipe-Origin-Key
    HeaderValue: !Ref BackendOriginKey
```

Nginx checks the header before forwarding API requests.

The actual token is not stored in the Git repository or included in this documentation.

**Security limitation:** The origin currently uses HTTP, so this header is transmitted without transport encryption between CloudFront and EC2. It is an additional access check, not a substitute for HTTPS or application authentication.

## 5. EC2 and Nginx Configuration

### 5.1 Security group restrictions

The EC2 backend security group was updated to allow inbound TCP port 80 only from the AWS-managed CloudFront origin-facing prefix list.

Prefix list:

`pl-3b927c52`

This reduces exposure compared with opening HTTP access to all IPv4 addresses.

However, the prefix list is shared by CloudFront distributions and does not uniquely identify our distribution.

The custom origin header provides an additional access restriction.

### 5.2 Nginx reverse proxy

Nginx was installed on the EC2 instance and configured to forward API requests to Django.

The relevant configuration is:

```nginx
server {
    listen 80 default_server;
    server_name _;

    location /api/ {
        if ($http_x_recipe_origin_key != "PRIVATE_SECRET_TOKEN") {
            return 403;
        }

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        return 404;
    }
}
```

The placeholder represents the existing private token and must not be used as an actual production value.

Nginx was validated using:

```bash
sudo nginx -t
sudo systemctl enable --now nginx
```

### 5.3 Docker networking

Django is exposed only on the EC2 loopback interface:

```text
127.0.0.1:8000:8000
```

This prevents direct public access to the container's application port.

External API traffic must pass through Nginx.

## 6. CloudFormation Deployment Procedure

The CloudFront changes were managed using the existing frontend CloudFormation stack.

### 6.1 Validate the template

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/frontend.yaml \
  --region us-east-1 \
  --profile recipe-app
```

### 6.2 Create a change set

A private temporary JSON parameter file was used to supply the backend origin token.

```bash
aws cloudformation create-change-set \
  --stack-name recipe-app-frontend \
  --change-set-name add-django-api-origin-v2 \
  --change-set-type UPDATE \
  --template-body file://infrastructure/cloudformation/frontend.yaml \
  --parameters file:///tmp/recipe-app-frontend-params.json \
  --region us-east-1 \
  --profile recipe-app
```

The parameter file was stored outside the repository and removed after successful change set creation.

### 6.3 Inspect infrastructure changes

Before execution, the proposed changes were inspected.

The change set showed:

| Resource | Action | Replacement |
|---|---|---|
| `FrontendDistribution` | Modify | False |

This confirmed that the existing CloudFront distribution would be modified rather than replaced.

No replacement of the S3 frontend bucket was proposed.

### 6.4 Execute the change set

```bash
aws cloudformation execute-change-set \
  --stack-name recipe-app-frontend \
  --change-set-name add-django-api-origin-v2 \
  --region us-east-1 \
  --profile recipe-app
```

The corrected update was subsequently verified through a successful API request.

## 7. Deployment Errors and Troubleshooting

Several issues occurred during the deployment process. These were useful for understanding CloudFormation rollback behavior, AWS-managed CloudFront policies, and Django host validation.

### 7.1 Error: Invalid CloudFront cache policy

**Error message:**

```text
Invalid request provided:
The specified cache policy does not exist.
(Service: CloudFront, Status Code: 404)
```

**Cause:**

The initial CloudFormation template contained an incorrect AWS-managed cache policy ID:

```text
413f1600-6a40-4f8f-9b13-86fa04c8f3e0
```

CloudFormation template validation did not catch the invalid ID because template validation does not guarantee that referenced external service resources exist.

The error occurred when CloudFormation attempted to update the CloudFront distribution.

**Resolution:**

We replaced the invalid ID with the correct AWS-managed `CachingDisabled` policy ID:

```text
4135ea2d-6df8-44a3-9df3-4b5a84be39ad
```

We verified that the policy existed:

```bash
aws cloudfront get-cache-policy \
  --id 4135ea2d-6df8-44a3-9df3-4b5a84be39ad \
  --profile recipe-app \
  --query 'CachePolicy.CachePolicyConfig.Name' \
  --output text
```

Result:

```text
Managed-CachingDisabled
```

**Lesson learned:**

CloudFormation template validation is necessary but insufficient. Service-specific identifiers should be verified before deploying.

### 7.2 Error: Cannot reuse a parameter from a rolled-back update

**Error message:**

```text
Invalid input for parameter key BackendOriginKey.
Cannot specify usePreviousValue as true for a parameter
key not in the previous template.
```

**Cause:**

The first CloudFront update failed and rolled back.

Because `BackendOriginKey` was introduced in the failed update, it was not part of the previously deployed stack template.

A subsequent attempt to create a change set using:

```text
ParameterKey=BackendOriginKey,UsePreviousValue=true
```

failed.

**Resolution:**

We supplied the original token again through a temporary parameter file.

The file was protected using restrictive permissions and kept outside Git.

**Lesson learned:**

A parameter introduced by a failed update may not be available for reuse after rollback. Parameters must be supplied explicitly when they are not part of the currently deployed stack.

### 7.3 Error: HTTP 400 Bad Request from Django

After the corrected CloudFront deployment, we tested:

```bash
curl -i https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/
```

The response was:

```text
HTTP/1.1 400 Bad Request
Server: nginx/1.30.5
X-Cache: Error from cloudfront
```

The response body contained Django's `Bad Request (400)` HTML page.

**Cause:**

The request successfully reached the EC2 instance and passed through Nginx, but Django rejected the forwarded hostname.

The backend initially allowed only:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

CloudFront used the EC2 origin hostname when forwarding the request, which was not included in Django's allowed hosts.

**Resolution:**

We updated the backend environment file:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ec2-3-214-51-24.compute-1.amazonaws.com
```

We then recreated the Docker container using the updated environment file.

A simple Docker restart would not have loaded the new environment variables.

**Lesson learned:**

When deploying Django behind a reverse proxy or CDN, `ALLOWED_HOSTS` must include the hostname Django receives in the HTTP Host header.

Updating a Docker environment file also requires recreating the container for the new variables to take effect.

### 7.4 Challenge: Preserving existing infrastructure

The frontend was already deployed and functional before API routing was added.

Replacing the CloudFront distribution or S3 bucket would have introduced unnecessary disruption.

To avoid this, we used CloudFormation change sets and checked the `Replacement` field before applying updates.

The final proposed change modified only the existing CloudFront distribution without replacement.

**Lesson learned:**

For infrastructure that is already running, review CloudFormation change sets before execution rather than relying solely on template validation.

## 8. Final Deployment Verification

After correcting the cache policy, supplying the parameter, and updating Django's allowed hosts, we tested the public API endpoint:

```text
https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/
```

The Django REST Framework browsable API loaded successfully.

The API returned:

```text
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
```

Response:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

This confirms that:

1. The public CloudFront endpoint is reachable over HTTPS.
2. The `/api/*` cache behavior routes requests to the EC2 origin.
3. The request reaches Nginx.
4. Nginx forwards the request to Django.
5. Django accepts the forwarded hostname.
6. Django REST Framework returns the expected JSON structure.

The empty ingredient list is expected because the deployed database does not currently contain ingredient records.

This test verifies API accessibility through the deployed frontend domain. Testing the ingredient search feature inside the React interface is a separate frontend integration check.

## 9. Remaining Issues and Limitations

### 9.1 CloudFront SPA error handling

The current CloudFront distribution uses custom error responses that convert HTTP 403 and 404 responses to HTTP 200 and serve `/index.html`.

Although this supports React client-side routing, it can also interfere with API error responses.

For example, an API endpoint that legitimately returns HTTP 404 may be presented as an HTTP 200 response containing the React HTML page.

**Planned improvement:**

Separate SPA routing behavior from API error handling, potentially using a CloudFront Function for frontend route rewriting and removing the distribution-wide custom error mappings.

### 9.2 Unencrypted backend origin connection

The current connection between CloudFront and EC2 uses HTTP on port 80.

Although the public CloudFront endpoint uses HTTPS, the origin connection is not encrypted.

**Planned improvement:**

Configure HTTPS between CloudFront and the backend origin with a valid TLS certificate and update the CloudFront origin protocol policy.

Until then, testing should be restricted to non-sensitive endpoints without credentials or personal information.

### 9.3 Authentication

Amazon Cognito authentication is planned but has not yet been implemented or verified in the deployed environment.

Authenticated API requests should not be enabled through the current HTTP origin connection.

### 9.4 Database

The deployed backend currently uses SQLite for development and midpoint demonstration.

A managed database such as Amazon RDS is a possible future improvement for durability, availability, and scalability.

### 9.5 Automated deployment

Infrastructure is managed using CloudFormation, but automatic application deployment through GitHub Actions and AWS OIDC is not yet fully implemented.

### 9.6 Infrastructure configuration consistency

The EC2 Elastic IP was allocated and associated separately from the current CloudFormation backend stack.

For future maintenance, the Elastic IP association should be brought under infrastructure-as-code management to reduce configuration drift.

## 10. Summary

The CloudFront integration was successfully completed after resolving several deployment issues.

The final architecture serves the React frontend from a private S3 bucket and forwards API requests to Django running in Docker on EC2.

The deployment demonstrated practical experience with:

- Amazon CloudFront distributions, origins, and cache behaviors
- S3 private hosting and Origin Access Control
- CloudFormation template validation, change sets, and rollback
- AWS-managed CloudFront policies
- EC2 security groups and CloudFront managed prefix lists
- Nginx reverse proxy configuration
- Docker container networking and environment configuration
- Django REST Framework deployment and host validation
- Troubleshooting end-to-end HTTP requests

**Final result:** The deployed `/api/ingredients/` endpoint returned HTTP 200 and the expected JSON response through the public CloudFront HTTPS domain.

The integration meets the initial midpoint deployment objective, while authentication, end-to-end encryption, API error handling, and production scalability remain future work.