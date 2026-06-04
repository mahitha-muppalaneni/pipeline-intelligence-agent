# Pipeline Runbooks & Knowledge Base

## PL_IngestSalesData_Daily

**Owner:** Data Engineering Team  
**SLA:** Critical — must complete by 03:00 AEST daily  
**Schedule:** Every day at 02:00 AEST (ScheduleTrigger: trg_daily_0200_aest)  
**Domain:** Sales  

### Description
Incremental ingestion of sales transaction data from the production SQL Server (`sql-sales-prod.database.windows.net`) into Azure Blob Storage silver layer. Uses high-watermark pattern based on transaction date.

### Architecture
SQL Server (source) → Lookup watermark → Copy Activity → Blob Storage (silver/sales) → Update watermark stored procedure

### Common Failures & Resolutions

**SqlFailedToConnect (UserError)**  
- Root cause: Network connectivity issue between ADF Integration Runtime and the SQL Server. Usually caused by firewall rule expiry, VNet peering drop, or SQL Server restart.  
- Resolution: Check Azure SQL firewall rules. Confirm IR is running. Ping sql-sales-prod from IR host. Contact DBA team if SQL Server is down.  
- Rerun: Safe to rerun manually after fix. Watermark is only updated on success so no data duplication risk.

**Timeout on Copy Activity**  
- Root cause: Unusually large incremental batch. Can happen after weekends or public holidays when 3+ days of data accumulate.  
- Resolution: Increase copy activity timeout from 1h to 2h for next run. Consider adding batch size limiter.

### SLA Breach Definition
If pipeline does not reach Succeeded status by 03:00 AEST, it is considered an SLA breach. Escalate to data-engineering@company.com and notify sales-ops@company.com.

---

## PL_TransformCustomer360

**Owner:** Analytics Engineering  
**SLA:** High — must complete by 06:00 AEST daily  
**Schedule:** Every day at 04:00 AEST  
**Domain:** Customer  

### Description
Transforms and merges raw customer data from multiple source systems (CRM, ERP, e-commerce) into a unified Customer 360 gold layer. Runs Databricks notebook for data quality validation.

### Architecture
Bronze (multi-source) → Data Flow: Cleanse → Data Flow: Merge → Databricks Notebook (DQ validation) → Gold layer

### Common Failures & Resolutions

**Data Flow cluster startup timeout**  
- Root cause: Azure Databricks cluster cold start. First run of the day may take 5-8 minutes.  
- Resolution: Enable cluster warm-up job at 03:50 AEST or switch to job cluster with keep-alive.

**DQ Validation failure (Notebook)**  
- Root cause: DQ score falls below 95% threshold. Typically caused by upstream data quality issues in CRM export.  
- Resolution: Review Databricks run output for specific column failures. Notify CRM team.

**rowsDropped spike**  
- Normal threshold: <1% rows dropped during cleanse  
- Alert threshold: >5% rows dropped — investigate source data quality

---

## PL_LoadInventoryFull

**Owner:** Data Engineering  
**SLA:** High — must complete by 06:00 AEST every Monday  
**Schedule:** Every Sunday at 01:00 AEST (TumblingWindowTrigger)  
**Domain:** Inventory  
**Source:** SAP ECC via ODBC (SAP HANA)  

### Description
Full load of inventory master data and stock levels from SAP ECC. Runs weekly due to SAP extraction volume constraints.

### Architecture
SAP ECC (ODBC) → Copy: Material Master → Copy: Stock Levels → Azure SQL (inventory schema)

### Common Failures & Resolutions

**UserErrorOdbcOperationFailed / Network error**  
- Root cause: SAP HANA ODBC connection failure. Usually caused by SAP system maintenance window or network instability between IR and SAP host.  
- Resolution: Check SAP BASIS team maintenance schedule. Confirm ODBC DSN settings on IR host. Retry after SAP system is available.  
- Note: SAP team runs maintenance windows Sunday 00:00–01:30 AEST — pipeline start time conflict!

**Recommendation:** Shift pipeline trigger to 02:00 AEST on Sundays to avoid SAP maintenance window overlap.

---

## PL_IngestFinanceGL_Incremental

**Owner:** Finance Data Team  
**SLA:** Critical — must complete each hourly run within 10 minutes  
**Schedule:** Hourly during business hours 05:00–18:00 AEST  
**Domain:** Finance  

### Description
High-frequency incremental ingestion of General Ledger transactions from finance SQL Server. Supports near-real-time finance reporting.

### Architecture
Finance SQL Server → Lookup max posting date → Copy incremental batch → Azure Blob (silver/finance) → Update high-watermark

### Performance Benchmarks
- Normal batch size: 15,000–30,000 rows per hour  
- Normal duration: 3–6 minutes  
- Alert if duration > 10 minutes  
- Alert if rowsRead = 0 for 2+ consecutive runs (possible source issue)

---

## PL_PowerBI_RefreshDatasets

**Owner:** BI Team  
**SLA:** Medium — dashboards available by 07:00 AEST  
**Schedule:** Daily at 06:00 AEST  
**Domain:** Reporting  

### Description
Triggers Power BI dataset refreshes via REST API and polls until completion. Refreshes Sales Dashboard and Finance Dashboard datasets in the executive_dashboards workspace.

### Known Issues

**ActivityTimedOut on UNTIL_WaitForRefreshComplete**  
- Root cause: Power BI dataset refresh takes longer than the 60-minute Until loop timeout. Usually happens when upstream pipelines (Sales, Finance) run late and PBI refresh is processing a larger-than-normal dataset.  
- Resolution: Check if upstream pipelines (PL_IngestSalesData_Daily, PL_IngestFinanceGL_Incremental) ran late. If so, this is expected. Increase Until timeout to 90 minutes.  
- Note: SLA dependency — this pipeline is downstream of PL_IngestSalesData_Daily. If sales pipeline fails, PBI refresh will time out.

---

## PL_ArchiveRawData_Monthly

**Owner:** Data Engineering  
**SLA:** Low — complete within 24 hours of month start  
**Schedule:** 1st of every month at 00:00 AEST  
**Domain:** Platform  

### Description
Archives prior month's raw bronze layer files to cold storage archive container. Processes files in batches using ForEach activity.

### Notes
- Large volume expected: 4,000–6,000 files, 80–120 GB per month  
- Runtime typically 2.5–4 hours  
- No downstream dependencies; safe to run at any time
