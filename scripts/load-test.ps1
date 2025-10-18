#Requires -Version 7.0
<#
.SYNOPSIS
    Performance and load testing script for Azure Advisor Reports Platform

.DESCRIPTION
    Comprehensive performance testing script that validates:
    - Large CSV file processing
    - Concurrent report generation
    - API response times
    - Memory usage
    - Database query performance

.PARAMETER TestType
    Type of test to run: Quick, Standard, Load, Stress, All

.PARAMETER BaseUrl
    Base URL of the API (default: http://localhost:8000)

.PARAMETER ConcurrentUsers
    Number of concurrent users to simulate (default: 10)

.EXAMPLE
    .\load-test.ps1 -TestType Quick
    .\load-test.ps1 -TestType Load -ConcurrentUsers 50
    .\load-test.ps1 -TestType All -BaseUrl "https://staging.example.com"

.NOTES
    Author: QA Team
    Date: October 6, 2025
    Requires: PowerShell 7.0+, Python 3.11+
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Quick', 'Standard', 'Load', 'Stress', 'All')]
    [string]$TestType = 'Quick',

    [Parameter(Mandatory=$false)]
    [string]$BaseUrl = 'http://localhost:8000',

    [Parameter(Mandatory=$false)]
    [int]$ConcurrentUsers = 10,

    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\test-results\performance"
)

# Script configuration
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'Continue'

# Test configuration
$Script:Config = @{
    BaseUrl = $BaseUrl
    ApiEndpoint = "$BaseUrl/api"
    TestDataDir = ".\test_data"
    ReportsDir = Join-Path $OutputDir "reports"
    LogFile = Join-Path $OutputDir "load-test-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
    ResultsFile = Join-Path $OutputDir "results-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
}

# Test results storage
$Script:Results = @{
    TestType = $TestType
    StartTime = Get-Date
    Tests = @()
    Summary = @{}
}

#region Helper Functions

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet('Info', 'Warning', 'Error', 'Success')]
        [string]$Level = 'Info'
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] [$Level] $Message"

    switch ($Level) {
        'Info'    { Write-Host $logMessage -ForegroundColor Cyan }
        'Warning' { Write-Host $logMessage -ForegroundColor Yellow }
        'Error'   { Write-Host $logMessage -ForegroundColor Red }
        'Success' { Write-Host $logMessage -ForegroundColor Green }
    }

    Add-Content -Path $Script:Config.LogFile -Value $logMessage
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." -Level Info

    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Log "Python version: $pythonVersion" -Level Success
    } catch {
        Write-Log "Python not found. Please install Python 3.11+" -Level Error
        return $false
    }

    # Check if backend is running
    try {
        $response = Invoke-WebRequest -Uri "$($Script:Config.BaseUrl)/api/health/" -Method GET -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-Log "Backend is running and healthy" -Level Success
        }
    } catch {
        Write-Log "Backend is not accessible at $($Script:Config.BaseUrl)" -Level Error
        Write-Log "Please start the backend server first: python manage.py runserver" -Level Warning
        return $false
    }

    # Check test data directory
    if (-not (Test-Path $Script:Config.TestDataDir)) {
        Write-Log "Creating test data directory..." -Level Info
        New-Item -ItemType Directory -Path $Script:Config.TestDataDir -Force | Out-Null
    }

    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    if (-not (Test-Path $Script:Config.ReportsDir)) {
        New-Item -ItemType Directory -Path $Script:Config.ReportsDir -Force | Out-Null
    }

    Write-Log "All prerequisites met" -Level Success
    return $true
}

function Measure-ApiCall {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = 'GET',
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )

    Write-Log "Testing: $Name" -Level Info

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $success = $false
    $statusCode = 0
    $errorMessage = $null

    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
            TimeoutSec = 30
        }

        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            $params.ContentType = 'application/json'
        }

        $response = Invoke-WebRequest @params
        $statusCode = $response.StatusCode
        $success = ($statusCode -ge 200 -and $statusCode -lt 300)

    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        $errorMessage = $_.Exception.Message
        Write-Log "Request failed: $errorMessage" -Level Warning
    } finally {
        $stopwatch.Stop()
    }

    $result = @{
        Name = $Name
        Url = $Url
        Method = $Method
        Duration = $stopwatch.ElapsedMilliseconds
        Success = $success
        StatusCode = $statusCode
        ErrorMessage = $errorMessage
        Timestamp = Get-Date
    }

    $Script:Results.Tests += $result

    if ($success) {
        Write-Log "$Name - ${stopwatch.ElapsedMilliseconds}ms - Status: $statusCode" -Level Success
    } else {
        Write-Log "$Name - ${stopwatch.ElapsedMilliseconds}ms - Status: $statusCode - Error: $errorMessage" -Level Error
    }

    return $result
}

