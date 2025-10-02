# Troubleshooting Guide
## Azure Advisor Reports Platform

**Document Type:** Support Guide
**Last Updated:** September 29, 2025
**Version:** 1.0
**Audience:** All users experiencing issues

---

## 🆘 Quick Help

**Need immediate assistance?**
- 📞 **Critical Issues:** Call support at +1-800-ADVISOR
- 💬 **Live Chat:** Available in platform (bottom-right corner)
- 📧 **Email:** support@azureadvisorreports.com
- 🔍 **Search this guide:** Use Ctrl+F (Windows) or Cmd+F (Mac)

**Before contacting support:**
1. Try the solutions in this guide
2. Clear your browser cache and cookies
3. Test with a different browser
4. Note any error messages exactly as displayed

---

## 📋 Issue Categories

### 🔐 Authentication & Login Issues
### 📁 File Upload Problems
### 📊 Report Generation Errors
### 🏃‍♂️ Performance Issues
### 🌐 Browser Compatibility
### 💾 Data & Account Issues

---

## 🔐 Authentication & Login Issues

### Issue: Cannot Sign In with Microsoft

**Symptoms:**
- "Sign in with Microsoft" button doesn't work
- Redirected to error page after entering credentials
- "Access denied" or "Invalid permissions" messages

**Immediate Solutions:**

```
🔧 Solution 1: Check Browser Settings
✅ Enable cookies and JavaScript
✅ Disable private/incognito mode
✅ Clear browser cache and cookies
✅ Try different browser (Chrome, Edge, Firefox)

🔧 Solution 2: Verify Account Access
✅ Confirm you have an Azure AD account
✅ Check if your organization requires specific permissions
✅ Contact your IT administrator if using enterprise account
✅ Try signing in to portal.azure.com first

🔧 Solution 3: Network & Firewall
✅ Check if your organization blocks Azure AD authentication
✅ Try from different network (mobile hotspot)
✅ Disable VPN temporarily
✅ Contact IT about firewall exceptions
```

**Advanced Troubleshooting:**

1. **Check Azure AD Application Status**
   - Your organization may need to approve the application
   - IT admin needs to consent to required permissions
   - Application may be blocked by organizational policies

2. **Browser Console Errors**
   - Press F12 to open developer tools
   - Look for red errors in Console tab
   - Share error details with support team

3. **Authentication Flow Debug**
   ```
   Normal Flow:
   Platform → Azure AD Login → Consent → Redirect → Success

   Common Failure Points:
   - Blocked at Azure AD Login (account/network issue)
   - Blocked at Consent (permissions issue)
   - Failed Redirect (browser/cookie issue)
   ```

### Issue: Session Keeps Expiring

**Symptoms:**
- Repeatedly prompted to log in
- "Session expired" messages during normal use
- Automatic logout after short periods

**Solutions:**

```
🔧 Immediate Fixes:
✅ Enable "Keep me signed in" during login
✅ Ensure cookies are enabled and not being blocked
✅ Add platform domain to browser trusted sites
✅ Disable aggressive ad blockers or privacy extensions

🔧 Long-term Solutions:
✅ Contact IT about extending Azure AD token lifetime
✅ Use platform regularly to maintain session
✅ Bookmark platform URL for quick re-access
✅ Consider using dedicated browser profile
```

### Issue: Wrong User Account Displayed

**Symptoms:**
- Platform shows different user name than expected
- Cannot access expected organizations or data
- Permission errors for features you should have access to

**Solutions:**

```
🔧 Account Switching:
✅ Sign out completely from platform
✅ Sign out from all Microsoft accounts in browser
✅ Clear browser cache and cookies
✅ Visit platform and sign in with correct account

🔧 Multiple Account Management:
✅ Use different browser profiles for different accounts
✅ Use incognito/private mode for testing accounts
✅ Sign out of other Microsoft services before accessing platform
✅ Contact support if accounts remain mixed
```

---

## 📁 File Upload Problems

### Issue: CSV Upload Fails or Hangs

**Symptoms:**
- Upload progress bar stops or freezes
- "Upload failed" error messages
- File doesn't appear after upload attempt
- Browser shows "Page unresponsive" warnings

**Immediate Diagnostics:**

