#!/bin/bash
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell -c 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username="admin").exists() or User.objects.create_superuser("admin", "admin@example.com", "admin123")'
python manage.py shell -c 'from basic_app.models import DoctorProfile; DoctorProfile.objects.get_or_create(full_name="Dr. John Doe", defaults={"phone_number": "1234567890", "speciality": "General", "qualification": "MD", "location": "vellore", "hospital_name": "Care Hospital", "doctor_username": "doctor1"})'