# AWS CloudFront Deployment and Troubleshooting

**Project:** Recipe Suggestion App  
**AWS Region:** `us-east-1`  
**Deployment method:** AWS CloudFormation  
**Last updated:** October 15, 2026  
**Status:** CloudFront frontend hosting, API routing, and SPA error handling deployed and verified

## 1. Overview

The Recipe Suggestion App uses Amazon CloudFront as the public HTTPS entry point for its React frontend and Django REST Framework API. The React build is hosted in a private Amazon S3 bucket, while Django runs in a Docker container on an Amazon EC2 instance behind Nginx.

CloudFront uses two origins: the S3 origin for the React application and an EC2 custom origin for requests matching `/api/*`. A CloudFront Function rewrites React client-side routes to `/index.html` without changing API error responses. The public frontend and API therefore share one domain.

### 1.1 Deployed resources

| Resource | Value |
|---|---|
| Frontend CloudFormation stack | `recipe-app-frontend` |
| CloudFront distribution ID | `E2YMECNRA0V5YR` |
| Public domain | `https://d1q0iv2raorz8j.cloudfront.net` |
| Private frontend S3 bucket | `recipe-app-frontend-frontendbucket-yhbrd6afosjk` |
| Backend EC2 instance | `i-0f80e33afb9d7dd0a` |
| Backend Elastic IP | `3.214.51.24` |
| Backend origin DNS | `ec2-3-214-51-24.compute-1.amazonaws.com` |
| CloudFront origin-facing prefix list | `pl-3b927c52` |
| Infrastructure template | `infrastructure/cloudformation/frontend.yaml` |
| Backend software | Nginx, Docker, Django REST Framework, SQLite |

## 2. Architecture and request routing

```text
                         Browser
                            |
                          HTTPS
                            |
                     Amazon CloudFront
                            |
              +-------------+-------------+
              |                           |
      Default cache behavior       /api/* cache behavior
              |                           |
    CloudFront Function                  EC2 origin
    SPA route rewrite                  HTTP port 80
              |                           |
       Private S3 bucket                 Nginx
              |                           |
         React build               127.0.0.1:8000
                                          |
                                   Docker / Django
                                          |
                                       SQLite
```

- `/`, `/dashboard`, `/profile`, and other extensionless frontend routes are handled by the default S3 behavior. The CloudFront Function rewrites these paths to `/index.html`.
- JavaScript, CSS, and other file paths are served from S3 without the SPA rewrite.
- `/api/*` requests are routed to EC2, where Nginx forwards them to Django.
- Viewer-to-CloudFront connections use HTTPS; **CloudFront-to-EC2 connections currently use unencrypted HTTP**.

The successful API tests establish that the deployed domain reaches Django. They do not, by themselves, prove that a React component invokes the API; that requires a separate browser Network-tab or UI integration test.

## 3. Initial frontend hosting

The initial CloudFormation frontend stack created a private S3 bucket and a CloudFront distribution. S3 Block Public Access was enabled, and objects use SSE-S3 encryption.

CloudFront Origin Access Control (OAC) grants the distribution access to S3 without making the bucket public. The S3 bucket policy restricts reads to the specific CloudFront distribution ARN.

Initially, React client-side routes were supported with distribution-wide custom error responses:

```yaml
CustomErrorResponses:
  - ErrorCode: 403
    ResponseCode: 200
    ResponsePagePath: /index.html
    ErrorCachingMinTTL: 0
  - ErrorCode: 404
    ResponseCode: 200
    ResponsePagePath: /index.html
    ErrorCachingMinTTL: 0
```

This worked for missing S3 paths representing React routes but later caused incorrect API error responses. **These mappings have since been removed**, as documented in Section 7.

## 4. Adding Django as a CloudFront origin

### 4.1 EC2 origin and API behavior

We added a second origin to `frontend.yaml`:

```yaml
- Id: DjangoAPIOrigin
  DomainName: ec2-3-214-51-24.compute-1.amazonaws.com
  CustomOriginConfig:
    HTTPPort: 80
    OriginProtocolPolicy: http-only
    OriginReadTimeout: 30
```

The backend Elastic IP provides a stable public address for the origin DNS name. We also added an ordered cache behavior for `/api/*`:

