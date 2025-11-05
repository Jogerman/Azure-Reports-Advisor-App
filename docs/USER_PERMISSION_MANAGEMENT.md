# User Permission Management Guide

This guide explains how to easily manage users and their permissions in the Azure Advisor Reports platform.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Role-Based Access Control](#role-based-access-control)
3. [Creating Users](#creating-users)
4. [Managing Permissions](#managing-permissions)
5. [Django Admin Interface](#django-admin-interface)
6. [Production Deployment](#production-deployment)

## Quick Start

### Step 1: Initialize Permission Groups (One-time setup)

Before creating users, initialize the permission groups:

```bash
# On Azure (via Azure Container Apps console or CLI)
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py init_permissions"

# Or via Docker exec if running locally
docker exec -it <container-name> python manage.py init_permissions
```

This creates four permission groups:
- **Administrator** - Full system access
- **Manager** - Manage clients, reports, and users
- **Analyst** - Create reports and manage clients
- **Viewer** - Read-only access

### Step 2: Create Users

Use the `create_user` management command to easily create users with roles:

```bash
# Create an Admin user
python manage.py create_user \
  --email admin@company.com \
  --password SecurePassword123! \
  --first-name Admin \
  --last-name User \
  --role admin \
  --superuser \
  --staff

# Create a Manager
python manage.py create_user \
  --email manager@company.com \
  --password SecurePassword123! \
  --first-name Jane \
  --last-name Manager \
  --role manager \
  --staff \
  --job-title "Account Manager" \
  --department "Client Services"

# Create an Analyst
python manage.py create_user \
  --email analyst@company.com \
  --password SecurePassword123! \
  --first-name John \
  --last-name Analyst \
  --role analyst \
  --job-title "Data Analyst"

# Create a Viewer (read-only)
python manage.py create_user \
  --email viewer@company.com \
  --password SecurePassword123! \
  --first-name Sarah \
  --last-name Viewer \
  --role viewer
```

## Role-Based Access Control

The platform uses a 4-tier role system:

### 1. Administrator (admin)
**Full system access - highest privilege level**

Permissions:
- ✅ All permissions across all modules
- ✅ Manage users (create, edit, delete)
- ✅ Manage clients (create, edit, delete)
- ✅ Manage reports (create, edit, delete)
- ✅ Access Django admin
- ✅ View analytics and system logs

Best for:
- System administrators
- IT managers
- Platform owners

---

### 2. Manager (manager)
**Manage clients, reports, and team members**

Permissions:
- ✅ View, create, and edit users (cannot delete)
- ✅ Full access to clients (create, edit, delete)
- ✅ Full access to reports (create, edit, delete)
- ✅ View and manage analytics
- ❌ Cannot delete users
- ❌ Cannot modify system settings

Best for:
- Account managers
- Team leads
- Client relationship managers

---

### 3. Analyst (analyst)
**Create reports and manage client data**

Permissions:
- ✅ View users (read-only)
- ✅ Create and edit clients
- ✅ Create and edit reports
- ✅ View analytics (read-only)
- ❌ Cannot delete clients
- ❌ Cannot manage users
- ❌ Cannot access admin panel

Best for:
- Data analysts
- Report generators
- Technical consultants

---

### 4. Viewer (viewer)
**Read-only access to reports and client data**

Permissions:
- ✅ View clients (read-only)
- ✅ View reports (read-only)
- ✅ View analytics (read-only)
- ❌ Cannot create or edit anything
- ❌ Cannot view users
- ❌ Cannot access admin panel

Best for:
- Stakeholders
- Executives
- External auditors
- Read-only consultants

## Creating Users

### Command-Line (Recommended for Production)

The `create_user` command automatically:
- Creates the user account
- Assigns the specified role
- Adds them to the appropriate permission group
- Sets up profile information

**Required Parameters:**
```bash
--email          # User's email address (used for login)
--password       # User's password
--first-name     # User's first name
--last-name      # User's last name
```

**Optional Parameters:**
```bash
--role           # User role: admin, manager, analyst, viewer (default: analyst)
--job-title      # Job title
--department     # Department name
--phone          # Phone number
--staff          # Grant Django admin access (flag)
--superuser      # Make user a superuser (flag)
```

**Examples:**

```bash
# Minimal user creation
python manage.py create_user \
  --email user@example.com \
  --password Pass123! \
  --first-name John \
  --last-name Doe

# Full user with all details
python manage.py create_user \
  --email john.manager@company.com \
  --password SecurePass123! \
  --first-name John \
  --last-name Manager \
  --role manager \
  --staff \
  --job-title "Senior Account Manager" \
  --department "Enterprise Solutions" \
  --phone "+1-555-0100"
```

### Django Admin Interface

You can also create users through the Django admin panel:

1. Navigate to `/admin/`
2. Click on "Users" → "Add User"
3. Fill in the required information
4. Select the appropriate **Role** from the dropdown
5. Manually add to the matching permission **Group**
6. Save

## Managing Permissions

### Bulk Permission Management (Django Admin)

The Django admin interface includes powerful bulk actions:

1. Navigate to `/admin/authentication/user/`
2. Select multiple users using checkboxes
3. Choose an action from the "Action" dropdown:

**Available Bulk Actions:**
- **Assign Administrator role** - Grant full access
- **Assign Manager role** - Grant management permissions
- **Assign Analyst role** - Grant analyst permissions
- **Assign Viewer role** - Grant read-only access
- **Activate selected users** - Enable user accounts
- **Deactivate selected users** - Disable user accounts
- **Grant Django admin access** - Allow access to admin panel
- **Revoke Django admin access** - Remove admin panel access

4. Click "Go" to apply the action

This makes it very easy to manage permissions for multiple users at once!

### Individual Permission Management

To modify a single user's permissions:

1. Go to `/admin/authentication/user/`
2. Click on the user you want to modify
3. Update the **Role** field
4. Update the **Groups** field to match the role:
   - admin → Administrator
   - manager → Manager
   - analyst → Analyst
   - viewer → Viewer
5. Toggle **is_staff** if they need Django admin access
6. Toggle **is_active** to enable/disable the account
7. Click "Save"

## Production Deployment

### Running Commands on Azure Container Apps

To run management commands in production:

```bash
# Initialize permissions (one-time setup)
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py init_permissions"

# Create a user
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py create_user --email user@example.com --password Pass123! --first-name John --last-name Doe --role manager --staff"
```

### Using the Superuser Command (Alternative)

If you prefer the original superuser command:

```bash
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py createsuperuser_auto --email admin@company.com --password Admin123! --first-name Admin --last-name User"
```

## Permission Matrix

| Feature | Administrator | Manager | Analyst | Viewer |
|---------|--------------|---------|---------|--------|
| **Users** |
| View users | ✅ | ✅ | ✅ | ❌ |
| Create users | ✅ | ✅ | ❌ | ❌ |
| Edit users | ✅ | ✅ | ❌ | ❌ |
| Delete users | ✅ | ❌ | ❌ | ❌ |
| **Clients** |
| View clients | ✅ | ✅ | ✅ | ✅ |
| Create clients | ✅ | ✅ | ✅ | ❌ |
| Edit clients | ✅ | ✅ | ✅ | ❌ |
| Delete clients | ✅ | ✅ | ❌ | ❌ |
| **Reports** |
| View reports | ✅ | ✅ | ✅ | ✅ |
| Create reports | ✅ | ✅ | ✅ | ❌ |
| Edit reports | ✅ | ✅ | ✅ | ❌ |
| Delete reports | ✅ | ✅ | ❌ | ❌ |
| **Analytics** |
| View analytics | ✅ | ✅ | ✅ | ✅ |
| Create analytics | ✅ | ✅ | ❌ | ❌ |
| Edit analytics | ✅ | ✅ | ❌ | ❌ |
| **Admin Panel** |
| Access admin | ✅* | Optional** | ❌ | ❌ |

\* Administrators always have admin access
\** Managers can be granted admin access using `--staff` flag

## Troubleshooting

### Permission groups not found

If you see this error when creating users:
```
Warning: Permission group "Manager" not found.
```

**Solution:** Run the init_permissions command:
```bash
python manage.py init_permissions
```

### User cannot access Django admin

**Check:**
1. Is the user's `is_staff` flag set to True?
2. Is the user's `is_active` flag set to True?
3. Does the user have the appropriate role?

**Solution:**
```bash
# Grant admin access via command
az containerapp exec \
  --name advisor-reports-backend \
  --resource-group rg-azure-advisor-app \
  --command "python manage.py shell -c \"from authentication.models import User; u = User.objects.get(email='user@example.com'); u.is_staff = True; u.save()\""
```

### Updating existing users' permissions

To update permissions for existing users, use the Django admin bulk actions:

1. Go to `/admin/authentication/user/`
2. Select the users
3. Choose "Assign [Role] role" action
4. Click "Go"

Or use Django shell:
```python
from authentication.models import User
from django.contrib.auth.models import Group

# Get the user
user = User.objects.get(email='user@example.com')

# Update role
user.role = 'manager'
user.save()

# Update permission group
user.groups.clear()
user.groups.add(Group.objects.get(name='Manager'))
```

## Best Practices

1. **Use the principle of least privilege** - Start users with minimal access (viewer/analyst) and grant more as needed

2. **Regularly audit user permissions** - Review user list monthly to ensure appropriate access levels

3. **Deactivate instead of delete** - When users leave, set `is_active=False` instead of deleting to preserve audit trails

4. **Use descriptive job titles and departments** - This helps identify users and their responsibilities

5. **Enable admin access only when needed** - Not all managers need Django admin access

6. **Use strong passwords** - Enforce complex passwords in production

7. **Document permission changes** - Keep a log of who was granted what access and when

## Quick Reference Commands

```bash
# Initialize permission groups (one-time)
python manage.py init_permissions

# Create admin user
python manage.py create_user --email admin@example.com --password Pass123! --first-name Admin --last-name User --role admin --superuser --staff

# Create manager with admin access
python manage.py create_user --email manager@example.com --password Pass123! --first-name Jane --last-name Doe --role manager --staff

# Create analyst (no admin access)
python manage.py create_user --email analyst@example.com --password Pass123! --first-name John --last-name Smith --role analyst

# Create viewer (read-only)
python manage.py create_user --email viewer@example.com --password Pass123! --first-name Sarah --last-name Jones --role viewer

# List all users
python manage.py shell -c "from authentication.models import User; [print(f'{u.email} - {u.get_role_display()}') for u in User.objects.all()]"
```

## Support

For issues or questions about user permission management:
1. Check this guide first
2. Review Django admin panel settings
3. Check application logs
4. Contact system administrator