```
🔍 Check File Properties:
✅ File size under 50MB?
✅ File extension is .csv?
✅ File opens correctly in Excel/text editor?
✅ File contains data (not empty)?

🔍 Check Connection:
✅ Stable internet connection?
✅ Not on slow or metered connection?
✅ No VPN issues affecting upload?
✅ Firewall not blocking file transfers?
```

**Step-by-Step Solutions:**

1. **File Size Reduction**
   ```powershell
   # If file is too large, filter data in Azure Advisor:

   # Option 1: Filter by Resource Group
   Get-AzAdvisorRecommendation -ResourceGroupName "specific-rg" | Export-Csv

   # Option 2: Filter by Category
   Get-AzAdvisorRecommendation | Where-Object {$_.Category -eq "Cost"} | Export-Csv

   # Option 3: Split by Subscription
   Get-AzAdvisorRecommendation -SubscriptionId "sub-1" | Export-Csv
   ```

2. **File Format Verification**
   ```
   ✅ Correct CSV format:
   Category,Business Impact,Recommendation,Resource Name...
   Cost,High,Right-size VM,vm-web-01...

   ❌ Incorrect formats:
   - Excel files saved as .xlsx
   - Tab-separated files
   - Files with BOM encoding issues
   - Corrupted downloads
   ```

3. **Browser-Specific Solutions**
   ```
   Chrome:
   ✅ Disable extensions temporarily
   ✅ Clear cache: Settings → Privacy → Clear browsing data
   ✅ Try incognito mode

   Firefox:
   ✅ Disable add-ons
   ✅ Clear cache: Options → Privacy → Clear Data
   ✅ Try private browsing

   Edge:
   ✅ Reset browser settings
   ✅ Clear cache: Settings → Privacy → Clear browsing data
   ✅ Try InPrivate mode
   ```

### Issue: File Validation Errors

**Common Validation Errors:**

#### Error: "Required column missing"
```
❌ "Required column 'Category' not found"

🔧 Solutions:
✅ Check column spelling exactly: "Category" not "category" or "Categories"
✅ Ensure first row contains headers
✅ Remove empty rows at top of file
✅ Check for hidden characters (copy column names to text editor)
✅ Re-export from Azure Advisor if columns missing
```

#### Error: "Invalid data format"
```
❌ "Business Impact values not recognized"

🔧 Accepted Values:
✅ High, Medium, Low
✅ H, M, L
✅ 1, 2, 3 (where 1=High, 2=Medium, 3=Low)

❌ Invalid Values:
❌ Critical, Normal, Minor
❌ 0, 4, 5
❌ Empty cells in Business Impact column
```

#### Error: "File encoding not supported"
```
❌ "Unable to parse CSV file - encoding error"

🔧 Solutions:
✅ Save file as UTF-8 encoding in Excel:
   File → Save As → More Options → Tools → Web Options → Encoding → UTF-8
✅ Use "CSV UTF-8" format when saving from Excel
✅ Open in Notepad and save with UTF-8 encoding
✅ Re-export from Azure Advisor
```

### Issue: Upload Succeeds but Shows Wrong Data

**Symptoms:**
- Upload completes but recommendation count seems wrong
- Categories don't match expectations
- Missing cost or savings data

**Diagnostic Steps:**

1. **Verify Source Data**
   ```
   ✅ Open CSV in Excel before uploading
   ✅ Count rows manually (should match platform count)
   ✅ Check all categories are present
   ✅ Verify cost data columns have values
   ```

2. **Check Azure Advisor Export Settings**
   ```
   ✅ Include all recommendation types in export
   ✅ Set scope to correct subscription(s)
   ✅ Don't filter out categories during export
   ✅ Ensure recent data (not old cached export)
   ```

3. **Platform Processing Issues**
   ```
   ✅ Wait for processing to complete fully
   ✅ Refresh page and check again
   ✅ Compare with previous uploads from same source
   ✅ Contact support if discrepancies persist
   ```

---

## 📊 Report Generation Errors

### Issue: Report Generation Fails

**Symptoms:**
- "Report generation failed" error message
- Report status stuck on "Processing" for hours
- Generated report is empty or incomplete

**Immediate Actions:**

```
🔧 Quick Fixes:
✅ Refresh page and check status again
✅ Verify CSV upload was successful
✅ Check if client has sufficient recommendation data
✅ Try generating different report type

🔧 Retry Process:
✅ Wait 5 minutes and try again
✅ Start with simpler report type (Executive Summary)
✅ Check system status page for known issues
✅ Contact support if persistent
```

