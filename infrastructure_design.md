# Stealth Legal AI - Infrastructure Design

## Executive Summary

This document outlines the production architecture for scaling the Stealth Legal AI document management service from prototype to enterprise-grade deployment.

## Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   CDN/Edge      │    │   Monitoring    │
│   (ALB/NLB)     │    │   (CloudFront)  │    │   (CloudWatch)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   Web Frontend  │    │   Logging       │
│   (Kong/AWS)    │    │   (S3 + CF)     │    │   (ELK Stack)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   Search        │    │   Cache Layer   │
│   (ECS/K8s)     │    │   (Elasticsearch)│   │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   File Storage  │    │   Backup        │
│   (RDS Aurora)  │    │   (S3)          │    │   (S3 + Glacier)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Infrastructure Components

### 1. Compute & Application Layer

**Primary Choice: AWS ECS with Fargate**
- **Why**: Serverless containers, auto-scaling, managed service
- **Alternative**: Kubernetes (EKS) for more control
- **Scaling**: Horizontal pod autoscaling based on CPU/memory
- **Deployment**: Blue-green deployments with ALB

**Configuration:**
```yaml
# ECS Service Configuration
Service:
  DesiredCount: 3
  MinCapacity: 2
  MaxCapacity: 20
  TargetCPUUtilization: 70%
  TargetMemoryUtilization: 80%
```

### 2. Database Layer

**Primary Choice: Amazon Aurora PostgreSQL**
- **Why**: ACID compliance, read replicas, point-in-time recovery
- **Scaling**: Multi-AZ deployment, read replicas for search queries
- **Backup**: Automated daily backups, 35-day retention

**Migration Path:**
```sql
-- From SQLite to PostgreSQL
-- Automated migration script
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    etag VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_etag ON documents(etag);
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

### 3. Search Infrastructure

**Primary Choice: Elasticsearch (OpenSearch)**
- **Why**: Full-text search, faceted search, relevance scoring
- **Deployment**: Managed service (AWS OpenSearch)
- **Scaling**: Multi-node cluster, auto-scaling

**Configuration:**
```json
{
  "index_settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "legal_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  }
}
```

### 4. Caching Layer

**Primary Choice: Redis (ElastiCache)**
- **Why**: In-memory caching, session storage, rate limiting
- **Use Cases**: 
  - Document ETags
  - Search results caching
  - Rate limiting tokens
  - Session management

**Configuration:**
```yaml
Redis:
  Engine: redis
  NodeType: cache.r6g.large
  NumCacheNodes: 2
  MultiAZ: true
  AutomaticFailover: enabled
```

## Security & Compliance

### 1. Authentication & Authorization

**Primary Choice: AWS Cognito + JWT**
- **Features**: SSO integration, MFA, user pools
- **Integration**: OAuth2/OIDC providers (Google, Microsoft)
- **Authorization**: Role-based access control (RBAC)

**Implementation:**
```python
# FastAPI middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    if token:
        user = verify_jwt_token(token)
        request.state.user = user
    return await call_next(request)
```

### 2. Data Encryption

**At Rest:**
- Database: AES-256 encryption
- S3: Server-side encryption (SSE-S3)
- EBS: Encryption by default

**In Transit:**
- TLS 1.3 for all communications
- API Gateway: HTTPS only
- Database: SSL/TLS connections

### 3. Compliance Framework

**GDPR Compliance:**
- Data residency controls
- Right to be forgotten
- Data portability
- Privacy by design

**SOC 2 Type II:**
- Access controls
- Audit logging
- Change management
- Incident response

## CI/CD Pipeline

### 1. Pipeline Architecture

```yaml
# GitHub Actions / AWS CodePipeline
Pipeline:
  Stages:
    - Source:
        Repository: GitHub
        Branch: main
    - Build:
        - Run tests
        - Build Docker image
        - Security scan
    - Deploy:
        - Staging deployment
        - Integration tests
        - Production deployment
```

### 2. Deployment Strategy

**Blue-Green Deployment:**
```yaml
Deployment:
  Strategy: BlueGreen
  HealthCheck:
    Path: /health
    Interval: 30s
    Timeout: 5s
    HealthyThreshold: 2
    UnhealthyThreshold: 3
  Rollback:
    Automatic: true
    Triggers:
      - ErrorRate > 5%
      - ResponseTime > 2s
