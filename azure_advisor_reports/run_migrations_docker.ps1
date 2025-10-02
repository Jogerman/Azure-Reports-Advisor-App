# PowerShell script to run migrations through Docker PostgreSQL
# This script executes Django migrations by directly applying SQL to the database

$ErrorActionPreference = "Stop"

Write-Host "=== Running Django Migrations via Docker ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Mark authentication migrations as applied
Write-Host "[1/5] Marking authentication migration 0002 as applied..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "INSERT INTO django_migrations (app, name, applied) VALUES ('authentication', '0002_user_role_user_auth_user_e_azure_o_ab0d80_idx_and_more', NOW()) ON CONFLICT DO NOTHING;"

# Step 2: Apply authentication migration SQL
Write-Host "[2/5] Applying authentication indexes..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS auth_user_e_azure_o_ab0d80_idx ON auth_user_extended (azure_object_id);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS auth_user_e_email_25b030_idx ON auth_user_extended (email);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS auth_user_e_role_7f68a6_idx ON auth_user_extended (role);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS auth_user_e_is_acti_768bce_idx ON auth_user_extended (is_active, role);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS auth_user_e_created_24e41e_idx ON auth_user_extended (created_at);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "ALTER TABLE auth_user_extended ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'analyst';"

# Step 3: Create clients tables
Write-Host "[3/5] Creating clients tables..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS clients (
    id UUID PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(50) DEFAULT 'other',
    contact_email VARCHAR(254),
    contact_phone VARCHAR(20),
    contact_person VARCHAR(255),
    azure_subscription_ids JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    contract_start_date DATE,
    contract_end_date DATE,
    billing_contact VARCHAR(254),
    account_manager_id UUID REFERENCES auth_user_extended(id) ON DELETE SET NULL,
    created_by_id UUID REFERENCES auth_user_extended(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@

docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS clients_company_570f91_idx ON clients (company_name);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS clients_status_98ee60_idx ON clients (status);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS clients_industr_cdecff_idx ON clients (industry);"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "CREATE INDEX IF NOT EXISTS clients_created_4c189f_idx ON clients (created_at);"

# Mark clients migrations as applied
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "INSERT INTO django_migrations (app, name, applied) VALUES ('clients', '0001_initial', NOW()) ON CONFLICT DO NOTHING;"
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "INSERT INTO django_migrations (app, name, applied) VALUES ('clients', '0002_initial', NOW()) ON CONFLICT DO NOTHING;"

# Step 4: Create client_contacts table
Write-Host "[4/5] Creating client_contacts table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS client_contacts (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(254) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(20) DEFAULT 'other',
    title VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (client_id, email)
);
"@

# Step 5: Create client_notes table
Write-Host "[5/5] Creating client_notes table..." -ForegroundColor Yellow
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c @"
CREATE TABLE IF NOT EXISTS client_notes (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    author_id UUID NOT NULL REFERENCES auth_user_extended(id) ON DELETE CASCADE,
    note_type VARCHAR(20) DEFAULT 'general',
    subject VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    related_report_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"@

Write-Host ""
Write-Host "=== Migration Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying tables..." -ForegroundColor Cyan
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "\dt"

Write-Host ""
Write-Host "Checking applied migrations..." -ForegroundColor Cyan
docker exec azure-advisor-postgres psql -U postgres -d azure_advisor_reports -c "SELECT app, name FROM django_migrations WHERE app IN ('authentication', 'clients', 'reports') ORDER BY applied DESC LIMIT 10;"