**Detailed Troubleshooting:**

1. **Processing Time Guidelines**
   ```
   Expected Processing Times:
   ✅ 1-50 recommendations: 1-2 minutes
   ✅ 51-200 recommendations: 2-4 minutes
   ✅ 201-500 recommendations: 4-8 minutes
   ✅ 500+ recommendations: 8-15 minutes

   ❌ Contact support if exceeding these timeframes
   ```

2. **Data Quality Requirements**
   ```
   Minimum for Report Generation:
   ✅ At least 1 recommendation uploaded
   ✅ Category field populated for all recommendations
   ✅ Business Impact field populated
   ✅ Recommendation text present

   For Quality Reports:
   ✅ Cost data for cost optimization reports
   ✅ Resource details for technical reports
   ✅ Security categories for security reports
   ```

3. **Browser Memory Issues**
   ```
   Large Report Symptoms:
   ❌ Browser becomes slow during generation
   ❌ "Page unresponsive" warnings
   ❌ Report generation times out

   Solutions:
   ✅ Close other browser tabs
   ✅ Use latest browser version
   ✅ Try on computer with more RAM
   ✅ Generate smaller reports (filter data first)
   ```

### Issue: Report Download Problems

**Symptoms:**
- Download button doesn't work
- Downloaded file is corrupted or empty
- PDF format issues or HTML rendering problems

**Download Solutions:**

```
🔧 Browser Download Issues:
✅ Disable download managers or extensions
✅ Allow pop-ups for platform domain
✅ Check Downloads folder (may download automatically)
✅ Try different browser
✅ Right-click download link and "Save As"

🔧 File Format Issues:
✅ PDF problems: Try HTML version first
✅ HTML problems: Try PDF version first
✅ Empty files: Wait longer for generation to complete
✅ Corrupted files: Clear browser cache and re-download
```

### Issue: Report Content Quality Issues

**Symptoms:**
- Report missing expected data or sections
- Formatting issues in generated reports
- Charts or graphs not displaying correctly

**Content Quality Diagnostics:**

1. **Missing Cost Data**
   ```
   Problem: Cost optimization report shows "No cost data available"

   Solutions:
   ✅ Verify CSV includes "Potential Annual Cost Savings" column
   ✅ Check if values in cost column are numbers, not text
   ✅ Re-export from Azure Advisor with cost recommendations enabled
   ✅ Use different report type if cost data unavailable
   ```

2. **Incomplete Technical Details**
   ```
   Problem: Technical report lacks implementation details

   Solutions:
   ✅ Ensure "Recommendation" column has detailed text
   ✅ Include "Potential Benefits" column for more context
   ✅ Verify all Azure Advisor recommendation types included
   ✅ Try Detailed Report type instead of Executive Summary
   ```

3. **Chart Display Issues**
   ```
   Problem: Charts not showing or appearing blank

   Solutions:
   ✅ Enable JavaScript in browser
   ✅ Disable ad blockers temporarily
   ✅ Try different browser
   ✅ Contact support with browser details
   ```

---

## 🏃‍♂️ Performance Issues

### Issue: Platform Loading Slowly

**Symptoms:**
- Pages take long time to load
- Features respond slowly to clicks
- Dashboard charts load slowly or not at all

**Performance Optimization:**

```
🔧 Browser Optimization:
✅ Clear browser cache and cookies
✅ Disable unnecessary browser extensions
✅ Close other tabs and applications
✅ Restart browser

🔧 Network Optimization:
✅ Check internet connection speed
✅ Try different network (mobile hotspot)
✅ Disable VPN temporarily
✅ Contact IT about network restrictions

🔧 System Optimization:
✅ Close other applications using memory
✅ Use latest browser version
✅ Restart computer if necessary
✅ Try different device
```

### Issue: Dashboard Not Updating

**Symptoms:**
- Recent uploads don't appear in dashboard
- Metrics show old data
- Charts display outdated information

**Data Refresh Solutions:**

```
🔧 Manual Refresh:
✅ Press F5 or Ctrl+F5 to force refresh
✅ Clear browser cache completely
✅ Sign out and sign back in
✅ Try different browser

🔧 Check Data Processing:
✅ Verify uploads completed successfully
✅ Check if reports were generated
✅ Allow 5-10 minutes for dashboard updates
✅ Contact support if data doesn't update after 1 hour
```