```yaml
CacheBehaviors:
  - PathPattern: /api/*
    TargetOriginId: DjangoAPIOrigin
    ViewerProtocolPolicy: redirect-to-https
    AllowedMethods: [GET, HEAD, OPTIONS, PUT, PATCH, POST, DELETE]
    CachedMethods: [GET, HEAD]
    Compress: true
    CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
    OriginRequestPolicyId: b689b0a8-53d0-40ab-baf2-68738e2966ac
```

The cache policy is AWS-managed **CachingDisabled**. The origin request policy is AWS-managed **AllViewerExceptHostHeader**, which sends the origin hostname as the `Host` header. The behavior allows API methods beyond GET, although only the Ingredients GET endpoint was verified during this deployment.

### 4.2 Origin header and EC2 network restrictions

We introduced a CloudFormation parameter for a shared private origin header:

```yaml
Parameters:
  BackendOriginKey:
    Type: String
    NoEcho: true
    MinLength: 32
    Description: Private header value shared by CloudFront and Nginx
```

The CloudFront custom origin includes:

```yaml
OriginCustomHeaders:
  - HeaderName: X-Recipe-Origin-Key
    HeaderValue: !Ref BackendOriginKey
```

The real header value was supplied using a private temporary parameters file, never committed to Git. The `NoEcho` property masks the parameter in certain CloudFormation displays but does not make the HTTP origin connection encrypted or constitute a full secrets-management solution.

The EC2 security group permits inbound TCP port 80 from the AWS-managed CloudFront origin-facing prefix list `pl-3b927c52`, rather than from the entire internet. This prefix list covers CloudFront origin-facing infrastructure generally, not only our distribution. Nginx checks the private header before proxying API traffic.

### 4.3 Nginx and Docker

The relevant Nginx configuration is:

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

`PRIVATE_SECRET_TOKEN` is a documentation placeholder, not the deployed value. Nginx configuration validation passed with `sudo nginx -t`, and the service was enabled. The Docker container publishes Django only on the EC2 loopback interface (`127.0.0.1:8000:8000`), preventing direct access to the Django port from outside EC2.

**Security caveat:** The current HTTP origin hop can expose transmitted data and the origin header to interception. Do not use this configuration for login credentials, authentication tokens, or personal information. End-to-end TLS and application authentication remain required improvements.

## 5. Initial CloudFormation deployment and troubleshooting

### 5.1 Template validation and change sets

We validated the template:

```bash
aws cloudformation validate-template \
  --template-body file://infrastructure/cloudformation/frontend.yaml \
  --region us-east-1 \
  --profile recipe-app
```

For the initial API-origin update, we created a change set using a private temporary JSON file containing `BackendOriginKey`:

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

The file was kept outside the repository with restrictive permissions and deleted after change set creation. The proposed change was `FrontendDistribution: Modify, Replacement: False`; neither the existing distribution nor S3 bucket was scheduled for replacement.

### 5.2 Failure: CloudFront cache policy did not exist

**Observed error:**

```text
Invalid request provided: The specified cache policy does not exist.
(Service: CloudFront, Status Code: 404)
```

**Cause:** The original template used an incorrect managed cache policy ID:

```text
413f1600-6a40-4f8f-9b13-86fa04c8f3e0
```

Template validation had passed, but CloudFormation could not update the distribution with a nonexistent policy. The stack update failed and rolled back.

**Fix:** Replace the ID with the correct `Managed-CachingDisabled` policy:

```text
4135ea2d-6df8-44a3-9df3-4b5a84be39ad
```

We verified the ID directly:

```bash
aws cloudfront get-cache-policy \
  --id 4135ea2d-6df8-44a3-9df3-4b5a84be39ad \
  --profile recipe-app \
  --query 'CachePolicy.CachePolicyConfig.Name' \
  --output text
```

Output: `Managed-CachingDisabled`.

**Lesson:** `validate-template` checks template structure but does not guarantee that every referenced AWS resource or policy exists.

### 5.3 Failure: Parameter unavailable after rollback

**Observed error:**

```text
Invalid input for parameter key BackendOriginKey.
Cannot specify usePreviousValue as true for a parameter key
not in the previous template.
```

