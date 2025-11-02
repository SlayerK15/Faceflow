# README.md

## FaceFlow — Cloud-first Face Grouping & Sharing

FaceFlow is a mobile/web app where users upload photos, the backend de‑duplicates, detects faces, builds embeddings, clusters them into "face groups," and lets users bulk‑share the right photos with the right recipients. The entire pipeline runs on AWS. The core face algorithm (detection + embeddings) is trained **from scratch** on Amazon SageMaker.

---

## Features

* Upload large batches from web and mobile (resumable multipart)
* Exact & near-duplicate detection (SHA‑256, pHash, SSIM)
* Face detection → alignment → 512‑D embeddings (ArcFace objective)
* Album‑scoped clustering (HDBSCAN + FAISS for incremental assignment)
* Human‑in‑the‑loop: merge/split clusters, label people
* Secure sharing via CloudFront signed URLs; bulk ZIP export
* Privacy-first: keep embeddings, optional purge originals
* Fully managed AWS: S3, Step Functions, Lambda, SageMaker, DynamoDB, CloudFront, Cognito, SES/SNS

---

## Architecture (High Level)

```
[ Web (Next.js) ]   [ Mobile (React Native) ]
          │
      Amazon Cognito (Auth)
          │
      API Gateway (REST + WS)
          │
        Lambda (FastAPI via LWA)
          │
   S3 (raw-uploads bucket) ──► EventBridge/S3 Events ──► SQS ──► Step Functions
                                                      │
                                                      ├─ Lambda: EXIF/Hashes/Thumbs
                                                      ├─ SageMaker Processing: detect+align
                                                      ├─ SageMaker Endpoint: embeddings
                                                      └─ Lambda: FAISS/HDBSCAN clustering → DynamoDB

S3: raw/derived/embeddings/exports     DynamoDB: users, albums, photos, faces, clusters, jobs
CloudFront: CDN + signed URLs          SES/SNS: share links
KMS: encryption                        CloudWatch + X‑Ray: observability
```

---

## Tech Stack

* **Frontend Web**: Next.js 15, TypeScript, React Query, AWS Amplify Auth UI
* **Mobile**: React Native (Expo), Amplify Auth
* **API**: FastAPI on AWS Lambda via Lambda Web Adapter (LWA)
* **Workers**: Lambda + Step Functions; FAISS clustering in Lambda or Fargate task
* **ML**: PyTorch 2.x (from scratch training), SageMaker Training/Processing/Endpoints
* **Data**: S3 (images, crops, embeddings), DynamoDB (single-table), CloudFront (delivery)
* **IaC**: Terraform, GitHub Actions (OIDC to AWS)

---

## Repository Layout

```
faceflow/
  infra/terraform/
    modules/
      api/           # API Gateway + Lambda + roles
      auth/          # Cognito User Pool + Identity Pool
      ddb/           # DynamoDB single-table + GSIs
      s3/            # Buckets + policies + event notifications
      cf/            # CloudFront distribution, origins, behaviors
      events/        # EventBridge, SQS, Step Functions
      sagemaker/     # ECR repos, Model Registry, endpoints
      iam/           # Fine-grained roles/policies
    envs/
      dev/
      prod/
  services/
    api/             # FastAPI app (Lambda entry via LWA)
    clustering/      # FAISS/HDBSCAN assignment (Lambda/Fargate)
    exporter/        # ZIP builder + signed URLs
    detection/       # Training & Processing (SageMaker container)
    embedding/       # Training & Inference (SageMaker container)
  frontend/
    web/
    mobile/
  .github/workflows/
  Makefile
  README.md
  agent.md
```

---

## Prerequisites

* AWS account with admin for bootstrap (then least-privileged roles)
* Terraform ≥ 1.8
* Node.js ≥ 20, pnpm ≥ 9
* Python ≥ 3.12, Docker ≥ 24
* AWS CLI v2, jq

---

## Quick Start (Dev)

1. **Clone & bootstrap**

```bash
pnpm i -g pnpm
make bootstrap   # installs git hooks, pre-commit, pnpm - if provided
```

2. **Create `.env` files** (examples below) and **configure AWS** profile.

3. **Provision core infra (dev)**

```bash
cd infra/terraform/envs/dev
terraform init
terraform apply -var-file=dev.tfvars
```

Outputs will include:

* `raw_bucket`, `derived_bucket`, `embeddings_bucket`
* `ddb_table`
* `api_url`, `ws_url`, `cognito_pool_ids`

