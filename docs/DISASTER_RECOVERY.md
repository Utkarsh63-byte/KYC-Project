# Disaster Recovery & Resiliency Plan

## Targets & Metrics
- **Recovery Time Objective (RTO)**: $< 15$ minutes
- **Recovery Point Objective (RPO)**: $< 1$ minute (Point-in-Time Restore)

## Failover & Outage Procedures
- **Database**: Multi-AZ RDS PostgreSQL with automatic failover in $<60$ seconds.
- **Document Storage**: AWS S3 99.999999999% (11 9s) durability across 3 Availability Zones.
- **Third-Party AI Service Outage**: System gracefully falls back to queuing documents for retry or routing applications to Human Reviewers with manual document inspection interfaces.
