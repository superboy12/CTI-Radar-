# Database Schema Documentation

## Overview

The CTI platform uses PostgreSQL with SQLAlchemy ORM (async).
All models use UUID primary keys and include `created_at` timestamps.

## Entity List

| Entity | Table | Description |
|--------|-------|-------------|
| User | `users` | Platform users with roles |
| Domain | `domains` | Core entity - tracked domains |
| IP | `ips` | IP addresses resolved from domains |
| Nameserver | `nameservers` | DNS nameservers |
| Certificate | `certificates` | TLS/SSL certificates |
| DomainIP | `domain_ips` | Domain ↔ IP junction |
| DomainNameserver | `domain_nameservers` | Domain ↔ NS junction |
| DomainCertificate | `domain_certificates` | Domain ↔ Cert junction |
| DomainAnalysis | `domain_analyses` | Analysis snapshots |
| ScanJob | `scan_jobs` | Batch analysis jobs |
| Dataset | `datasets` | ML training datasets |
| MLModel | `ml_models` | Trained ML models |
| Experiment | `experiments` | Reproducible experiments |
| MLPrediction | `ml_predictions` | Classification predictions |
| Alert | `alerts` | Threat alerts |
| BlocklistEntry | `blocklist_entries` | DNS blocklist/whitelist |
| FilterPolicy | `filter_policies` | DNS filtering rules |
| ThreatSource | `threat_sources` | Intel source tracking |
| AuditLog | `audit_logs` | User action audit trail |

## Classification Values

### Domain Classification
- `LEGITIMATE` - Domain is assessed as legitimate
- `SUSPICIOUS` - Domain shows suspicious indicators  
- `GAMBLING_INDICATED` - Domain shows gambling indicators

### Risk Level
- `LOW` - Low risk
- `MEDIUM` - Medium risk
- `HIGH` - High risk

### Domain Status
- `pending` - Awaiting analysis
- `analyzing` - Currently being analyzed
- `analyzed` - Analysis complete
- `error` - Analysis failed

### User Roles
- `ADMIN` - Full platform access
- `RESEARCHER` - Can create/modify domains and run ML
- `VIEWER` - Read-only access

## Key Relationships

- A Domain can resolve to multiple IPs (many-to-many via `domain_ips`)
- An IP can host multiple Domains (infrastructure sharing detection)
- A Domain can have multiple Analyses over time (history)
- A Domain can have multiple ML Predictions from different models
- Each Experiment links a Dataset with a Model and stores metrics