function New-TestCSV {
    param(
        [int]$Rows = 100,
        [string]$Filename
    )

    Write-Log "Generating test CSV with $Rows rows..." -Level Info

    $csvPath = Join-Path $Script:Config.TestDataDir $Filename

    # CSV Header (Azure Advisor format)
    $header = @(
        'Category',
        'Business Impact',
        'Recommendation',
        'Subscription ID',
        'Subscription Name',
        'Resource Group',
        'Resource Name',
        'Resource Type',
        'Potential Savings',
        'Currency',
        'Potential Benefits',
        'Retirement Date',
        'Retiring Feature',
        'Updated Date'
    )

    $categories = @('Cost', 'Security', 'Reliability', 'Operational Excellence', 'Performance')
    $impacts = @('High', 'Medium', 'Low')
    $resourceTypes = @('Microsoft.Compute/virtualMachines', 'Microsoft.Storage/storageAccounts', 'Microsoft.Sql/servers')

    # Create CSV content
    $csv = @()
    $csv += $header -join ','

    for ($i = 1; $i -le $Rows; $i++) {
        $category = $categories | Get-Random
        $impact = $impacts | Get-Random
        $resourceType = $resourceTypes | Get-Random

        $row = @(
            $category,
            $impact,
            "Sample recommendation $i for performance improvement",
            "sub-$(Get-Random -Minimum 1000 -Maximum 9999)",
            "Subscription $i",
            "rg-test-$i",
            "resource-$i",
            $resourceType,
            (Get-Random -Minimum 10 -Maximum 5000),
            'USD',
            'Improved performance and cost savings',
            '',
            '',
            (Get-Date).ToString('yyyy-MM-dd')
        )

        $csv += $row -join ','
    }

    $csv | Out-File -FilePath $csvPath -Encoding UTF8
    Write-Log "Created test CSV: $csvPath" -Level Success

    return $csvPath
}

function Test-HealthEndpoint {
    Write-Log "=== Testing Health Endpoint ===" -Level Info
    Measure-ApiCall -Name "Health Check" -Url "$($Script:Config.ApiEndpoint)/health/" -Method GET
}

function Test-CSVProcessingPerformance {
    param([int]$Rows = 100)

    Write-Log "=== Testing CSV Processing Performance ($Rows rows) ===" -Level Info

    # Generate test CSV
    $csvPath = New-TestCSV -Rows $Rows -Filename "test_$Rows.csv"

    # Measure file size
    $fileSize = (Get-Item $csvPath).Length
    Write-Log "Test file size: $([Math]::Round($fileSize / 1KB, 2)) KB" -Level Info

    # Time the CSV parsing (using Python directly)
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        $pythonScript = @"
import pandas as pd
import sys

csv_path = r'$csvPath'
df = pd.read_csv(csv_path, encoding='utf-8-sig')
print(f'Rows: {len(df)}')
print(f'Columns: {len(df.columns)}')
print(f'Memory: {df.memory_usage(deep=True).sum() / 1024:.2f} KB')
"@

        $result = $pythonScript | python

        $stopwatch.Stop()

        Write-Log "CSV Processing completed in ${stopwatch.ElapsedMilliseconds}ms" -Level Success
        Write-Log $result -Level Info

        $Script:Results.Tests += @{
            Name = "CSV Processing - $Rows rows"
            Duration = $stopwatch.ElapsedMilliseconds
            FileSize = $fileSize
            Rows = $Rows
            Success = $true
            Timestamp = Get-Date
        }

    } catch {
        $stopwatch.Stop()
        Write-Log "CSV Processing failed: $($_.Exception.Message)" -Level Error

        $Script:Results.Tests += @{
            Name = "CSV Processing - $Rows rows"
            Duration = $stopwatch.ElapsedMilliseconds
            Success = $false
            ErrorMessage = $_.Exception.Message
            Timestamp = Get-Date
        }
    }
}

