#!/bin/sh
# Script para crear superusuario en Azure Container Apps

echo "Creando superusuario..."

python manage.py shell << EOF
from authentication.models import User
import os

email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
password = os.getenv('ADMIN_PASSWORD', 'changeme123')
first_name = os.getenv('ADMIN_FIRST_NAME', 'Admin')
last_name = os.getenv('ADMIN_LAST_NAME', 'User')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    print(f"✓ Superusuario creado: {email}")
else:
    print(f"✓ Superusuario ya existe: {email}")
EOF

echo "Proceso completado."
