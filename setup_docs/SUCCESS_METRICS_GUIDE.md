# Success Metrics Guide
## Azure Advisor Reports Platform - KPI Tracking & Reporting

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Owner:** Product Management Team
**Review Frequency:** Monthly

---

## Table of Contents

1. [Overview](#overview)
2. [Key Performance Indicators (KPIs)](#key-performance-indicators-kpis)
3. [Metric Definitions](#metric-definitions)
4. [Dashboard Setup](#dashboard-setup)
5. [Data Collection Methods](#data-collection-methods)
6. [Reporting Templates](#reporting-templates)
7. [Monthly Review Process](#monthly-review-process)
8. [Quarterly Business Review](#quarterly-business-review)
9. [Action Planning](#action-planning)

---

## Overview

### Purpose

This guide provides a comprehensive framework for tracking, measuring, and reporting on the success metrics defined in [SUCCESS_METRICS.md](SUCCESS_METRICS.md). It enables stakeholders to monitor platform performance, user adoption, business impact, and return on investment.

### Success Metrics Categories

**1. User Adoption Metrics**
- User growth and retention
- Organization onboarding
- Feature adoption rates

**2. Platform Usage Metrics**
- Report generation volume
- Client management activity
- Dashboard engagement

**3. Performance Metrics**
- Report generation time
- API response times
- System uptime

**4. Business Impact Metrics**
- Time savings achieved
- Cost savings identified
- Customer satisfaction

**5. Technical Quality Metrics**
- Error rates
- Bug resolution time
- Test coverage

---

## Key Performance Indicators (KPIs)

### North Star Metric

**Primary Success Indicator:**
- **Reports Generated per Month** - Demonstrates platform value and user engagement

**Target:** 1,000+ reports/month by Month 3

### Critical KPIs (Tier 1)

| KPI | Target | Measurement Frequency | Owner |
|-----|--------|----------------------|-------|
| **Active Organizations** | 50 by Month 3 | Weekly | Product Manager |
| **Reports Generated/Month** | 1,000 by Month 3 | Daily | Product Manager |
| **User Satisfaction (CSAT)** | >4.5/5.0 | Monthly | Support Lead |
| **System Uptime** | >99.5% | Real-time | DevOps Lead |
| **Report Generation Time** | <45 seconds avg | Real-time | Tech Lead |

### Important KPIs (Tier 2)

| KPI | Target | Measurement Frequency | Owner |
|-----|--------|----------------------|-------|
| **User Retention Rate** | >85% monthly | Monthly | Product Manager |
| **Feature Adoption Rate** | >60% | Monthly | Product Manager |
| **API Response Time (P95)** | <2 seconds | Real-time | Tech Lead |
| **Support Ticket Volume** | <20/week | Weekly | Support Lead |
| **Time Savings per Report** | >7 hours | Per report | Product Manager |

### Secondary KPIs (Tier 3)

| KPI | Target | Measurement Frequency | Owner |
|-----|--------|----------------------|-------|
| **Net Promoter Score (NPS)** | >30 | Quarterly | Product Manager |
| **Cost Savings Identified** | Track | Monthly | Product Manager |
| **Test Coverage** | >85% | Per release | QA Lead |
| **Critical Bugs** | 0 in production | Daily | Tech Lead |
| **Azure Cost** | <$900/month | Monthly | DevOps Lead |

---

## Metric Definitions

### 1. User Adoption Metrics

#### 1.1 Active Organizations
**Definition:** Number of organizations with at least one active user who logged in during the measurement period.

**Calculation:**
```sql
SELECT COUNT(DISTINCT organization_id)
FROM users
WHERE last_login >= DATE_TRUNC('month', CURRENT_DATE)
  AND is_active = TRUE;
```

**Data Source:** User database table
**Target:** 50 organizations by Month 3
**Reporting Frequency:** Weekly

**Interpretation:**
- <10 organizations: Early stage, focus on onboarding
- 10-30 organizations: Growth phase, iterate on feedback
- 30-50 organizations: Scaling phase, ensure stability
- 50+ organizations: Success milestone achieved

---

#### 1.2 Total Active Users
**Definition:** Number of individual users who logged in during the measurement period.

**Calculation:**
```sql
SELECT COUNT(DISTINCT user_id)
FROM users
WHERE last_login >= DATE_TRUNC('month', CURRENT_DATE)
  AND is_active = TRUE;
```

**Data Source:** User database table
**Target:** 100-150 users by Month 3 (assuming 2-3 users per org)
**Reporting Frequency:** Weekly

---

#### 1.3 User Growth Rate
**Definition:** Month-over-month percentage increase in active users.

**Calculation:**
```
User Growth Rate = ((Current Month Users - Previous Month Users) / Previous Month Users) × 100%
```

**Target:** 20-30% monthly growth in first 3 months
**Reporting Frequency:** Monthly

**Example:**
- Month 1: 20 users
- Month 2: 35 users
- Growth Rate: ((35-20)/20) × 100% = 75%

---

#### 1.4 User Retention Rate
**Definition:** Percentage of users from previous month who remain active in current month.

**Calculation:**
```sql
-- Users from previous month who logged in this month
WITH prev_month_users AS (
  SELECT DISTINCT user_id
  FROM users
  WHERE last_login >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
    AND last_login < DATE_TRUNC('month', CURRENT_DATE)
),
retained_users AS (
  SELECT DISTINCT u.user_id
  FROM users u
  INNER JOIN prev_month_users p ON u.user_id = p.user_id
  WHERE u.last_login >= DATE_TRUNC('month', CURRENT_DATE)
)
SELECT
  COUNT(DISTINCT r.user_id) * 100.0 / COUNT(DISTINCT p.user_id) AS retention_rate
FROM prev_month_users p
LEFT JOIN retained_users r ON p.user_id = r.user_id;
```

**Target:** >85% monthly retention
**Reporting Frequency:** Monthly

---

### 2. Platform Usage Metrics

#### 2.1 Reports Generated per Month
**Definition:** Total number of reports successfully generated during the month.

**Calculation:**
```sql
SELECT COUNT(*)
FROM reports
WHERE status = 'completed'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
  AND created_at < DATE_TRUNC('month', CURRENT_DATE + INTERVAL '1 month');
```

**Data Source:** Reports database table
**Target:** 1,000 reports/month by Month 3
**Reporting Frequency:** Daily (cumulative monthly)

**Breakdown by Report Type:**
```sql
SELECT report_type, COUNT(*) as count
FROM reports
WHERE status = 'completed'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY report_type
ORDER BY count DESC;
```

---

#### 2.2 Reports per User per Month
**Definition:** Average number of reports generated per active user.

**Calculation:**
```
Reports per User = Total Reports Generated / Total Active Users
```

**Target:** 5-10 reports per user per month
**Reporting Frequency:** Monthly

**Interpretation:**
- <3 reports/user: Low engagement, improve onboarding
- 3-5 reports/user: Average engagement
- 5-10 reports/user: Good engagement
- >10 reports/user: Power users, gather feedback

---

#### 2.3 Client Management Activity
**Definition:** Number of new clients created during the period.

**Calculation:**
```sql
SELECT COUNT(*)
FROM clients
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE);
```

**Target:** 100-200 clients/month by Month 3
**Reporting Frequency:** Weekly

---

#### 2.4 Feature Adoption Rate
**Definition:** Percentage of users who have used specific features.

**Key Features to Track:**
- Dashboard Analytics (target: >80% of users)
- Report Download (target: >90% of users)
- Client Management (target: >70% of users)
- Multiple Report Types (target: >60% of users)

**Calculation Example (Dashboard):**
```sql
WITH dashboard_users AS (
  SELECT DISTINCT user_id
  FROM analytics_access_logs
  WHERE accessed_at >= DATE_TRUNC('month', CURRENT_DATE)
),
active_users AS (
  SELECT DISTINCT user_id
  FROM users
  WHERE last_login >= DATE_TRUNC('month', CURRENT_DATE)
)
SELECT
  COUNT(DISTINCT d.user_id) * 100.0 / COUNT(DISTINCT a.user_id) AS adoption_rate
FROM active_users a
LEFT JOIN dashboard_users d ON a.user_id = d.user_id;
```

**Reporting Frequency:** Monthly

---

### 3. Performance Metrics

#### 3.1 Average Report Generation Time
**Definition:** Average time from CSV upload to report completion.

**Calculation:**
```sql
SELECT AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) AS avg_seconds
FROM reports
WHERE status = 'completed'
  AND created_at >= DATE_TRUNC('day', CURRENT_DATE);
```

**Data Source:** Reports table, Application Insights
**Target:** <45 seconds average
**Reporting Frequency:** Real-time monitoring, daily summary

**Percentile Analysis:**
```sql
SELECT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration) AS p50_seconds,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY duration) AS p75_seconds,
  PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration) AS p95_seconds,
  PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration) AS p99_seconds
FROM (
  SELECT EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at)) AS duration
  FROM reports
  WHERE status = 'completed'
    AND created_at >= DATE_TRUNC('day', CURRENT_DATE)
) AS report_durations;
```

---

#### 3.2 API Response Time
**Definition:** Time for API endpoints to respond to requests.

**Data Source:** Application Insights

**Application Insights Query:**
```kusto
requests
| where timestamp >= ago(24h)
| summarize
    avg_duration = avg(duration),
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    p99 = percentile(duration, 99)
    by name
| order by avg_duration desc
```

**Target:** P95 <2 seconds
**Reporting Frequency:** Real-time monitoring, daily summary

---

#### 3.3 System Uptime
**Definition:** Percentage of time the platform is available and functional.

**Calculation:**
```
Uptime % = (Total Time - Downtime) / Total Time × 100%
```

**Data Source:** Application Insights Availability Tests
**Target:** >99.5% monthly
**Reporting Frequency:** Real-time monitoring, monthly summary

**Downtime Tracking:**
- Track all incidents >5 minutes
- Categorize by severity (critical, high, medium, low)
- Document root cause and resolution

---

#### 3.4 Error Rate
**Definition:** Percentage of requests resulting in errors.

**Calculation:**
```kusto
requests
| where timestamp >= ago(24h)
| summarize
    total = count(),
    errors = countif(resultCode >= 400)
| extend error_rate = (errors * 100.0) / total
```

**Target:** <1% error rate
**Reporting Frequency:** Real-time monitoring, daily summary

---

### 4. Business Impact Metrics

#### 4.1 Time Savings per Report
**Definition:** Time saved compared to manual report generation.

**Calculation:**
```
Time Savings = Manual Time - Automated Time
```

**Assumptions:**
- Manual report generation: 8 hours
- Automated report generation: 45 minutes (0.75 hours)
- Time savings: 7.25 hours per report

**Monthly Time Savings:**
```
Monthly Time Savings = Total Reports Generated × 7.25 hours
```

**Example:**
- 100 reports/month × 7.25 hours = 725 hours saved/month
- Equivalent to ~18 full-time work weeks

**Reporting Frequency:** Monthly

---

#### 4.2 Cost Savings Identified
**Definition:** Total potential Azure cost savings identified in generated reports.

**Calculation:**
```sql
SELECT SUM(potential_savings) AS total_potential_savings
FROM recommendations
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE)
  AND category = 'cost';
```

**Data Source:** Recommendations table
**Target:** Track trend (varies by customer Azure spend)
**Reporting Frequency:** Monthly

**Note:** This is *potential* savings identified, not necessarily realized. Track customer feedback on actual savings achieved.

---

#### 4.3 Customer Satisfaction (CSAT)
**Definition:** Average satisfaction rating from users.

**Measurement Method:**
- In-app survey after report generation
- Monthly email survey
- Support ticket resolution survey

**Survey Question:**
"How satisfied are you with Azure Advisor Reports Platform?"
- 1 = Very Dissatisfied
- 2 = Dissatisfied
- 3 = Neutral
- 4 = Satisfied
- 5 = Very Satisfied

**Calculation:**
```
CSAT Score = Average of all ratings
```

**Target:** >4.5/5.0
**Reporting Frequency:** Monthly (minimum 30 responses)

---

#### 4.4 Net Promoter Score (NPS)
**Definition:** Likelihood of users to recommend the platform.

**Survey Question:**
"On a scale of 0-10, how likely are you to recommend Azure Advisor Reports Platform to a colleague?"

**Calculation:**
```
NPS = % Promoters (9-10) - % Detractors (0-6)
```

**Categories:**
- Promoters: 9-10
- Passives: 7-8
- Detractors: 0-6

**Target:** >30 (Good), >50 (Excellent)
**Reporting Frequency:** Quarterly

---

### 5. Technical Quality Metrics

#### 5.1 Test Coverage
**Definition:** Percentage of code covered by automated tests.

**Calculation:**
```bash
# Backend (pytest)
pytest --cov=apps --cov-report=term

# Frontend (Jest)
npm test -- --coverage
```

**Current Status:**
- Backend: 52% (target: 85%)
- Frontend: 75% (target: 80%)

**Target:** >85% backend, >80% frontend
**Reporting Frequency:** Per release

---

#### 5.2 Bug Count by Severity
**Definition:** Number of open bugs categorized by severity.

**Severity Levels:**
- **Critical:** System down, data loss, security vulnerability
- **High:** Major feature broken, significant user impact
- **Medium:** Feature partially broken, workaround available
- **Low:** Minor issue, cosmetic, low impact

**Target:**
- Critical bugs in production: 0
- High-priority bugs: <5
- Total open bugs: <20

**Reporting Frequency:** Weekly

---

#### 5.3 Mean Time to Resolution (MTTR)
**Definition:** Average time to resolve bugs/issues.

**Calculation:**
```
MTTR = Sum of (Resolution Time - Report Time) / Number of Resolved Issues
```

**Target:**
- Critical: <4 hours
- High: <24 hours
- Medium: <7 days
- Low: <30 days

**Reporting Frequency:** Weekly

---

## Dashboard Setup

### Application Insights Dashboard

**Create Custom Dashboard:**

1. **Navigate to Application Insights**
   - Go to Azure Portal → Application Insights → your instance

2. **Create New Dashboard**
   - Click "Dashboard" → "New dashboard"
   - Name: "Azure Advisor Reports - Success Metrics"

3. **Add Tiles for Key Metrics**

**Tile 1: Active Users (Last 30 Days)**
```kusto
customEvents
| where name == "user_login"
| where timestamp >= ago(30d)
| summarize dcount(tostring(customDimensions.user_id))
| render timechart
```

**Tile 2: Reports Generated (Daily)**
```kusto
customEvents
| where name == "report_generated"
| where timestamp >= ago(30d)
| summarize count() by bin(timestamp, 1d)
| render timechart
```

**Tile 3: Average Report Generation Time**
```kusto
customMetrics
| where name == "report_generation_time"
| where timestamp >= ago(7d)
| summarize avg(value) by bin(timestamp, 1h)
| render timechart
```

**Tile 4: API Response Time (P95)**
```kusto
requests
| where timestamp >= ago(7d)
| summarize percentile(duration, 95) by bin(timestamp, 1h)
| render timechart
```

**Tile 5: Error Rate**
```kusto
requests
| where timestamp >= ago(24h)
| summarize
    total = count(),
    errors = countif(resultCode >= 400)
| extend error_rate = (errors * 100.0) / total
| project error_rate
```

**Tile 6: System Availability**
```kusto
availabilityResults
| where timestamp >= ago(30d)
| summarize availability = avg(success) * 100
| project availability
```

4. **Pin Dashboard**
   - Click "Pin to dashboard"
   - Select your custom dashboard
   - Arrange tiles for optimal viewing

5. **Set Auto-Refresh**
   - Configure dashboard to auto-refresh every 5 minutes
   - Enable email alerts for critical metrics

---

### Database Metrics Dashboard (SQL Queries)

**Create a monitoring script to run daily:**

```sql
-- File: scripts/daily_metrics.sql

-- 1. Active Users (Last 30 Days)
SELECT COUNT(DISTINCT user_id) AS active_users_30d
FROM users
WHERE last_login >= CURRENT_DATE - INTERVAL '30 days';

-- 2. Active Organizations
SELECT COUNT(DISTINCT organization_id) AS active_organizations
FROM users
WHERE last_login >= CURRENT_DATE - INTERVAL '30 days'
  AND is_active = TRUE;

-- 3. Reports Generated (This Month)
SELECT
  report_type,
  COUNT(*) AS count
FROM reports
WHERE status = 'completed'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY report_type
ORDER BY count DESC;

-- 4. Total Reports (This Month)
SELECT COUNT(*) AS total_reports_this_month
FROM reports
WHERE status = 'completed'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE);

-- 5. Average Report Generation Time (Last 7 Days)
SELECT
  AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) AS avg_seconds
FROM reports
WHERE status = 'completed'
  AND created_at >= CURRENT_DATE - INTERVAL '7 days';

-- 6. Client Management Activity (This Month)
SELECT COUNT(*) AS new_clients_this_month
FROM clients
WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE);

-- 7. Total Cost Savings Identified (This Month)
SELECT
  SUM(potential_savings) AS total_potential_savings,
  COUNT(*) AS cost_recommendations
FROM recommendations
WHERE category = 'cost'
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE);

-- 8. User Retention Rate (Month over Month)
WITH prev_month_users AS (
  SELECT DISTINCT user_id
  FROM users
  WHERE last_login >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
    AND last_login < DATE_TRUNC('month', CURRENT_DATE)
),
retained_users AS (
  SELECT DISTINCT u.user_id
  FROM users u
  INNER JOIN prev_month_users p ON u.user_id = p.user_id
  WHERE u.last_login >= DATE_TRUNC('month', CURRENT_DATE)
)
SELECT
  COUNT(DISTINCT r.user_id) * 100.0 / NULLIF(COUNT(DISTINCT p.user_id), 0) AS retention_rate
FROM prev_month_users p
LEFT JOIN retained_users r ON p.user_id = r.user_id;
```

**Automate Execution:**
```powershell
# Script: run_daily_metrics.ps1
$date = Get-Date -Format "yyyy-MM-dd"
$output_file = "metrics_$date.csv"

psql -h <server> -U <user> -d <database> -f daily_metrics.sql -o $output_file --csv

# Email results to team
Send-MailMessage -To "team@yourcompany.com" -From "metrics@yourcompany.com" `
  -Subject "Daily Success Metrics - $date" `
  -Body "Daily metrics attached" `
  -Attachments $output_file `
  -SmtpServer "smtp.yourcompany.com"
```

---

## Data Collection Methods

### 1. Automatic Data Collection

**Application Insights (Automatic):**
- API request/response times
- Error rates and exceptions
- User sessions
- Custom events (login, report generation, etc.)
- System performance (CPU, memory)

**Database (Automatic):**
- All user actions logged with timestamps
- Report generation metadata
- Client management operations

**Configuration:**
Already configured in application code via:
- `ApplicationInsights` SDK (backend)
- `@microsoft/applicationinsights-web` (frontend)

---

### 2. Manual Data Collection

**User Surveys:**

**Post-Report Generation Survey (CSAT):**
- Trigger: After successful report download
- Frequency: 20% of reports (randomly sampled)
- Questions:
  1. How satisfied are you with this report? (1-5)
  2. What would make it better? (optional text)

**Monthly User Survey (NPS):**
- Trigger: Email sent on 1st of each month
- Frequency: Monthly to all active users
- Questions:
  1. How likely are you to recommend this platform? (0-10)
  2. What's the primary reason for your score? (text)
  3. What features would you like to see? (text)

**Implementation:**
- Use Microsoft Forms or Typeform
- Track response rate (target: >30%)
- Store responses in database for analysis

---

### 3. Azure Cost Tracking

**Monitor Azure Spending:**
```powershell
# Get current month costs
az consumption usage list `
  --start-date (Get-Date -Day 1 -Format "yyyy-MM-dd") `
  --end-date (Get-Date -Format "yyyy-MM-dd") `
  --query "[].{Date:usageStart, Cost:pretaxCost}" `
  --output table

# Set up budget alert
az consumption budget create `
  --resource-group rg-azure-advisor-reports-prod `
  --budget-name monthly-budget `
  --amount 900 `
  --time-grain Monthly `
  --start-date (Get-Date -Format "yyyy-MM-01") `
  --end-date (Get-Date -Format "yyyy-12-31")
```

---

## Reporting Templates

### Weekly Status Report Template

**Subject:** Azure Advisor Reports - Weekly Status (Week of [Date])

**To:** Product Team, Leadership

**Key Metrics (Week of [Date]):**

| Metric | This Week | Last Week | Change | Target | Status |
|--------|-----------|-----------|--------|--------|--------|
| Active Organizations | ___ | ___ | ___% | 50 | ☐ On Track ☐ At Risk |
| Active Users | ___ | ___ | ___% | 100 | ☐ On Track ☐ At Risk |
| Reports Generated | ___ | ___ | ___% | 250/week | ☐ On Track ☐ At Risk |
| Avg Report Gen Time | ___s | ___s | ___s | <45s | ☐ On Track ☐ At Risk |
| System Uptime | ___% | ___% | ___% | >99.5% | ☐ On Track ☐ At Risk |
| Critical Bugs | ___ | ___ | ___ | 0 | ☐ On Track ☐ At Risk |

**Highlights:**
- [Key achievement or milestone this week]
- [User feedback or testimonial]
- [Feature improvement or launch]

**Challenges:**
- [Issue or blocker]
- [Action plan to resolve]

**Next Week Focus:**
- [Priority 1]
- [Priority 2]
- [Priority 3]

---

### Monthly Performance Report Template

**Subject:** Azure Advisor Reports - Monthly Performance Report ([Month] [Year])

**Executive Summary:**
[2-3 sentence summary of month's performance, highlighting key wins and challenges]

**1. User Adoption**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Active Organizations | ___ | ___ | ☐ Met ☐ Missed |
| Active Users | ___ | ___ | ☐ Met ☐ Missed |
| New Organizations | ___ | ___ | ☐ Met ☐ Missed |
| User Retention Rate | >85% | ___% | ☐ Met ☐ Missed |

**Trend Analysis:**
[Include chart showing user growth over past 3-6 months]

**2. Platform Usage**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Reports Generated | 1,000 | ___ | ☐ Met ☐ Missed |
| Reports per User | 5-10 | ___ | ☐ Met ☐ Missed |
| New Clients Created | 100-200 | ___ | ☐ Met ☐ Missed |
| Dashboard Adoption | >80% | ___% | ☐ Met ☐ Missed |

**Report Type Breakdown:**
- Detailed Report: ___% (___ reports)
- Executive Summary: ___% (___ reports)
- Cost Optimization: ___% (___ reports)
- Security Assessment: ___% (___ reports)
- Operational Excellence: ___% (___ reports)

**3. Performance**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Avg Report Gen Time | <45s | ___s | ☐ Met ☐ Missed |
| API Response Time (P95) | <2s | ___s | ☐ Met ☐ Missed |
| System Uptime | >99.5% | ___% | ☐ Met ☐ Missed |
| Error Rate | <1% | ___% | ☐ Met ☐ Missed |

**Incidents:**
- Total incidents: ___
- Critical incidents: ___ (downtime: ___ minutes)
- Resolution: [Brief description of major incidents and resolutions]

**4. Business Impact**

| Metric | This Month | Cumulative |
|--------|------------|------------|
| Time Saved (hours) | ___ | ___ |
| Cost Savings Identified ($) | ___ | ___ |
| Customer Satisfaction (CSAT) | ___/5.0 | ___/5.0 |

**5. Technical Quality**

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Test Coverage (Backend) | >85% | ___% | ☐ Met ☐ Missed |
| Test Coverage (Frontend) | >80% | ___% | ☐ Met ☐ Missed |
| Critical Bugs | 0 | ___ | ☐ Met ☐ Missed |
| Open High-Priority Bugs | <5 | ___ | ☐ Met ☐ Missed |

**6. Financial**

| Metric | Budget | Actual | Status |
|--------|--------|--------|--------|
| Azure Infrastructure | $900 | $___ | ☐ Under ☐ Over |
| Support Costs | $___ | $___ | ☐ Under ☐ Over |

**7. Key Wins**
- [Win 1]
- [Win 2]
- [Win 3]

**8. Challenges & Action Plans**
- [Challenge 1] → [Action plan]
- [Challenge 2] → [Action plan]

**9. Next Month Focus**
- [Priority 1]
- [Priority 2]
- [Priority 3]

**Prepared by:** [Name]
**Date:** [Date]

---

## Monthly Review Process

### Monthly Review Meeting Agenda

**Frequency:** First week of each month
**Duration:** 60 minutes
**Attendees:** Product Manager, Tech Lead, DevOps Lead, Support Lead, Key Stakeholders

**Agenda:**

**1. Metrics Review (20 minutes)**
- Review monthly report (sent 24 hours in advance)
- Discuss trends (positive and negative)
- Compare against targets and previous months

**2. User Feedback Discussion (15 minutes)**
- Review CSAT and NPS scores
- Discuss common themes from surveys and support tickets
- Highlight positive testimonials
- Address concerns and complaints

**3. Technical Performance (10 minutes)**
- System uptime and incidents
- Performance trends
- Bug status and quality metrics
- Infrastructure costs

**4. Action Planning (10 minutes)**
- Review action items from previous month (status update)
- Identify new action items for current month
- Assign owners and due dates

**5. Next Month Priorities (5 minutes)**
- Confirm priorities for next month
- Discuss any upcoming features or changes
- Set goals for next review

**Meeting Output:**
- [ ] Meeting minutes documented
- [ ] Action items assigned with owners and due dates
- [ ] Next month priorities confirmed
- [ ] Monthly report approved and distributed to stakeholders

---

## Quarterly Business Review

### Quarterly Business Review (QBR) Template

**Frequency:** Quarterly (Q1, Q2, Q3, Q4)
**Duration:** 90 minutes
**Attendees:** Executive team, Product team, All leads, Key customers (optional)

**Presentation Outline:**

**Slide 1: Executive Summary**
- Quarter highlights (3-4 bullets)
- Key achievements
- Performance vs. targets
- Quarter-over-quarter growth

**Slide 2-3: User Adoption & Growth**
- Organization growth trend (chart)
- User growth trend (chart)
- Retention analysis
- User segmentation (by role, industry, usage)

**Slide 4-5: Platform Usage**
- Reports generated trend (chart)
- Report type distribution
- Feature adoption analysis
- Usage patterns and insights

**Slide 6: Performance & Reliability**
- Uptime summary
- Performance trends
- Incident summary and learnings
- Infrastructure scalability

**Slide 7: Business Impact**
- Total time saved (cumulative)
- Total cost savings identified (cumulative)
- Customer satisfaction trends
- ROI calculations

**Slide 8: Customer Voice**
- NPS score and trend
- Top positive feedback themes
- Top improvement requests
- Customer testimonials (2-3 quotes)

**Slide 9: Technical Quality**
- Test coverage progress
- Bug metrics and trends
- Code quality improvements
- Technical debt status

**Slide 10: Financial Performance**
- Azure costs vs. budget
- Cost per report trend
- Cost optimization initiatives
- Revenue (if applicable)

**Slide 11: Roadmap & Future Plans**
- Completed features (this quarter)
- In-progress features
- Next quarter priorities
- Long-term vision (6-12 months)

**Slide 12: Risks & Challenges**
- Current challenges
- Mitigation plans
- Resource needs
- Dependencies

**Slide 13: Q&A and Discussion**
- Open discussion
- Feedback from stakeholders
- Decisions required

**QBR Output:**
- [ ] Presentation delivered and recorded
- [ ] Feedback collected from stakeholders
- [ ] Roadmap adjustments (if any)
- [ ] Action items for next quarter
- [ ] QBR summary distributed

---

## Action Planning

### Action Item Template

**Issue/Opportunity:** [Description]

**Current State:** [Where are we now?]

**Desired State:** [Where do we want to be?]

**Owner:** [Name]

**Priority:** ☐ Critical ☐ High ☐ Medium ☐ Low

**Due Date:** [Date]

**Success Criteria:** [How will we know it's done?]

**Action Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Status:** ☐ Not Started ☐ In Progress ☐ Blocked ☐ Complete

**Blockers:** [If any]

**Updates:**
- [Date]: [Update]
- [Date]: [Update]

---

### Sample Action Plan (Example)

**Issue:** User retention rate is 78% (below target of 85%)

**Current State:**
- Retention rate: 78%
- Top churn reason: "Platform too complex for occasional users"

**Desired State:**
- Retention rate: 85%+
- Improved onboarding experience

**Owner:** Product Manager

**Priority:** High

**Due Date:** 30 days

**Success Criteria:**
- Retention rate increases to 85%+ within 60 days of implementation
- User feedback indicates improved onboarding

**Action Steps:**
1. Create interactive product tour for new users
2. Add contextual help tooltips throughout platform
3. Create "Getting Started" checklist on dashboard
4. Send automated onboarding emails (day 1, 3, 7, 14)
5. Measure impact on retention after 30 days

**Status:** In Progress

**Updates:**
- Oct 10: Product tour design complete
- Oct 15: Development 50% complete
- Oct 20: Testing in progress

---

## Appendix: Quick Reference

### Key Metric Targets Summary

| Metric | Month 1 | Month 2 | Month 3 | Ongoing |
|--------|---------|---------|---------|---------|
| Active Organizations | 15 | 30 | 50 | Growth |
| Reports/Month | 250 | 500 | 1,000 | Growth |
| CSAT Score | >4.0 | >4.3 | >4.5 | >4.5 |
| System Uptime | >99% | >99.5% | >99.5% | >99.5% |
| Report Gen Time | <60s | <50s | <45s | <45s |
| User Retention | >80% | >82% | >85% | >85% |

### Data Sources Quick Reference

| Metric | Data Source | Access Method |
|--------|-------------|---------------|
| User Activity | Application Insights | Azure Portal → App Insights → Logs |
| Reports Generated | PostgreSQL Database | SQL Query (see Metric Definitions) |
| Performance Metrics | Application Insights | Azure Portal → App Insights → Metrics |
| System Uptime | Application Insights | Availability tests |
| User Satisfaction | Surveys | Microsoft Forms/Typeform |
| Azure Costs | Azure Cost Management | Azure Portal → Cost Management |

### Contact Information

**Metric Owners:**
- **Product Manager:** [Name], [email] - User adoption, business impact
- **Tech Lead:** [Name], [email] - Performance, technical quality
- **DevOps Lead:** [Name], [email] - Uptime, infrastructure costs
- **Support Lead:** [Name], [email] - Customer satisfaction, support metrics

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-06 | Product Team | Initial success metrics guide |

---

**Related Documents:**
- [SUCCESS_METRICS.md](SUCCESS_METRICS.md) - High-level success metrics definition
- [DASHBOARD_USER_GUIDE.md](DASHBOARD_USER_GUIDE.md) - Platform dashboard usage
- [FINAL_PROJECT_STATUS_REPORT.md](FINAL_PROJECT_STATUS_REPORT.md) - Project status
- [MONITORING_SETUP.md](MONITORING_SETUP.md) - Technical monitoring setup

---

**End of Success Metrics Guide**
