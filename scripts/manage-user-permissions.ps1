# ================================
# Manage User Permissions Script
# Azure Advisor Reports Platform
# ================================

param(
    [Parameter(Mandatory=$false)]
    [string]$Email,

    [Parameter(Mandatory=$false)]
    [ValidateSet('admin', 'analyst', 'viewer')]
    [string]$Role,

    [Parameter(Mandatory=$false)]
    [switch]$MakeAdmin,

    [Parameter(Mandatory=$false)]
    [switch]$RemoveAdmin,

    [Parameter(Mandatory=$false)]
    [switch]$List
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "User Permission Management Tool" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# List all users
if ($List) {
    Write-Host "Listing all users..." -ForegroundColor Yellow
    docker exec azure-advisor-backend python manage.py shell -c "
from apps.authentication.models import User
users = User.objects.all()
print('\n=== USERS IN SYSTEM ===\n')
for u in users:
    print(f'Email: {u.email}')
    print(f'  Role: {u.role}')
    print(f'  Staff: {u.is_staff}')
    print(f'  Superuser: {u.is_superuser}')
    print(f'  Azure ID: {u.azure_object_id or \"N/A\"}')
    print('-' * 50)
"
    exit
}

# Make user admin
if ($MakeAdmin -and $Email) {
    Write-Host "Granting admin permissions to: $Email" -ForegroundColor Yellow
    docker exec azure-advisor-backend python manage.py shell -c "
from apps.authentication.models import User
try:
    user = User.objects.get(email='$Email')
    user.is_staff = True
    user.is_superuser = True
    user.role = 'admin'
    user.save()
    print(f'✅ User {user.email} is now an admin')
except User.DoesNotExist:
    print(f'❌ User with email {Email} not found')
"
    exit
}

# Remove admin permissions
if ($RemoveAdmin -and $Email) {
    Write-Host "Removing admin permissions from: $Email" -ForegroundColor Yellow
    docker exec azure-advisor-backend python manage.py shell -c "
from apps.authentication.models import User
try:
    user = User.objects.get(email='$Email')
    user.is_staff = False
    user.is_superuser = False
    user.role = 'analyst'
    user.save()
    print(f'✅ Admin permissions removed from {user.email}')
except User.DoesNotExist:
    print(f'❌ User with email {Email} not found')
"
    exit
}

# Change user role
if ($Role -and $Email) {
    Write-Host "Changing role for: $Email to $Role" -ForegroundColor Yellow
    docker exec azure-advisor-backend python manage.py shell -c "
from apps.authentication.models import User
try:
    user = User.objects.get(email='$Email')
    user.role = '$Role'
    if '$Role' == 'admin':
        user.is_staff = True
        user.is_superuser = True
    user.save()
    print(f'✅ User {user.email} role changed to: $Role')
except User.DoesNotExist:
    print(f'❌ User with email {Email} not found')
"
    exit
}

# Show help if no parameters
Write-Host "Usage Examples:" -ForegroundColor Green
Write-Host ""
Write-Host "  List all users:" -ForegroundColor White
Write-Host "    .\manage-user-permissions.ps1 -List" -ForegroundColor Gray
Write-Host ""
Write-Host "  Make user admin:" -ForegroundColor White
Write-Host "    .\manage-user-permissions.ps1 -Email user@example.com -MakeAdmin" -ForegroundColor Gray
Write-Host ""
Write-Host "  Remove admin permissions:" -ForegroundColor White
Write-Host "    .\manage-user-permissions.ps1 -Email user@example.com -RemoveAdmin" -ForegroundColor Gray
Write-Host ""
Write-Host "  Change user role:" -ForegroundColor White
Write-Host "    .\manage-user-permissions.ps1 -Email user@example.com -Role analyst" -ForegroundColor Gray
Write-Host ""
Write-Host "Available Roles: admin, analyst, viewer" -ForegroundColor Yellow
Write-Host ""