function Test-ConcurrentRequests {
    param(
        [int]$Count = 10,
        [string]$Endpoint = '/api/health/'
    )

    Write-Log "=== Testing Concurrent Requests (Count: $Count) ===" -Level Info

    $jobs = @()
    $startTime = Get-Date

    # Start concurrent requests
    for ($i = 1; $i -le $Count; $i++) {
        $jobs += Start-Job -ScriptBlock {
            param($url)

            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                $response = Invoke-WebRequest -Uri $url -Method GET -UseBasicParsing -TimeoutSec 30
                $stopwatch.Stop()

                return @{
                    Success = $true
                    Duration = $stopwatch.ElapsedMilliseconds
                    StatusCode = $response.StatusCode
                }
            } catch {
                $stopwatch.Stop()
                return @{
                    Success = $false
                    Duration = $stopwatch.ElapsedMilliseconds
                    Error = $_.Exception.Message
                }
            }
        } -ArgumentList "$($Script:Config.BaseUrl)$Endpoint"
    }

    # Wait for all jobs to complete
    Write-Log "Waiting for $Count concurrent requests to complete..." -Level Info
    $results = $jobs | Wait-Job | Receive-Job
    $jobs | Remove-Job

    $endTime = Get-Date
    $totalDuration = ($endTime - $startTime).TotalMilliseconds

    # Analyze results
    $successful = ($results | Where-Object { $_.Success }).Count
    $failed = $Count - $successful
    $avgDuration = ($results | Measure-Object -Property Duration -Average).Average
    $maxDuration = ($results | Measure-Object -Property Duration -Maximum).Maximum
    $minDuration = ($results | Measure-Object -Property Duration -Minimum).Minimum

    Write-Log "Concurrent Request Results:" -Level Success
    Write-Log "  Total Requests: $Count" -Level Info
    Write-Log "  Successful: $successful" -Level $(if ($successful -eq $Count) { 'Success' } else { 'Warning' })
    Write-Log "  Failed: $failed" -Level $(if ($failed -eq 0) { 'Success' } else { 'Error' })
    Write-Log "  Total Duration: $([Math]::Round($totalDuration, 2))ms" -Level Info
    Write-Log "  Avg Duration: $([Math]::Round($avgDuration, 2))ms" -Level Info
    Write-Log "  Min Duration: $([Math]::Round($minDuration, 2))ms" -Level Info
    Write-Log "  Max Duration: $([Math]::Round($maxDuration, 2))ms" -Level Info
    Write-Log "  Requests/sec: $([Math]::Round($Count / ($totalDuration / 1000), 2))" -Level Info

    $Script:Results.Tests += @{
        Name = "Concurrent Requests - $Count users"
        TotalDuration = $totalDuration
        AverageDuration = $avgDuration
        MinDuration = $minDuration
        MaxDuration = $maxDuration
        Successful = $successful
        Failed = $failed
        RequestsPerSecond = $Count / ($totalDuration / 1000)
        Timestamp = Get-Date
    }
}

function Test-MemoryUsage {
    Write-Log "=== Testing Memory Usage ===" -Level Info

    try {
        # Get Django process
        $djangoProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*manage.py*runserver*" }

        if ($djangoProcess) {
            $memoryMB = [Math]::Round($djangoProcess.WorkingSet64 / 1MB, 2)
            Write-Log "Django process memory usage: $memoryMB MB" -Level Info

            $Script:Results.Tests += @{
                Name = "Memory Usage"
                MemoryMB = $memoryMB
                Timestamp = Get-Date
            }

            if ($memoryMB -gt 500) {
                Write-Log "WARNING: Memory usage is high (>500 MB)" -Level Warning
            }
        } else {
            Write-Log "Django process not found" -Level Warning
        }
    } catch {
        Write-Log "Failed to measure memory usage: $($_.Exception.Message)" -Level Error
    }
}

function Test-DatabaseQueryPerformance {
    Write-Log "=== Testing Database Query Performance ===" -Level Info

    # Test various API endpoints that hit the database
    $endpoints = @(
        @{ Name = "List Clients"; Path = "/api/clients/"; Method = "GET" },
        @{ Name = "List Reports"; Path = "/api/reports/"; Method = "GET" },
        @{ Name = "Dashboard Analytics"; Path = "/api/analytics/dashboard/"; Method = "GET" }
    )

    foreach ($endpoint in $endpoints) {
        Measure-ApiCall -Name $endpoint.Name -Url "$($Script:Config.ApiEndpoint)$($endpoint.Path)" -Method $endpoint.Method
    }
}

function Invoke-QuickTest {
    Write-Log "========================================" -Level Info
    Write-Log "Running QUICK Performance Tests" -Level Info
    Write-Log "========================================" -Level Info

    Test-HealthEndpoint
    Test-CSVProcessingPerformance -Rows 100
    Test-ConcurrentRequests -Count 5
    Test-MemoryUsage
}

function Invoke-StandardTest {
    Write-Log "========================================" -Level Info
    Write-Log "Running STANDARD Performance Tests" -Level Info
    Write-Log "========================================" -Level Info

    Test-HealthEndpoint
    Test-CSVProcessingPerformance -Rows 100
    Test-CSVProcessingPerformance -Rows 500
    Test-ConcurrentRequests -Count 10
    Test-DatabaseQueryPerformance
    Test-MemoryUsage
}