---

## 🌐 Browser Compatibility

### Supported Browsers

```
✅ Fully Supported:
- Google Chrome 90+
- Microsoft Edge 90+
- Mozilla Firefox 88+
- Safari 14+ (Mac only)

⚠️ Limited Support:
- Internet Explorer 11 (deprecated)
- Older browser versions

❌ Not Supported:
- Internet Explorer 10 and below
- Very old mobile browsers
```

### Browser-Specific Issues

#### Chrome Issues
```
Problem: Extensions interfering with platform
Solution: Test in incognito mode, disable extensions one by one

Problem: Download issues
Solution: Check Chrome download settings, allow automatic downloads

Problem: Authentication loops
Solution: Clear Chrome cookies for Microsoft domains
```

#### Firefox Issues
```
Problem: File upload failures
Solution: Disable Enhanced Tracking Protection for platform

Problem: Report display issues
Solution: Ensure JavaScript enabled, update Firefox

Problem: Session timeouts
Solution: Allow cookies, disable strict privacy settings
```

#### Safari Issues
```
Problem: Authentication problems
Solution: Enable cross-site tracking, allow pop-ups

Problem: Download issues
Solution: Check Safari download preferences

Problem: Display formatting
Solution: Update Safari, disable reader mode
```

#### Edge Issues
```
Problem: Legacy compatibility
Solution: Ensure using new Edge (Chromium-based), not Legacy Edge

Problem: Corporate restrictions
Solution: Contact IT about browser policies

Problem: File upload timeouts
Solution: Disable SmartScreen temporarily for uploads
```

---

## 💾 Data & Account Issues

### Issue: Missing Clients or Data

**Symptoms:**
- Previously created clients don't appear
- Uploaded files seem to have disappeared
- Reports generated before are no longer available

**Data Recovery Steps:**

```
🔧 Account Verification:
✅ Confirm signed in with correct Microsoft account
✅ Check if using work vs personal account
✅ Verify organization access hasn't changed
✅ Contact admin about user permissions

🔧 Data Location Check:
✅ Use search function to find clients
✅ Check different client status filters
✅ Look in different report categories
✅ Check if accidentally deleted

🔧 Browser Data Issues:
✅ Clear cache but keep login data
✅ Try different browser to verify data exists
✅ Disable browser sync that might cause conflicts
✅ Contact support with account details
```

### Issue: Duplicate Clients or Reports

**Symptoms:**
- Same client appears multiple times
- Duplicate reports with same data
- Cannot delete duplicate entries

**Duplicate Management:**

```
🔧 Prevention:
✅ Search for existing client before creating new one
✅ Use consistent naming conventions
✅ Check carefully before confirming creation
✅ Train team members on proper procedures

🔧 Resolution:
✅ Contact support to merge duplicate clients
✅ Delete duplicate reports if permissions allow
✅ Update client information to distinguish similar entries
✅ Document naming conventions for team
```

### Issue: Permission or Access Errors

**Symptoms:**
- "Access denied" messages for features
- Cannot create clients or upload files
- Limited functionality compared to expected

**Permission Troubleshooting:**

```
🔧 Account Role Check:
✅ Verify account type (admin, user, viewer)
✅ Contact organization admin about role assignment
✅ Check if temporary permissions expired
✅ Confirm account is properly provisioned

🔧 Organization Settings:
✅ Verify organization policies allow platform access
✅ Check if specific features are disabled by admin
✅ Contact IT about Azure AD app permissions
✅ Request role elevation if needed for specific tasks
```

---

## 🔧 Self-Service Diagnostic Tools

### Browser Console Check

**How to access:**
1. Press F12 (Windows) or Cmd+Option+I (Mac)
2. Click "Console" tab
3. Look for red error messages
4. Share error details with support

**Common Error Messages:**
```
❌ "Failed to fetch" - Network/connectivity issue
❌ "401 Unauthorized" - Authentication problem
❌ "413 Request Entity Too Large" - File too big
❌ "CORS error" - Browser security issue
```

### Network Connectivity Test

**Basic Tests:**
```powershell
# Test basic connectivity (Windows)
ping platform.azureadvisorreports.com
nslookup platform.azureadvisorreports.com

# Test HTTPS access
curl -I https://platform.azureadvisorreports.com

# Test from different network
# Try mobile hotspot or different WiFi
```