4. **Build and push ML containers to ECR**

```bash
make build-ml     # builds services/detection and services/embedding
make push-ml      # pushes to ECR repos created by terraform
```

5. **Create SageMaker models & endpoint**

```bash
make sagemaker-deploy   # registers model, creates endpoint config + endpoint
```

6. **Deploy API + workers**

```bash
make deploy-api
make deploy-workers
```

7. **Run Web (local)**

```bash
cd frontend/web
pnpm i && pnpm dev
```

---

## Environment Variables

### `services/api/.env`

```
APP_ENV=dev
TABLE_NAME=<ddb_table>
RAW_BUCKET=<raw_bucket>
DERIVED_BUCKET=<derived_bucket>
EMBEDDINGS_BUCKET=<embeddings_bucket>
COGNITO_USER_POOL_ID=...
COGNITO_CLIENT_ID=...
SAGEMAKER_EMBEDDING_ENDPOINT=<name>
CLOUDFRONT_DOMAIN=<domain>
SES_SENDER=noreply@your-domain.com
```

### `services/detection/.env` (training & processing)

```
S3_TRAIN_DATA_BUCKET=...
S3_OUTPUT_BUCKET=...
```

### `services/embedding/.env`

```
EMBED_DIM=512
```

---

## Data Model (DynamoDB single-table)

**PK/SK patterns**

```
PK=USER#{userId}    SK=ALBUM#{albumId}              → album
PK=ALBUM#{albumId}  SK=PHOTO#{photoId}              → photo meta (S3 keys, EXIF, hashes)
PK=ALBUM#{albumId}  SK=FACE#{faceId}                → bbox, crop key, embedding key
PK=ALBUM#{albumId}  SK=CLUSTER#{clusterId}          → centroid, member ids
PK=ALBUM#{albumId}  SK=RECIPIENT#{recipientId}
PK=ALBUM#{albumId}  SK=JOB#{jobId}                  → pipeline state
```

**Indexes**: LSI1 (by `createdAt`), GSI1 (by `status`), GSI2 (by `userId#albumId`).

---

## S3 Layout

```
s3://faceflow-raw-uploads/tenant/{userId}/{albumId}/YYYY/MM/DD/{uuid}.jpg
s3://faceflow-derived/thumb/{photoId}.jpg
s3://faceflow-derived/crops/{faceId}.jpg
s3://faceflow-embeddings/{photoId}.npy
s3://faceflow-exports/share/{shareId}/archive.zip
```

---

## Pipelines

### Step Functions (pseudo-ASL)

```json
{
  "Comment": "Photo ingestion pipeline",
  "StartAt": "ExtractEXIF",
  "States": {
    "ExtractEXIF": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "Next": "DetectAlign"},
    "DetectAlign": {"Type": "Task", "Resource": "arn:aws:states:::sagemaker:createProcessingJob.sync", "Next": "Embed"},
    "Embed": {"Type": "Task", "Resource": "arn:aws:states:::sagemaker:invokeEndpoint", "Next": "Cluster"},
    "Cluster": {"Type": "Task", "Resource": "arn:aws:states:::lambda:invoke", "Next": "Notify"},
    "Notify": {"Type": "Task", "Resource": "arn:aws:states:::sns:publish", "End": true}
  }
}
```

### De-duplication

* SHA‑256 exact matches
* pHash + SSIM thresholding → prefer highest resolution and face count

### Clustering (album-scoped)

* L2-normalized embeddings; cosine similarity via inner product
* HDBSCAN for batch; FAISS for incremental nearest-centroid assignment

---

## API (Sketch)

```
POST /albums                          → create album
POST /albums/{id}/uploadUrl           → presigned PUT URL
GET  /albums/{id}/status              → job status + counts
GET  /albums/{id}/clusters            → cluster list + confidences
POST /albums/{id}/clusters/{cid}/label  {name}
POST /albums/{id}/clusters/merge        {a,b,c}
POST /albums/{id}/share                 {recipients, filters}
GET  /shares/{shareId}                → list signed contents
```

Auth via Cognito JWT; rate-limits via API GW usage plans.

---

## Local Development

* For web/mobile: run against dev cloud APIs
* For API unit tests: `pytest -q` with moto for DDB/S3 and local FAISS
* For ML: dockerized training on a local GPU is supported; emit artifacts to `./artifacts/`