function Invoke-LoadTest {
    Write-Log "========================================" -Level Info
    Write-Log "Running LOAD Performance Tests" -Level Info
    Write-Log "========================================" -Level Info

    Test-HealthEndpoint
    Test-CSVProcessingPerformance -Rows 100
    Test-CSVProcessingPerformance -Rows 500
    Test-CSVProcessingPerformance -Rows 1000
    Test-ConcurrentRequests -Count 25
    Test-ConcurrentRequests -Count 50
    Test-DatabaseQueryPerformance
    Test-MemoryUsage
}

function Invoke-StressTest {
    Write-Log "========================================" -Level Info
    Write-Log "Running STRESS Performance Tests" -Level Info
    Write-Log "========================================" -Level Info

    Test-HealthEndpoint
    Test-CSVProcessingPerformance -Rows 1000
    Test-CSVProcessingPerformance -Rows 5000
    Test-ConcurrentRequests -Count 50
    Test-ConcurrentRequests -Count 100
    Test-DatabaseQueryPerformance
    Test-MemoryUsage
}

function New-TestReport {
    Write-Log "========================================" -Level Info
    Write-Log "Generating Test Report" -Level Info
    Write-Log "========================================" -Level Info

    $Script:Results.EndTime = Get-Date
    $Script:Results.TotalDuration = ($Script:Results.EndTime - $Script:Results.StartTime).TotalSeconds

    # Calculate summary statistics
    $allTests = $Script:Results.Tests
    $successfulTests = ($allTests | Where-Object { $_.Success -eq $true }).Count
    $failedTests = ($allTests | Where-Object { $_.Success -eq $false }).Count

    $avgDuration = ($allTests | Where-Object { $_.Duration } | Measure-Object -Property Duration -Average).Average

    $Script:Results.Summary = @{
        TotalTests = $allTests.Count
        Successful = $successfulTests
        Failed = $failedTests
        SuccessRate = if ($allTests.Count -gt 0) { ($successfulTests / $allTests.Count) * 100 } else { 0 }
        AverageDuration = $avgDuration
        TotalDurationSeconds = $Script:Results.TotalDuration
    }

    # Save to JSON
    $Script:Results | ConvertTo-Json -Depth 10 | Out-File -FilePath $Script:Config.ResultsFile -Encoding UTF8

    # Print summary
    Write-Log "" -Level Info
    Write-Log "========================================" -Level Success
    Write-Log "TEST SUMMARY" -Level Success
    Write-Log "========================================" -Level Success
    Write-Log "Test Type: $TestType" -Level Info
    Write-Log "Start Time: $($Script:Results.StartTime)" -Level Info
    Write-Log "End Time: $($Script:Results.EndTime)" -Level Info
    Write-Log "Total Duration: $([Math]::Round($Script:Results.TotalDuration, 2))s" -Level Info
    Write-Log "" -Level Info
    Write-Log "Total Tests: $($Script:Results.Summary.TotalTests)" -Level Info
    Write-Log "Successful: $($Script:Results.Summary.Successful)" -Level Success
    Write-Log "Failed: $($Script:Results.Summary.Failed)" -Level $(if ($Script:Results.Summary.Failed -eq 0) { 'Success' } else { 'Error' })
    Write-Log "Success Rate: $([Math]::Round($Script:Results.Summary.SuccessRate, 2))%" -Level $(if ($Script:Results.Summary.SuccessRate -ge 95) { 'Success' } elseif ($Script:Results.Summary.SuccessRate -ge 80) { 'Warning' } else { 'Error' })
    Write-Log "Average Duration: $([Math]::Round($Script:Results.Summary.AverageDuration, 2))ms" -Level Info
    Write-Log "" -Level Info
    Write-Log "Results saved to: $($Script:Config.ResultsFile)" -Level Success
    Write-Log "Log saved to: $($Script:Config.LogFile)" -Level Success
    Write-Log "========================================" -Level Success
}

#endregion

#region Main Execution

try {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   Azure Advisor Reports - Performance Testing        ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        Write-Log "Prerequisites check failed. Exiting." -Level Error
        exit 1
    }

    Write-Host ""

    # Run tests based on type
    switch ($TestType) {
        'Quick'    { Invoke-QuickTest }
        'Standard' { Invoke-StandardTest }
        'Load'     { Invoke-LoadTest }
        'Stress'   { Invoke-StressTest }
        'All'      {
            Invoke-QuickTest
            Write-Host ""
            Invoke-StandardTest
            Write-Host ""
            Invoke-LoadTest
            Write-Host ""
            Invoke-StressTest
        }
    }

    Write-Host ""

    # Generate report
    New-TestReport

    Write-Host ""
    Write-Log "Performance testing completed successfully!" -Level Success

} catch {
    Write-Log "Performance testing failed: $($_.Exception.Message)" -Level Error
    Write-Log "Stack trace: $($_.ScriptStackTrace)" -Level Error
    exit 1
}

#endregion
