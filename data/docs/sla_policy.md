# SLA Policy & Escalation Matrix

## SLA Tiers

| Tier | Description | Max Allowed Failures/Week | Escalation Response Time |
|------|-------------|--------------------------|--------------------------|
| Critical | Business-blocking pipelines. Revenue or compliance impact if late. | 0 | Immediate (PagerDuty) |
| High | Important analytics pipelines. Impacts daily reporting. | 1 | Within 30 minutes |
| Medium | Dashboard refreshes, non-urgent aggregations. | 2 | Within 2 hours |
| Low | Archival, housekeeping, non-time-sensitive. | No limit | Next business day |

## Critical Pipelines (Production)
- PL_IngestSalesData_Daily — must complete by 03:00 AEST
- PL_IngestFinanceGL_Incremental — each run must complete within 10 mins
- PL_LoadInventoryFull — must complete by 06:00 AEST Monday

## Escalation Contacts

| Domain | Primary Contact | Escalation |
|--------|----------------|------------|
| Data Engineering | data-engineering@company.com | head-of-data@company.com |
| Sales | sales-ops@company.com | vp-sales@company.com |
| Finance | finance-data@company.com | cfo-office@company.com |
| BI/Reporting | bi-team@company.com | analytics-lead@company.com |

## Incident Classification

**P1 — Critical Incident**  
Any critical-SLA pipeline failing 2+ consecutive runs. Immediate PagerDuty alert. War room within 15 minutes.

**P2 — High Incident**  
High-SLA pipeline failing, or critical pipeline failing first run. Slack alert to #data-platform-alerts. Fix within 2 hours.

**P3 — Medium Incident**  
Medium/Low SLA pipeline failing. Jira ticket. Fix within next business day.

## Retry Policy Standards
- Critical pipelines: 3 retries, 5-minute interval
- High pipelines: 2 retries, 10-minute interval
- Medium/Low: 1 retry, 30-minute interval

## Known Dependency Chain (execution order)
1. PL_IngestSalesData_Daily (02:00)
2. PL_IngestFinanceGL_Incremental (hourly 05:00 onwards)
3. PL_TransformCustomer360 (04:00)
4. PL_PowerBI_RefreshDatasets (06:00) ← depends on 1 & 3 completing