### Clear Browser Data Completely

**Chrome:**
1. Settings → Privacy and security → Clear browsing data
2. Select "All time"
3. Check all boxes
4. Clear data

**Firefox:**
1. Options → Privacy & Security → Clear Data
2. Check all boxes
3. Clear

**Edge:**
1. Settings → Privacy, search, and services → Clear browsing data
2. Choose "All time"
3. Select all data types
4. Clear now

---

## 📞 When to Contact Support

### Before Contacting Support

**Information to Gather:**
- [ ] Exact error message (screenshot preferred)
- [ ] Browser type and version
- [ ] Operating system
- [ ] File details (size, name, source)
- [ ] Steps you've already tried
- [ ] When the issue first occurred

**Self-Service Attempts:**
- [ ] Tried different browser
- [ ] Cleared cache and cookies
- [ ] Attempted with different file/data
- [ ] Checked this troubleshooting guide
- [ ] Waited appropriate time for processing

### Support Contact Methods

**🔴 Critical Issues (System Down, Data Loss):**
- Phone: +1-800-ADVISOR (24/7)
- Emergency email: critical@azureadvisorreports.com

**🟡 Standard Issues (Features Not Working):**
- Live chat: Available in platform 8 AM - 8 PM EST
- Email: support@azureadvisorreports.com
- Response time: Within 4 hours business days

**🟢 Questions & Training:**
- Email: help@azureadvisorreports.com
- Community forum: community.azureadvisorreports.com
- Response time: Within 24 hours

### Support Ticket Best Practices

**Subject Line Examples:**
```
✅ Good: "CSV upload fails - validation error on Category column"
✅ Good: "Report generation timeout - 500+ recommendations"
❌ Poor: "Help - not working"
❌ Poor: "Problem with platform"
```

**Information to Include:**
1. **Account Details:**
   - Email address used for login
   - Organization name
   - User role

2. **Issue Details:**
   - What you were trying to do
   - What happened instead
   - Exact error messages
   - When it started happening

3. **Environment:**
   - Browser and version
   - Operating system
   - Network environment (corporate, home, mobile)

4. **Files (if relevant):**
   - Sample CSV file (remove sensitive data)
   - Screenshots of errors
   - Browser console errors

---

## 📚 Additional Resources

### Documentation Links
- [Getting Started Guide](GETTING_STARTED.md) - Basic platform introduction
- [CSV Upload Guide](CSV_UPLOAD_GUIDE.md) - Detailed upload instructions
- [Report Generation Guide](REPORT_GENERATION_GUIDE.md) - Creating and customizing reports
- [API Documentation](API_DOCUMENTATION.md) - For developers and integrations

### Video Tutorials
- [Platform Overview (5 min)](https://youtube.com/watch?v=platform-overview)
- [CSV Upload Walkthrough (8 min)](https://youtube.com/watch?v=csv-upload-demo)
- [Troubleshooting Common Issues (12 min)](https://youtube.com/watch?v=troubleshooting-guide)

### Community Resources
- [User Community Forum](https://community.azureadvisorreports.com)
- [Best Practices Blog](https://blog.azureadvisorreports.com)
- [Monthly Webinars](https://events.azureadvisorreports.com)

---

## 🏁 Quick Reference Card

### Emergency Checklist
1. **Is it a known issue?** Check [status page](https://status.azureadvisorreports.com)
2. **Try different browser** - Often solves 50% of issues
3. **Clear cache and cookies** - Resolves authentication and loading issues
4. **Check file requirements** - Most upload issues are file-related
5. **Wait and retry** - Server processing can take several minutes
6. **Contact support** - If above steps don't help

### Common Quick Fixes
| Issue | Quick Fix |
|-------|-----------|
| Can't log in | Clear cookies, try different browser |
| Upload fails | Check file size (<50MB), try Chrome |
| Report won't generate | Wait 10 minutes, refresh page |
| Page loads slowly | Close other tabs, disable extensions |
| Download doesn't work | Right-click link, "Save As" |
| Data missing | Check correct Microsoft account |

---

*This troubleshooting guide is continuously updated based on user feedback and support ticket trends. For suggestions or improvements, contact documentation@azureadvisorreports.com*

**Document Status:** ✅ Complete | 📅 Last Updated: September 29, 2025 | 🔄 Next Review: November 29, 2025