```

## Monitoring & Observability

### 1. Metrics & Alerting

**Key Metrics:**
- API response time (p95 < 500ms)
- Error rate (< 1%)
- Document processing time
- Search query performance
- Database connection pool usage

**Alerting:**
```yaml
Alerts:
  - Name: HighErrorRate
    Condition: ErrorRate > 1%
    Actions: [SNS, PagerDuty]
  
  - Name: HighLatency
    Condition: P95ResponseTime > 500ms
    Actions: [SNS, Slack]
```

### 2. Logging Strategy

**Centralized Logging:**
- Application logs → CloudWatch Logs
- Access logs → ALB logs
- Database logs → RDS logs
- Search logs → OpenSearch logs

**Log Aggregation:**
```yaml
Logging:
  Format: JSON
  Fields:
    - timestamp
    - level
    - service
    - trace_id
    - user_id
    - operation
```

### 3. Distributed Tracing

**Implementation: AWS X-Ray**
- Request tracing across services
- Performance bottleneck identification
- Dependency mapping

## Scalability & Performance

### 1. Auto-scaling Strategy

**Application Scaling:**
```yaml
AutoScaling:
  TargetCPUUtilization: 70%
  TargetMemoryUtilization: 80%
  ScaleUpCooldown: 300s
  ScaleDownCooldown: 600s
  MinInstances: 2
  MaxInstances: 20
```

### 2. Database Scaling

**Read Replicas:**
- Primary: Write operations
- Replicas: Read operations, search queries
- Auto-scaling based on CPU utilization

### 3. Caching Strategy

**Multi-level Caching:**
1. **Application Cache**: Redis for ETags, session data
2. **CDN Cache**: Static assets, API responses
3. **Database Cache**: Query result caching

## Cost Optimization

### 1. Resource Right-sizing

**Instance Types:**
- Development: t3.small
- Staging: t3.medium
- Production: c6g.large (ARM-based, cost-effective)

**Storage Optimization:**
- S3 Intelligent Tiering
- Database storage optimization
- Log retention policies

### 2. Multi-region Strategy

**Primary Region**: us-east-1
**Secondary Region**: us-west-2 (DR)
**Edge Locations**: CloudFront for global performance

## Disaster Recovery

### 1. Backup Strategy

**Database Backups:**
- Automated daily backups
- Point-in-time recovery (35 days)
- Cross-region backup replication

**Application Recovery:**
- Infrastructure as Code (Terraform)
- Multi-AZ deployment
- Auto-scaling for failover

### 2. RTO/RPO Targets

- **RTO**: 15 minutes (application recovery)
- **RPO**: 1 hour (data loss tolerance)

## Operational Considerations

### 1. Change Management

**Deployment Windows:**
- Maintenance windows: Sunday 2-4 AM UTC
- Emergency deployments: Anytime with approval

**Rollback Strategy:**
- Automatic rollback on health check failures
- Manual rollback via CI/CD pipeline

### 2. Incident Response

**Escalation Matrix:**
1. On-call engineer (15 min response)
2. Senior engineer (30 min response)
3. Engineering manager (1 hour response)

**Communication:**
- Status page for customers
- Slack notifications for team
- PagerDuty for critical alerts

## Migration Plan

### Phase 1: Infrastructure Setup (Week 1-2)
- Set up AWS infrastructure
- Configure CI/CD pipeline
- Implement monitoring

### Phase 2: Database Migration (Week 3)
- Set up Aurora PostgreSQL
- Migrate data from SQLite
- Update application code

### Phase 3: Search Migration (Week 4)
- Deploy Elasticsearch
- Migrate search functionality
- Performance testing

### Phase 4: Security & Compliance (Week 5-6)
- Implement authentication
- Add encryption
- Compliance audit

### Phase 5: Production Deployment (Week 7)
- Blue-green deployment
- Load testing
- Go-live

## Risk Mitigation

### 1. Technical Risks
- **Database migration**: Extensive testing, rollback plan
- **Search performance**: Load testing, optimization
- **Security vulnerabilities**: Regular security scans

### 2. Operational Risks
- **Team capacity**: Cross-training, documentation
- **Third-party dependencies**: Vendor evaluation, alternatives
- **Compliance gaps**: Regular audits, expert consultation

## Success Metrics

### 1. Performance Metrics
- API response time < 500ms (p95)
- Search query time < 200ms
- 99.9% uptime SLA

### 2. Business Metrics
- User adoption rate
- Document processing volume
- Search query volume

### 3. Operational Metrics
- Mean time to recovery (MTTR) < 30 minutes
- Deployment frequency: Daily
- Change failure rate < 5%
