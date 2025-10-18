# Quick Start Guide
**Azure Advisor Reports Platform - Get Started in 5 Minutes**

Version 1.0 | Last Updated: October 5, 2025

---

## Your First Report in 5 Minutes

This quick start guide will help you generate your first Azure Advisor report in just 5 minutes. Perfect for new users who want to get started immediately.

---

## Before You Begin

You'll need:
- [ ] **Azure Active Directory account** (your work/organization Microsoft account)
- [ ] **Azure Advisor CSV file** (exported from Azure Portal)
- [ ] **Web browser** (Chrome, Edge, Firefox, or Safari)
- [ ] **5 minutes** of your time

---

## Step 1: Login (30 seconds)

### What to Do:
1. Navigate to the platform URL: `https://your-platform-url.azurewebsites.net`
2. Click the **"Sign in with Microsoft"** button
3. Enter your work email and password
4. Approve the permission request (first-time only)

### What You'll See:
```
┌─────────────────────────────────────┐
│  Azure Advisor Reports Platform     │
│                                     │
│  [  Sign in with Microsoft  ]       │
│                                     │
│  Trusted by cloud teams worldwide  │
└─────────────────────────────────────┘
```

**Common Issue:** If you see "Account not found":
- Make sure you're using your **work** Microsoft account (not personal)
- Contact your administrator to grant access

---

## Step 2: Get Your Azure Advisor CSV (2 minutes)

### If You Don't Have the CSV Yet:

1. **Open Azure Portal** (portal.azure.com)
2. **Search for "Advisor"** in the top search bar
3. Click **"Advisor" service**
4. Click **"Recommendations"** in the left menu
5. Click **"Download as CSV"** button at the top
6. **Save the file** to your Downloads folder

### File Name Should Look Like:
```
advisor-recommendations-2025-10-05.csv
advisor_export_20251005.csv
AzureAdvisorRecommendations.csv
```

**File Size:** Typically 100KB - 5MB (larger subscriptions may be bigger)

---

## Step 3: Create a Client (30 seconds)

### What to Do:
1. Click **"Clients"** in the sidebar (left menu)
2. Click the blue **"+ Add Client"** button (top right)
3. **Fill in the form:**
   - **Company Name:** Enter client's name (e.g., "Contoso Corp")
   - **Industry:** Select from dropdown (e.g., "Technology")
   - **Contact Email:** Enter email (e.g., "admin@contoso.com")
   - **Azure Subscription IDs:** (Optional - you can skip this)
4. Click **"Save Client"**

### Form Fields:
```
┌────────────────────────────────────┐
│ Company Name *                     │
│ [Contoso Corporation        ]      │
│                                    │
│ Industry *                         │
│ [Technology          ▼]            │
│                                    │
│ Contact Email *                    │
│ [admin@contoso.com          ]      │
│                                    │
│ [Cancel]           [Save Client]   │
└────────────────────────────────────┘
```

**Success:** You'll see a green notification: "Client created successfully!"

---

## Step 4: Upload Your CSV (1 minute)

### What to Do:
1. Click **"Reports"** in the sidebar
2. Click the blue **"+ Generate Report"** button
3. **Step 1 - Select Client:**
   - Choose the client you just created from the dropdown
   - Click **"Next"**

4. **Step 2 - Upload CSV:**
   - **Drag and drop** your CSV file into the upload zone, OR
   - Click **"Browse"** to select the file from your computer
   - Wait for the green checkmark ✅
   - Click **"Next"**

### Upload Zone:
```
┌─────────────────────────────────────┐
│    Drop CSV file here               │
│           OR                        │
│    [  Browse Files  ]               │
│                                     │
│  Supported: .csv files up to 50MB  │
└─────────────────────────────────────┘
```

**Common Issues:**
- **"File type not supported"** → Make sure it's a .csv file (not .xlsx or .txt)
- **"File too large"** → File must be under 50MB

---

## Step 5: Select Report Type (30 seconds)

### Choose the Right Report:

**For Your First Report, Choose:**
- **Executive Summary** - Best for getting a quick overview (recommended)

### All Report Types:

| Report Type | Best For | Pages | Time |
|------------|----------|-------|------|
| **Executive Summary** ⭐ | Leadership, first-time users | 5-8 | Fast |
| **Detailed Report** | Technical teams, deep analysis | 20-50 | Slower |
| **Cost Optimization** | Finance, savings focus | 12-20 | Medium |
| **Security Assessment** | Security teams, compliance | 10-18 | Medium |
| **Operational Excellence** | DevOps, reliability | 15-25 | Medium |

### What to Do:
1. Click on the **"Executive Summary"** card
2. Click the green **"Generate Report"** button
3. Wait for processing (30-45 seconds)

---

## Step 6: Download Your Report (30 seconds)

### What You'll See:
```
Report Status: Processing... ⏳

(After 30-45 seconds)

Report Status: Completed ✅
```

### Download Options:
1. Click the **"Download HTML"** button for web viewing, OR
2. Click the **"Download PDF"** button for printing/sharing

### Your Report Includes:
✅ **Executive Summary** - High-level overview
✅ **Key Metrics Dashboard** - Visual charts and graphs
✅ **Top Recommendations** - Prioritized actions
✅ **Cost Savings Estimate** - Potential monthly savings
✅ **Azure Advisor Score** - Overall health rating
✅ **Professional Formatting** - Ready to share with stakeholders

