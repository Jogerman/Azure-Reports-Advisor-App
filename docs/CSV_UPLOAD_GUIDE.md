# CSV Upload Guide
## Azure Advisor Reports Platform

**Document Type:** User Guide - Core Feature
**Last Updated:** September 29, 2025
**Version:** 1.0
**Audience:** All users (primary focus on regular users)

---

## 📋 Overview

The CSV upload feature is the foundation of report generation in the Azure Advisor Reports Platform. This guide covers everything you need to know about preparing, uploading, and troubleshooting Azure Advisor CSV files.

**Time to Read:** 8 minutes
**Time to Complete First Upload:** 5 minutes

---

## 🎯 What You'll Learn

- How to export Azure Advisor data correctly
- CSV file requirements and formatting
- Step-by-step upload process
- How to verify successful uploads
- Common issues and solutions
- Best practices for ongoing success

---

## 📤 Step 1: Exporting Azure Advisor Data

Before you can upload a CSV file, you need to export it from Azure Advisor. Here are three methods:

### Method A: Azure Portal (Recommended for Beginners)

1. **Navigate to Azure Advisor**
   - Go to [portal.azure.com](https://portal.azure.com)
   - Sign in with your Azure account
   - Search for "Advisor" in the top search bar
   - Select "Azure Advisor" from the results

2. **Select Your Scope**
   - Choose the subscription(s) you want to analyze
   - Use the subscription filter at the top if managing multiple subscriptions
   - For first-time users, start with one subscription

3. **Export the Data**
   - Click the **"Download as CSV"** button in the toolbar
   - The file will download to your default download folder
   - Note the filename (usually includes date and subscription info)

**💡 Pro Tip:** Export data at the beginning of each month for consistent reporting cycles.

### Method B: PowerShell (For Power Users)

```powershell
# Connect to your Azure account
Connect-AzAccount

# Set the subscription context (replace with your subscription ID)
Set-AzContext -SubscriptionId "your-subscription-id"

# Get all advisor recommendations
$recommendations = Get-AzAdvisorRecommendation

# Export to CSV with timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd"
$filename = "azure-advisor-recommendations-$timestamp.csv"
$recommendations | Export-Csv -Path $filename -NoTypeInformation

Write-Host "Exported $($recommendations.Count) recommendations to $filename"
```

### Method C: Azure CLI (For Command Line Users)

```bash
# Login to Azure
az login

# Set the subscription (replace with your subscription ID)
az account set --subscription "your-subscription-id"

# Export recommendations to CSV
timestamp=$(date +%Y-%m-%d)
filename="azure-advisor-recommendations-$timestamp.csv"

az advisor recommendation list --output table > $filename

echo "Exported recommendations to $filename"
```

**Important Notes:**
- PowerShell and CLI methods may require additional formatting
- Portal export is pre-formatted and platform-ready
- Always verify the CSV content before uploading

---

## 📄 Step 2: Understanding CSV Requirements

### Required File Specifications

| Requirement | Details | Why It Matters |
|-------------|---------|----------------|
| **File Format** | .csv only | Ensures consistent data parsing |
| **File Size** | Maximum 50MB | Prevents timeout and performance issues |
| **Encoding** | UTF-8 (with or without BOM) | Supports international characters |
| **Headers** | First row must contain column names | Enables automatic field mapping |

### Required Columns

Your CSV file **must** include these columns (case-insensitive):

#### Essential Columns (Must Have)
- `Category` - Recommendation category (Cost, Security, etc.)
- `Business Impact` - High, Medium, or Low
- `Recommendation` - The recommendation text
- `Subscription ID` - Azure subscription identifier
- `Resource Group` - Resource group name
- `Resource Name` - Specific resource name

#### Recommended Columns (Should Have)
- `Subscription Name` - Human-readable subscription name
- `Type` - Resource type (Virtual Machine, Storage Account, etc.)
- `Potential Benefits` - Description of potential improvements
- `Potential Annual Cost Savings` - Estimated cost savings amount
- `Currency` - Currency code (USD, EUR, etc.)
- `Retirement Date` - For deprecation recommendations
- `Retiring Feature` - Feature being retired
- `Updated Date` - When recommendation was last updated

### Sample CSV Structure

```csv
Category,Business Impact,Recommendation,Subscription ID,Subscription Name,Resource Group,Resource Name,Type,Potential Benefits,Potential Annual Cost Savings,Currency
Cost,High,Right-size underutilized virtual machines,12345678-1234-1234-1234-123456789012,Production Subscription,rg-web-prod,vm-web-01,Virtual Machine,Reduce costs by rightsizing,2400,USD
Security,Medium,Enable disk encryption,12345678-1234-1234-1234-123456789012,Production Subscription,rg-db-prod,vm-db-01,Virtual Machine,Improve data security,0,USD
Reliability,Low,Use availability zones,12345678-1234-1234-1234-123456789012,Production Subscription,rg-app-prod,vm-app-01,Virtual Machine,Improve availability,0,USD
```

---

## 📁 Step 3: Uploading Your CSV File

### Upload Process

1. **Navigate to Reports Section**
   - From the main dashboard, click **"Reports"** in the sidebar
   - Or click **"Generate New Report"** from any client page

2. **Select or Create Client**
   - Choose an existing client from the dropdown
   - Or click **"Add New Client"** to create one first
   - Client selection is required before upload

3. **Access Upload Interface**
   - Click **"Upload CSV File"** button
   - The upload dialog will open

4. **Choose Upload Method**

   **Option A: Drag and Drop**
   - Drag your CSV file into the upload area
   - You'll see a visual indicator when the file is ready to drop
   - Release to upload

   **Option B: File Browser**
   - Click **"Browse Files"** or **"Choose File"**
   - Navigate to your CSV file location
   - Select the file and click **"Open"**

5. **Monitor Upload Progress**
   - Progress bar shows upload status
   - File validation occurs automatically
   - You'll see confirmation when upload completes

6. **Verify Upload Success**
   - Check for green success message
   - Review the upload summary (number of recommendations found)
   - Note any warnings about missing columns

### Upload Interface Elements

```
┌─────────────────────────────────────────────────────────┐
│                    Upload CSV File                      │
├─────────────────────────────────────────────────────────┤
│  Client: [Production Client ▼]                         │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │         📁 Drag CSV file here                   │   │
│  │              or                                 │   │
│  │         [Browse Files]                          │   │
│  │                                                 │   │
│  │  Supported: .csv files up to 50MB              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ✅ File validation passed                             │
│  📊 Found 247 recommendations                          │
│  ⚠️  Missing optional column: Currency                 │
│                                                         │
│              [Cancel]  [Upload & Process]              │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Step 4: Validation and Processing

### Automatic Validation Checks

When you upload a file, the platform automatically checks:

1. **File Format Validation**
   - ✅ File has .csv extension
   - ✅ File is under 50MB
   - ✅ File is readable and not corrupted

2. **Structure Validation**
   - ✅ First row contains headers
   - ✅ At least 1 data row exists
   - ✅ Required columns are present

3. **Data Quality Validation**
   - ✅ Category values are recognized
   - ✅ Business Impact values are valid (High/Medium/Low)
   - ✅ Subscription IDs are properly formatted
   - ✅ No completely empty rows

### Validation Results

**Green (Success):** File meets all requirements
- All required columns present
- Data format is correct
- Ready for report generation

**Yellow (Warning):** File is usable but has minor issues
- Missing optional columns
- Some data formatting inconsistencies
- Will process but may affect report quality

**Red (Error):** File cannot be processed
- Missing required columns
- File format issues
- Data corruption or encoding problems

### Processing Timeline

| File Size | Expected Processing Time |
|-----------|-------------------------|
| Under 1MB (typical) | 15-30 seconds |
| 1-10MB | 30-90 seconds |
| 10-50MB | 2-5 minutes |

**Processing Steps:**
1. **Upload Complete** (immediate)
2. **File Validation** (5-10 seconds)
3. **Data Parsing** (varies by size)
4. **Recommendation Analysis** (10-30 seconds)
5. **Ready for Report Generation** ✅

---

## 🔧 Step 5: Troubleshooting Common Issues

### Issue 1: File Upload Fails

**Symptoms:**
- Upload progress bar stops
- Error message appears
- File doesn't appear in system

**Common Causes & Solutions:**

```
❌ File too large (over 50MB)
✅ Solution: Use filters in Azure Advisor to export smaller datasets
   - Filter by subscription
   - Filter by resource group
   - Filter by recommendation category

❌ File format not recognized
✅ Solution: Ensure file has .csv extension
   - Save as CSV from Excel: File > Save As > CSV (Comma delimited)
   - Verify file extension is .csv, not .txt or .xlsx

❌ Internet connection issues
✅ Solution: Check connection and retry
   - Test with smaller file first
   - Try different browser
   - Clear browser cache
```

### Issue 2: Validation Errors

**Missing Required Columns:**
```
❌ Error: "Required column 'Category' not found"
✅ Solutions:
   1. Check column spelling (case-insensitive)
   2. Ensure first row has headers
   3. Remove any blank rows at the top
   4. Check for hidden characters in column names
```

**Data Format Issues:**
```
❌ Error: "Invalid Business Impact values"
✅ Acceptable values: High, Medium, Low, H, M, L
❌ Invalid values: Critical, Normal, 1, 2, 3

❌ Error: "Subscription ID format invalid"
✅ Format: 12345678-1234-1234-1234-123456789012
❌ Invalid: partial IDs, subscription names only
```

### Issue 3: Poor Data Quality

**Warning: "Many recommendations missing cost data"**
- Impact: Cost optimization reports will be less effective
- Solution: Re-export from Azure Advisor with cost data enabled

**Warning: "Limited recommendation details"**
- Impact: Technical reports may lack implementation details
- Solution: Ensure all Azure Advisor recommendation types are included

### Issue 4: Processing Hangs or Fails

**If processing takes longer than expected:**

1. **Check File Size**
   - Files over 10MB may take several minutes
   - Progress will update every 30 seconds

2. **Browser Issues**
   - Try refreshing the page (upload may have completed)
   - Use Chrome or Edge for best compatibility
   - Disable browser extensions that might interfere

3. **Network Issues**
   - Stable internet connection required
   - Avoid uploads on slow or unstable connections

4. **Contact Support**
   - If processing fails after 10 minutes
   - Provide upload ID and file details

---

## 🚀 Best Practices for Success

### File Preparation Best Practices

1. **Regular Export Schedule**
   - Export monthly for consistent reporting
   - Mark calendar for first week of each month
   - Azure recommendations update regularly

2. **Organized File Naming**
   ```
   Good: azure-advisor-production-2025-09.csv
   Good: client-abc-advisor-data-sep2025.csv
   Bad: download.csv
   Bad: recommendations.csv
   ```

3. **Data Quality Checks**
   - Open CSV in Excel/text editor before uploading
   - Verify all expected columns are present
   - Check for reasonable recommendation counts (typically 10-500)

4. **Client Organization**
   - Create clients before uploading their data
   - Use consistent client naming conventions
   - Add notes about each client's environment

### Upload Workflow Best Practices

1. **Batch Processing**
   - Upload multiple clients' files in sequence
   - Don't upload files simultaneously (can cause conflicts)
   - Process during low-traffic times if possible

2. **Verification Steps**
   - Always review upload summary before proceeding
   - Check recommendation count against expectations
   - Note any validation warnings for follow-up

3. **Error Recovery**
   - Keep original CSV files for re-upload if needed
   - Screenshot any error messages for support
   - Document successful upload settings for consistency

### Long-Term Success Strategies

1. **Automation Opportunities**
   - Use PowerShell/CLI for regular exports
   - Set up scheduled exports where possible
   - Consider API integration for enterprise users

2. **Quality Monitoring**
   - Track recommendation trends over time
   - Monitor cost savings opportunities
   - Compare data quality across exports

3. **Team Coordination**
   - Establish who handles uploads for each client
   - Share successful upload templates
   - Document client-specific requirements

---

## 📊 Understanding Upload Results

### Upload Summary Information

After a successful upload, you'll see:

```
✅ Upload Complete

📁 File: azure-advisor-production-2025-09.csv
👤 Client: Production Environment
📊 Recommendations Found: 247

Category Breakdown:
• Cost: 89 recommendations (36%)
• Security: 67 recommendations (27%)
• Reliability: 58 recommendations (23%)
• Operational Excellence: 33 recommendations (14%)

💰 Potential Annual Savings: $45,670
⚡ Ready for report generation
```

### Data Quality Indicators

**Excellent (90-100% data completeness):**
- All required and optional columns present
- Cost data available for most recommendations
- Detailed descriptions and resource information

**Good (70-89% data completeness):**
- All required columns present
- Some optional data missing
- May affect advanced report features

**Acceptable (50-69% data completeness):**
- Required columns present but limited detail
- Basic reports will work
- Advanced analytics may be limited

**Poor (Under 50% data completeness):**
- Missing critical information
- Consider re-exporting with more complete data
- Contact support for data quality improvement tips

---

## 🔗 Next Steps

### After Successful Upload

1. **Generate Your First Report**
   - Choose appropriate report type for your audience
   - Review [Report Types Guide](REPORT_TYPES.md) for guidance
   - Start with Executive Summary for business stakeholders

2. **Explore Dashboard Analytics**
   - View recommendation trends
   - Analyze cost optimization opportunities
   - Set up monitoring for key metrics

3. **Set Up Regular Workflows**
   - Schedule monthly uploads
   - Create template emails for report delivery
   - Document successful processes for team members

### Additional Resources

- **[Report Generation Guide](REPORT_GENERATION_GUIDE.md)** - Next step after CSV upload
- **[Client Management Guide](CLIENT_MANAGEMENT.md)** - Organizing your clients effectively
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Detailed problem resolution
- **[API Documentation](API_DOCUMENTATION.md)** - For automated uploads

### Support and Training

- **📧 Email Support:** upload-help@azureadvisorreports.com
- **💬 Live Chat:** Available in platform (bottom-right corner)
- **🎥 Video Tutorial:** [CSV Upload Walkthrough](https://youtube.com/watch?v=csv-upload-demo)
- **📞 Training Session:** Schedule a 1-on-1 walkthrough

---

## 🏁 Quick Reference

### Pre-Upload Checklist
- [ ] CSV file exported from Azure Advisor
- [ ] File size under 50MB
- [ ] Client created in platform
- [ ] Required columns present
- [ ] Stable internet connection

### Upload Checklist
- [ ] Correct client selected
- [ ] File uploaded successfully
- [ ] Validation passed (green status)
- [ ] Recommendation count reasonable
- [ ] No critical errors reported

### Post-Upload Checklist
- [ ] Upload summary reviewed
- [ ] Data quality acceptable
- [ ] Ready to generate reports
- [ ] File backed up for future reference
- [ ] Next upload scheduled

---

*This guide is part of the Azure Advisor Reports Platform documentation. For updates or suggestions, contact the documentation team.*

**Document Status:** ✅ Complete | 📅 Last Updated: September 29, 2025 | 🔄 Next Review: October 29, 2025