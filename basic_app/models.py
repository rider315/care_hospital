from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

numeric = RegexValidator(r'^[0-9]*$', 'Only numeric characters are allowed.')

class User(AbstractUser):
    """Custom user model with doctor and patient roles."""
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=50, blank=True)

class Doctor(models.Model):
    """Doctor profile linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField(max_length=20, validators=[numeric])
    speciality = models.CharField(max_length=20)
    location = models.CharField(max_length=20, default="vellore")

    def __str__(self):
        return f"{self.user.username} (Doctor)"

class Patient(models.Model):
    """Patient profile linked to a User."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    phone_number = models.CharField(max_length=20, validators=[numeric])
    location = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.username} (Patient)"

class Appointments(models.Model):
    """Appointment details for a patient with a doctor."""
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, validators=[numeric])
    doctor = models.CharField(max_length=20)
    message = models.CharField(max_length=20)
    time = models.CharField(max_length=20)
    date = models.CharField(max_length=20)
    patient_username = models.CharField(max_length=20, default="", blank=True)
    doctor_username = models.CharField(max_length=20, default="", blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class DoctorProfile(models.Model):
    """Public profile for a doctor."""
    full_name = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)
    speciality = models.CharField(max_length=20)
    qualification = models.CharField(max_length=20)
    location = models.CharField(max_length=20)
    hospital_name = models.CharField(max_length=20)
    doctor_username = models.CharField(max_length=20, default="", blank=True)

    def __str__(self):
        return self.full_name

class Prescription(models.Model):
    """Prescription details for a patient."""
    patientid = models.PositiveIntegerField(null=True, blank=True)
    patient_username = models.CharField(max_length=20, default="", blank=True)
    patient_name = models.CharField(max_length=20)
    patient_phone = models.CharField(max_length=20)
    appointment_date = models.CharField(max_length=20)
    doctor_name = models.CharField(max_length=20)
    symptom = models.CharField(max_length=40)
    medicine = models.CharField(max_length=50)
    doctor_fee = models.PositiveIntegerField()
    medicine_fee = models.PositiveIntegerField()
    other_charges = models.PositiveIntegerField()
    total = models.PositiveIntegerField()

    def __str__(self):
        return self.patient_name