**Cause:** `BackendOriginKey` had been introduced in the failed update. Following rollback, the previously deployed stack template did not contain that parameter, so `UsePreviousValue=true` was invalid.

**Fix:** Recreate the change set with the original header token supplied through a private parameters file. Once that update succeeded, the parameter became part of the deployed stack and could be reused in later updates.

**Lesson:** A newly introduced parameter from a rolled-back update cannot necessarily be reused as a previous stack parameter.

### 5.4 Failure: Django returned HTTP 400

After CloudFront successfully routed requests to EC2, the first API test returned:

```http
HTTP/1.1 400 Bad Request
Server: nginx/1.30.5
Content-Type: text/html; charset=utf-8
```

**Cause:** Django's environment initially contained:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

The CloudFront origin request used the EC2 origin hostname in the HTTP `Host` header. Nginx forwarded that hostname to Django, where it failed `ALLOWED_HOSTS` validation.

**Fix:** Update `/opt/recipe-app/backend.env` to include the EC2 origin hostname:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ec2-3-214-51-24.compute-1.amazonaws.com
```

The Docker container was recreated using the same image, port mapping, environment file, and persistent SQLite bind mount. A simple `docker restart` would not have reloaded the changed environment file.

**Lesson:** Verify the forwarded `Host` header when deploying Django behind CloudFront and Nginx; recreate containers when changing Docker-supplied environment variables.

### 5.5 Initial successful API test

After the fixes, the public endpoint worked:

```bash
curl -i 'https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/'
```

The Django REST Framework response returned HTTP 200 with a paginated JSON object:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

The empty list was expected because the deployed SQLite database did not yet contain ingredient records.

## 6. Discovered problem: API errors were replaced with React HTML

Although the valid Ingredients endpoint worked, a request for a nonexistent ingredient exposed a routing problem:

```bash
curl -i 'https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/999999/'
```

**Incorrect response before the fix:**

```http
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 458
```

The distribution-wide `CustomErrorResponses` rules were converting the backend's HTTP 404 into HTTP 200 and serving the React `index.html` file. This could mislead API clients, break JSON parsing, and hide genuine backend errors.

We needed to preserve React client-side navigation while allowing Django to return its own HTTP status codes and JSON errors.

## 7. Fix: CloudFront Function for SPA routing

### 7.1 New CloudFront Function

We added the following resource to `frontend.yaml` under `Resources`:

```yaml
FrontendSpaRewriteFunction:
  Type: AWS::CloudFront::Function
  Properties:
    Name: !Sub '${AWS::StackName}-spa-rewrite'
    AutoPublish: true
    FunctionConfig:
      Comment: Rewrite React SPA routes to index.html
      Runtime: cloudfront-js-1.0
    FunctionCode: |
      function handler(event) {
        var request = event.request;
        var uri = request.uri;

        // Leave API requests unchanged.
        if (uri === '/api' || uri.indexOf('/api/') === 0) {
          return request;
        }

        // Leave static files unchanged.
        if (uri.indexOf('.') !== -1) {
          return request;
        }

        // Rewrite React routes to index.html.
        request.uri = '/index.html';
        return request;
      }
