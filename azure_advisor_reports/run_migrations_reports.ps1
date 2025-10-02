# PowerShell script to create reports tables

$ErrorActionPreference = "Stop"

Write-Host "=== Creating Reports Tables ===" -ForegroundColor Cyan
Write-Host ""

# Create reports table
Write-Host "[1/4] Creating reports table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    created_by_id UUID REFERENCES auth_user_extended(id) ON DELETE SET NULL,
    report_type VARCHAR(20) NOT NULL,
    title VARCHAR(255),
    csv_file VARCHAR(500),
    html_file VARCHAR(500),
    pdf_file VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending',
    analysis_data JSONB DEFAULT '{}',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    csv_uploaded_at TIMESTAMP,
    processing_started_at TIMESTAMP,
    processing_completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@

Write-Host "[2/4] Creating indexes for reports table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS reports_client__80ebc7_idx ON reports (client_id, status);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS reports_report__ff8b25_idx ON reports (report_type);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS reports_created_c5f642_idx ON reports (created_at);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS reports_status_e83c1d_idx ON reports (status);"

# Create recommendations table
Write-Host "[3/4] Creating recommendations table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    category VARCHAR(30) NOT NULL,
    business_impact VARCHAR(10),
    recommendation TEXT NOT NULL,
    subscription_id VARCHAR(255),
    subscription_name VARCHAR(255),
    resource_group VARCHAR(255),
    resource_name VARCHAR(255),
    resource_type VARCHAR(255),
    potential_savings DECIMAL(12,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    potential_benefits TEXT,
    retirement_date DATE,
    retiring_feature VARCHAR(255),
    advisor_score_impact DECIMAL(5,2) DEFAULT 0,
    csv_row_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@

Write-Host "[4/4] Creating indexes for recommendations table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS recommendat_report__662bd5_idx ON recommendations (report_id, category);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS recommendat_busines_b0d8a4_idx ON recommendations (business_impact);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS recommendat_potenti_890ab6_idx ON recommendations (potential_savings);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS recommendat_subscri_ebc8e2_idx ON recommendations (subscription_id);"

# Create report_templates table
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS report_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    report_type VARCHAR(20) NOT NULL,
    html_template TEXT,
    css_styles TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by_id UUID REFERENCES auth_user_extended(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@

# Create report_shares table
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS report_shares (
    id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    shared_by_id UUID NOT NULL REFERENCES auth_user_extended(id) ON DELETE CASCADE,
    shared_with_email VARCHAR(254) NOT NULL,
    permission_level VARCHAR(20) DEFAULT 'view',
    access_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (report_id, shared_with_email)
);
"@

# Mark reports migration as applied
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "INSERT INTO django_migrations (app, name, applied) VALUES ('reports', '0001_initial', NOW()) ON CONFLICT DO NOTHING;"

Write-Host ""
Write-Host "=== Reports Tables Created Successfully ===" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying tables..." -ForegroundColor Cyan
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "\dt"

Write-Host ""
Write-Host "All Applied Migrations:" -ForegroundColor Cyan
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 15;"