---

## CI/CD

* PR: lint/test → docker build → push to ECR (dev) → plan (Terraform) → deploy preview API
* Main: promote to `dev` env; manual approval to `prod`
* SageMaker Model Registry: register new model → blue/green deploy to endpoint

---

## Security & Compliance

* KMS encryption for S3 and DynamoDB; private VPC endpoints for SageMaker/S3
* IAM least-privilege roles per service; no long-lived secrets (use IRSA/OIDC)
* Data subject deletion: wipe S3 prefixes & DDB items on request

---

## Observability

* CloudWatch metrics/alarms (error rate, SQS age, SFN failures)
* X‑Ray traces across API → Lambda → SageMaker
* Structured logs (JSON) with request IDs

---

## Cost Notes (dev-size ballpark)

* S3 (200 GB): ~$5–$6 + requests
* DynamoDB on-demand: $15–$60
* SageMaker: serverless or low‑duty g5 endpoint; batch processing on Spot
* CloudFront egress depends on shares

---

## Roadmap

* MVP: dedupe, detect, embed, cluster, share
* V1: FAISS online assignment, CloudFront Image Handler, SES templates
* V2: Active learning + weekly retrain; serverless inference
* V3: Multi-tenant SaaS, billing, analytics

---

# agent.md

## Purpose

This file tells a coding agent (e.g., Codex) exactly how to scaffold and implement FaceFlow. Follow steps in order. Produce working code, infra, and CI/CD.

---

## Global Constraints

* Languages: TypeScript (web/mobile), Python 3.12 (API/ML)
* Frameworks: Next.js 15, FastAPI, PyTorch 2.x
* Cloud: AWS only; IaC = Terraform; Containers = Docker/ECR
* Security: least privilege IAM, KMS encryption, private networking for SageMaker
* Style: Black + Ruff (Python), Biome/ESLint + Prettier (TS); Conventional Commits

---

## Versions (pin)

* python = 3.12.x
* node = 20.x; pnpm = 9.x
* pytorch = 2.4.x; faiss-cpu = latest; hdbscan = latest
* awscli v2; terraform 1.8+

---

## Step 0 — Repo Scaffolding

1. Create the tree shown in README under **Repository Layout**.
2. Add root configs:

   * `.editorconfig`, `.gitignore`, `.gitattributes`
   * `pyproject.toml` (black, ruff, pytest), `pnpm-workspace.yaml`
   * `Makefile` with targets: `bootstrap, fmt, lint, test, build-ml, push-ml, deploy-api, deploy-workers, sagemaker-deploy`
3. Add `.github/workflows/`:

   * `ci.yml`: lint+tests, docker build, Terraform plan
   * `deploy.yml`: on main; deploy dev; manual prod promotion

---

## Step 1 — Terraform Modules

Create modules under `infra/terraform/modules/` with inputs/outputs:

* `auth/`: Cognito User Pool, App Client, Identity Pool
* `s3/`: raw/derived/embeddings/exports buckets; event notifications → SQS
* `ddb/`: single-table + LSIs/GSIs
* `api/`: API Gateway (REST + WS), Lambda (FastAPI via Lambda Web Adapter), permissions
* `events/`: SQS queue, DLQ, Step Functions state machine skeleton
* `sagemaker/`: ECR repos (detection, embedding), Model Registry, endpoint (serverless or g5), VPC endpoints
* `cf/`: CloudFront distro with S3 origins and signed URLs
* `iam/`: fine-grained IAM roles (api, clustering, exporter, sagemaker-exec)
  Create `envs/dev` and `envs/prod` with variables and backends; print required outputs.

**Acceptance**: `terraform apply` creates buckets, table, API, queues, state machine, ECR, and (optional) a placeholder SageMaker endpoint.

---

## Step 2 — API Service (FastAPI on Lambda)

Path: `services/api/`

* `app/main.py` with routes from README **API (Sketch)**
* Auth: validate Cognito JWT using JWKS
* DynamoDB access via boto3; resource names from env vars
* S3 presigned PUTs for `/uploadUrl`
* Start Step Functions execution after upload (album/job)
* WebSocket (optional) for progress notifications
* Packaging: `Dockerfile` using AWS Lambda Python base + Lambda Web Adapter

**Tests**: pytest for handlers; moto for DDB/S3; schema tests with pydantic models.

---

## Step 3 — Ingestion Lambda (EXIF/Hashes/Thumbs)