---

## Congratulations! 🎉

You've successfully generated your first Azure Advisor report!

### Next Steps:

**Explore More Features:**
- [ ] **View Dashboard** - See analytics across all your clients
- [ ] **Generate Other Report Types** - Try Detailed or Cost Optimization reports
- [ ] **Add More Clients** - Scale to manage multiple customers
- [ ] **Schedule Regular Reports** - Upload CSVs monthly for trend analysis
- [ ] **Share Reports** - Email HTML/PDF reports to stakeholders

**Learn More:**
- 📖 [User Manual](USER_MANUAL.md) - Complete feature guide (45 pages)
- 🔧 [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
- ❓ [FAQ](FAQ.md) - Frequently asked questions
- 🎥 [Video Tutorials](VIDEO_SCRIPTS.md) - Watch step-by-step videos

---

## Common First-Time Issues

### Problem: "Cannot sign in"
**Solution:**
- Use your **work Microsoft account** (not personal)
- Make sure your organization has granted access
- Try clearing browser cookies and cache
- Contact your IT administrator if issues persist

### Problem: "CSV upload failed"
**Solution:**
- Verify file is **.csv format** (not .xlsx or .txt)
- Check file size is **under 50MB**
- Make sure CSV is from **Azure Advisor** (not other Azure exports)
- Try re-downloading from Azure Portal

### Problem: "Report generation taking too long"
**Solution:**
- **Normal time:** 30-45 seconds for small CSVs (<500 recommendations)
- **Longer time:** 1-2 minutes for large CSVs (1000+ recommendations)
- **If stuck over 5 minutes:** Refresh the page and check "Reports" list
- The report will complete in the background

### Problem: "Downloaded report is blank"
**Solution:**
- Try a different browser (Chrome or Edge recommended)
- Disable browser ad-blockers temporarily
- Check CSV had valid recommendations (not an empty export)
- Try generating a different report type

---

## Quick Reference Card

### Essential Actions:

| Action | Location | Button/Link |
|--------|----------|-------------|
| **Login** | Homepage | "Sign in with Microsoft" |
| **Add Client** | Clients page | "+ Add Client" (top right) |
| **Generate Report** | Reports page | "+ Generate Report" (top right) |
| **View Dashboard** | Sidebar | "Dashboard" (first item) |
| **Download Report** | Report card | "Download HTML" or "Download PDF" |
| **Get Help** | Any page | "?" icon (top right) |

### Keyboard Shortcuts:

| Shortcut | Action |
|----------|--------|
| `Ctrl + /` | Open command palette |
| `Ctrl + N` | New client |
| `Ctrl + R` | New report |
| `Ctrl + D` | Go to dashboard |
| `Esc` | Close modal/dialog |

---

## Support

**Need Help?**
- 📧 Email: support@yourcompany.com
- 📖 Documentation: [Full User Manual](USER_MANUAL.md)
- 💬 Chat: Click chat icon (bottom right)
- 🎥 Videos: [Tutorial Library](VIDEO_SCRIPTS.md)

**Report a Bug:**
- Use the "Report Issue" button in the help menu
- Include screenshot and error message
- Expected response: 1 business day

---

## Tips for Success

### 💡 Pro Tips:

1. **Export CSVs Regularly**
   Monthly exports help you track improvement trends over time

2. **Start with Executive Summary**
   Get the high-level view first, then dive into Detailed Reports

3. **Use Client Notes**
   Add notes to each client about their specific Azure setup

4. **Download Both Formats**
   - HTML for interactive viewing and web sharing
   - PDF for email and printing

5. **Check Dashboard Weekly**
   Monitor metrics to track your optimization progress

### ⚠️ Common Pitfalls to Avoid:

❌ **Don't** upload Excel files - must be CSV
❌ **Don't** use personal Microsoft accounts - need work accounts
❌ **Don't** upload CSVs from other Azure services - must be Advisor
❌ **Don't** close browser during generation - wait for completion
❌ **Don't** share reports publicly - they may contain sensitive data

---

## What's Next?

### Recommended Learning Path:

**Week 1: Master the Basics**
1. Generate 2-3 reports for different clients
2. Explore the dashboard analytics
3. Try different report types

**Week 2: Optimize Your Workflow**
1. Set up regular CSV export schedule
2. Create templates for common client types
3. Learn keyboard shortcuts

**Week 3: Advanced Features**
1. Use the API for automation (see [API Documentation](API_DOCUMENTATION.md))
2. Set up webhooks for notifications
3. Integrate with your existing tools

**Week 4: Become a Power User**
1. Analyze trends across multiple months
2. Create custom presentations using report data
3. Train your team members

---

## Quick Start Checklist

**I have successfully:**
- [x] Logged in with my work Microsoft account
- [x] Exported a CSV from Azure Advisor
- [x] Created my first client
- [x] Uploaded a CSV file
- [x] Selected a report type
- [x] Generated and downloaded a report
- [ ] Explored the dashboard
- [ ] Read the full user manual
- [ ] Bookmarked the documentation

**Time to complete:** ~5 minutes ✅

---

**Version:** 1.0
**Last Updated:** October 5, 2025
**Feedback:** help@yourcompany.com

---

*This quick start guide is part of the Azure Advisor Reports Platform documentation suite. For comprehensive information, see the [Full Documentation Index](DOCUMENTATION_INDEX.md).*