```

The function is associated with the **default S3 cache behavior only**, not the `/api/*` behavior:

```yaml
FunctionAssociations:
  - EventType: viewer-request
    FunctionARN: !GetAtt FrontendSpaRewriteFunction.FunctionARN
```

We removed the distribution-wide `CustomErrorResponses` mappings. The CloudFront Function now handles SPA navigation, while the backend returns its own errors.

**Routing details:** The default behavior rewrites extensionless frontend paths such as `/dashboard` and `/profile` to `/index.html`. File paths containing a period, such as `/assets/nonexistent.js`, remain unchanged. Requests matching `/api/*` use their separate behavior and do not execute this function. The function's `/api` check also leaves that path unchanged if it reaches the default behavior.

### 7.2 Deploying the SPA fix

We validated the updated template, then created a second change set:

```bash
aws cloudformation create-change-set \
  --stack-name recipe-app-frontend \
  --change-set-name fix-spa-api-error-handling \
  --change-set-type UPDATE \
  --template-body file://infrastructure/cloudformation/frontend.yaml \
  --parameters ParameterKey=BackendOriginKey,UsePreviousValue=true \
  --region us-east-1 \
  --profile recipe-app
```

This time `UsePreviousValue=true` worked because `BackendOriginKey` was already part of the successfully deployed stack.

The change set showed:

| Action | Logical resource | Replacement |
|---|---|---|
| Modify | `FrontendDistribution` | False |
| Add | `FrontendSpaRewriteFunction` | None |

We executed the change set, then tested API responses, SPA routes, and missing static assets. The existing CloudFront distribution and S3 bucket were preserved.

## 8. Final verification

All four post-fix tests passed against the deployed CloudFront domain.

| Test | Command / path | Observed result | Status |
|---|---|---|---|
| Missing ingredient | `/api/ingredients/999999/` | HTTP 404, JSON error | Passed |
| Valid ingredients list | `/api/ingredients/?format=json` | HTTP 200, JSON | Passed |
| React client-side route | `/dashboard` | HTTP 200, HTML | Passed |
| Missing static asset | `/assets/nonexistent.js` | HTTP 403 or 404, not 200 | Passed |

The missing-ingredient response after the fix was:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
Server: nginx/1.30.5
```

```json
{
  "detail": "No Ingredient matches the given query."
}
```

This verifies that CloudFront no longer replaces Django API errors with React HTML. It also confirms that the React route rewrite still works and missing JavaScript files are not disguised as successful HTML responses.

### 8.1 Local shell issue during testing

A query-string test initially failed in the local zsh shell:

```text
zsh: no matches found: https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/?format=json
```

This was **not** an AWS error. zsh interpreted the unquoted `?` as a filename wildcard. Quoting the URL fixed the command:

```bash
curl -i 'https://d1q0iv2raorz8j.cloudfront.net/api/ingredients/?format=json'
```

## 9. Lessons learned

1. **Validate resource identifiers, not just YAML.** A valid CloudFormation template can still fail when an AWS-managed policy ID is incorrect.
2. **Understand rollback state.** A parameter added by a failed update is not necessarily available through `UsePreviousValue`.
3. **Check reverse-proxy headers.** Django's `ALLOWED_HOSTS` must match the `Host` header received through CloudFront and Nginx.
4. **Keep SPA routing separate from API errors.** Distribution-wide error remapping can turn genuine API failures into HTTP 200 HTML responses.
5. **Use change sets for live infrastructure.** Both successful changes were reviewed for resource replacement before execution.
6. **Test failures as well as successes.** Missing API resources and missing assets exposed problems that a successful GET alone would not reveal.
7. **Protect secrets and understand the limits of controls.** The origin header and CloudFront prefix-list restriction reduce exposure but do not replace HTTPS or user authentication.

## 10. Remaining work and limitations

| Item | Current state / next action |
|---|---|
| CloudFront SPA and API error handling | **Resolved and verified** |
| End-to-end HTTPS | **Pending:** CloudFront-to-EC2 origin still uses HTTP; add a valid TLS certificate and HTTPS origin configuration |
| Authentication | **Pending:** Amazon Cognito integration has not been verified in the deployed backend |
| Database | **Pending:** SQLite is used for the midpoint environment; evaluate RDS for future requirements |
| CI/CD | **Pending:** GitHub OIDC infrastructure exists, but automated application deployment is not complete |
| Elastic IP infrastructure-as-code | **Pending:** EIP allocation/association were performed outside the backend CloudFormation stack |
| SPA rewrite edge cases | Current rule treats extensionless default-origin paths as SPA routes; refine if future assets or server paths require different behavior |
| Frontend feature integration | API availability through the shared domain is verified; actual React ingredient-search interaction should be verified separately if not already tested |

## 11. Conclusion

CloudFront now serves the React frontend from a private S3 bucket and routes `/api/*` requests to Django on EC2 through Nginx. The deployment was completed through CloudFormation without replacing the existing frontend distribution or bucket.

We resolved an invalid CloudFront cache policy, a parameter-reuse error after rollback, a Django `ALLOWED_HOSTS` rejection, and distribution-wide SPA error handling that had masked Django 404 responses. The final API, React routing, and missing-asset tests all passed.

**Final status as of October 15, 2026:** CloudFront frontend hosting, Django API routing, and SPA error handling are deployed and verified. End-to-end origin encryption, authentication, and production scalability remain future work.