Path: `services/api/` or separate `services/ingestion/`

* Extract EXIF (piexif), compute SHA‑256, pHash; write to DDB
* Generate thumbnail (Pillow) → `derived/thumb/`
* Idempotent processing; safe for retries

---

## Step 4 — Detection (Train from Scratch) — SageMaker

Path: `services/detection/`

* Implement PyTorch training script: MobileNetV3+FPN detector, focal loss
* Export TorchScript for Processing & optional real-time detection
* Processing entrypoint to read S3 raw, emit aligned crops to `derived/crops/` and JSON with bboxes
* `Dockerfile` for training/processing container; push to ECR

**Acceptance**: Processing job runs on a sample set; outputs crops + JSON to S3.

---

## Step 5 — Embedding (Train from Scratch) — SageMaker

Path: `services/embedding/`

* ResNet/EfficientNet backbone, ArcFace head (512‑D)
* Training script reading aligned crops; outputs model.pt
* Inference handler (SageMaker) that returns L2‑normalized vectors
* `Dockerfile` for training + inference; register model; create endpoint

**Acceptance**: Invoke endpoint returns 512‑D vectors for input crops.

---

## Step 6 — Clustering Service

Path: `services/clustering/`

* Build FAISS index per album; batch HDBSCAN for fresh albums
* Incremental assignment: nearest centroid threshold τ; create new cluster if below τ
* Update DDB with `CLUSTER#{clusterId}` and membership
* Ship as Lambda (faiss-cpu layer or manylinux wheel) or Fargate task if size exceeds Lambda limits

**Acceptance**: Given a set of embeddings in S3, produces clusters in DDB.

---

## Step 7 — Exporter / Sharing

Path: `services/exporter/`

* Build per-recipient ZIP from selected clusters
* Write to `exports/` and return CloudFront signed URL
* SES template to email share link

---

## Step 8 — Frontend Web (Next.js)

Path: `frontend/web/`

* Auth flows with Amplify (Cognito Hosted UI)
* Upload UI with multipart + progress
* Album view with cluster chips (merge/split/label)
* Share dialog: pick recipients, preview bundle

**Acceptance**: End-to-end demo with small image set.

---

## Step 9 — Mobile (React Native / Expo)

* Sign-in with Cognito
* Native image picker → multipart upload
* Minimal cluster review + share flow

---

## Step 10 — Step Functions Orchestration

* Define ASL from README; wire Lambda/Processing/Endpoint tasks
* Error handling, retries, DLQs; write `JOB#{jobId}` status transitions

---

## Testing & Quality Gates

* Unit tests: API, ingestion, clustering logic
* Integration tests: synthetic upload triggers pipeline; assert clusters created
* Load test: k6 or artillery on uploadUrl + presigned PUT
* ML eval: track ROC@FAR, cluster purity, user edit rate

---

## Observability & Alarms

* CloudWatch dashboards: API 5xx, SQS age, SFN failure count, Endpoint latency
* Alarms to SNS; X‑Ray tracing enabled

---

## Definition of Done (per service)

* Linted & 90% unit test pass
* Terraform plan clean; zero drift
* Minimal runbook in `RUNBOOK.md`
* Cost note and limits documented

---

## Makefile Targets (sketch)

```
bootstrap:
	pnpm -v || npm i -g pnpm

fmt:
	ruff check --fix services/** && black services/**
	pnpm -C frontend/web fmt

lint:
	ruff check services/**
	pnpm -C frontend/web lint

test:
	pytest -q

build-ml:
	docker build -t detection:dev services/detection
	docker build -t embedding:dev services/embedding

push-ml:
	# tag & push to ECR (use env outputs)

deploy-api:
	# package & deploy Lambda (sam or zip to S3 + terraform apply)

sagemaker-deploy:
	# register model, endpoint config, endpoint
```

---

## Commit & PR Rules

* Conventional Commits (`feat:`, `fix:`, `chore:`)
* Small, reviewable PRs; include screenshots for UI and sample JSON for APIs
* Link CloudWatch logs and SFN exec ARNs in PR description for e2e runs

---

## Fallbacks & Limits

* If FAISS wheels exceed Lambda limits, switch clustering to Fargate
* If endpoint idle cost is high, use SageMaker Serverless or batch Transform
* For very large albums, shard clustering by day, then merge with hierarchical pass
#   F a c e f l o w  
 