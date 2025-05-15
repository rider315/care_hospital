from django.shortcuts import render
from django.urls import reverse
from django.views.generic import CreateView
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import io
from xhtml2pdf import pisa
from django.template.loader import get_template
from basic_app.form import *
from basic_app import models
from basic_app.models import *
from basic_app.diet_recommender import *
# from basic_app.whatsapp import send_message
import pickle
import joblib
import csv

# Create your views here.

def index(request):
    return render(request, 'basic_app/index.html')

def register(request):
    return render(request, 'basic_app/register.html')

class patient_reg(CreateView):
    model = User
    form_class = PatientSignUpForm
    template_name = 'basic_app/patient_reg.html'

    def form_valid(self, form):
        user = form.save()
        return HttpResponseRedirect(reverse('login'))

class doctor_reg(CreateView):
    model = User
    form_class = DoctorSignUpForm
    template_name = 'basic_app/doctor_reg.html'

    def form_valid(self, form):
        user = form.save()
        return HttpResponseRedirect(reverse('login'))

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active and user.is_doctor:
                login(request, user)
                return HttpResponseRedirect(reverse('doctor_dashboard'))
            elif user.is_active and user.is_patient:
                login(request, user)
                return HttpResponseRedirect(reverse('patient_dashboard'))
            else:
                return HttpResponse("ACCOUNT NOT ACTIVE")
        else:
            messages.error(request, "Username or Password incorrect!")
            return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'basic_app/login.html')

@login_required
def patient_dashboard(request):
    docname = DoctorProfile.objects.all()
    delapp = Appointments.objects.all()
    app = Appointments.objects.filter(patient_username=request.user.username)
    finddoctor = None
    pres = Prescription.objects.filter(patient_username=request.user.username)

    if request.method == 'POST':
        print(request.POST)  # Debug POST data
        if 'appointment' in request.POST:
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            phone_number = request.POST.get('phone_number')
            doctor = request.POST.get('doctor')
            message = request.POST.get('message')
            time = request.POST.get('time')
            date = request.POST.get('date')
            patient_username = request.user.username

            # Validate required fields
            required_fields = {
                'first_name': first_name,
                'last_name': last_name,
                'phone_number': phone_number,
                'doctor': doctor,
                'message': message,
                'time': time,
                'date': date
            }
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                messages.error(request, f"Please fill in all required fields: {', '.join(missing_fields).replace('_', ' ').title()}")
                return HttpResponseRedirect(reverse('patient_dashboard'))

            # Find the doctor's profile
            doc = DoctorProfile.objects.filter(full_name=doctor)
            if not doc.exists():
                messages.error(request, f"No doctor found with name: {doctor}")
                return HttpResponseRedirect(reverse('patient_dashboard'))

            doctor_username = doc.first().doctor_username
            booking_form = Appointments(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                doctor=doctor,
                message=message,
                time=time,
                date=date,
                patient_username=patient_username,
                doctor_username=doctor_username
            )
            try:
                booking_form.save()
                # send_message(f'Your appointment has been scheduled with {doctor} on {date} at {time}')
                messages.success(request, f"Appointment with {doctor} scheduled successfully!")
                return HttpResponseRedirect(reverse('patient_dashboard'))
            except Exception as e:
                messages.error(request, "Failed to schedule appointment. Please try again.")
                print(f"Error saving appointment: {e}")

        elif 'finddoc' in request.POST:
            location = request.POST.get('location')
            speciality = request.POST.get('speciality')
            finddoctor = DoctorProfile.objects.filter(location=location, speciality=speciality)
            if not finddoctor.exists():
                finddoctor = None
                messages.info(request, "No doctors found matching your criteria.")

    context = {'app': app, 'docname': docname, 'finddoctor': finddoctor, 'delapp': delapp, 'pres': pres}
    return render(request, 'basic_app/patient_dashboard.html', context)

@login_required
def editApp(request, pk):
    docname = DoctorProfile.objects.all()
    editapp = Appointments.objects.get(id=pk)

    if request.method == 'POST':
        print(request.POST)  # Debug POST data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        doctor = request.POST.get('doctor')
        message = request.POST.get('message')
        time = request.POST.get('time')
        date = request.POST.get('date')

        # Validate required fields
        required_fields = {
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': phone_number,
            'doctor': doctor,
            'message': message,
            'time': time,
            'date': date
        }
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            messages.error(request, f"Please fill in all required fields: {', '.join(missing_fields).replace('_', ' ').title()}")
            return HttpResponseRedirect(reverse('patient_dashboard'))

        Appointments.objects.filter(id=pk).update(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            doctor=doctor,
            message=message,
            time=time,
            date=date
        )
        messages.success(request, "Appointment updated successfully!")
        return HttpResponseRedirect(reverse('patient_dashboard'))

    context = {'editapp': editapp, 'docname': docname}
    return render(request, 'basic_app/editapp.html', context)

@login_required
def deleteApp(request, pk):
    delapp = Appointments.objects.get(id=pk)
    delapp.delete()
    messages.success(request, "Appointment deleted successfully!")
    return HttpResponseRedirect(reverse('patient_dashboard'))

@login_required
def doctor_dashboard(request):
    docapp = Appointments.objects.filter(doctor_username=request.user.username)
    cnt = docapp.count()
    pres = []
    if docapp:
        pres = Prescription.objects.filter(doctorName=docapp[0].doctor)

    app = []
    pre = []
    for a in docapp:
        v = 0
        for p in pres:
            if a.id == p.patientid:
                v = 1
                pre.append(a.id)
        if v == 0:
            app.append(a.id)

    profile = DoctorProfile.objects.filter(doctor_username=request.user.username).first()

    context = {'docapp': docapp, 'cnt': cnt, 'pres': pres, 'profile': profile, 'app': app, 'pre': pre}

    if request.method == "POST":
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        speciality = request.POST.get('speciality')
        qualification = request.POST.get('qualification')
        location = request.POST.get('location')
        hospital_name = request.POST.get('hospital_name')
        doctor_username = request.user.username

        try:
            if not profile:
                profile_form = DoctorProfile(
                    full_name=full_name,
                    phone_number=phone_number,
                    speciality=speciality,
                    qualification=qualification,
                    location=location,
                    hospital_name=hospital_name,
                    doctor_username=doctor_username
                )
                profile_form.save()
                messages.success(request, "Doctor profile created successfully!")
            else:
                DoctorProfile.objects.filter(id=profile.id).update(
                    full_name=full_name,
                    phone_number=phone_number,
                    speciality=speciality,
                    qualification=qualification,
                    location=location,
                    hospital_name=hospital_name,
                    doctor_username=doctor_username
                )
                messages.success(request, "Doctor profile updated successfully!")
            return HttpResponseRedirect(reverse('doctor_dashboard'))
        except Exception as e:
            messages.error(request, "Failed to save profile. Please try again.")
            print(f"Error saving profile: {e}")

    return render(request, 'basic_app/doctor_dashboard.html', context)

@login_required
def delDocApp(request, pk):
    deldocapp = Appointments.objects.get(id=pk)
    deldocapp.delete()
    messages.success(request, "Appointment deleted successfully!")
    return HttpResponseRedirect(reverse('doctor_dashboard'))

def prescription(request, pk):
    appDetails = Appointments.objects.get(id=pk)
    context = {
        'patientid': pk,
        'patientName': (appDetails.first_name + ' ' + appDetails.last_name),
        'doctorName': appDetails.doctor,
        'appdate': appDetails.date,
        'phone': appDetails.phone_number
    }

    if request.method == 'POST':
        context2 = {
            'symptom': request.POST['symptom'],
            'medicine': request.POST['medicine'],
            'doctorFee': request.POST['doctorFee'],
            'otherCharges': request.POST['otherCharges'],
            'medicineFee': request.POST['medicineFee'],
            'total': (int(request.POST['doctorFee']) + int(request.POST['medicineFee']) + int(request.POST['otherCharges']))
        }
        context.update(context2)

        pres = Prescription(
            patientid=pk,
            patient_username=appDetails.patient_username,
            patientName=(appDetails.first_name + ' ' + appDetails.last_name),
            patientPhone=appDetails.phone_number,
            appointmentDate=appDetails.date,
            doctorName=appDetails.doctor,
            symptom=request.POST['symptom'],
            medicine=request.POST['medicine'],
            doctorFee=request.POST['doctorFee'],
            medicineFee=request.POST['medicineFee'],
            otherCharges=request.POST['otherCharges'],
            total=(int(request.POST['doctorFee']) + int(request.POST['medicineFee']) + int(request.POST['otherCharges']))
        )
        pres.save()

        message_to_send = request.POST['medicine'].replace(',', '\n')
        # print(send_message(f'Your prescription of medicines is as follows:\n{message_to_send}', appDetails.phone_number))
        return render(request, 'basic_app/finalprescription.html', context)

    return render(request, 'basic_app/prescription.html', context)

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse(pdf, content_type='application/pdf')

def download_pdf_view(request, pk):
    pres = Prescription.objects.filter(patientid=pk).order_by('-id')[:1]
    if not pres.exists():
        return HttpResponse("No prescription found.", status=404)
    dict = {
        'patientName': pres[0].patientName,
        'doctorName': pres[0].doctorName,
        'patientPhone': pres[0].patientPhone,
        'appdate': pres[0].appointmentDate,
        'symptom': pres[0].symptom,
        'medicine': pres[0].medicine,
        'medicineFee': pres[0].medicineFee,
        'doctorFee': pres[0].doctorFee,
        'otherCharges': pres[0].otherCharges,
        'total': pres[0].total,
    }
    return render_to_pdf('basic_app/download.html', dict)

def download_patient(request, pk):
    pres = Prescription.objects.get(id=pk)
    dict = {
        'patientName': pres.patientName,
        'doctorName': pres.doctorName,
        'patientPhone': pres.patientPhone,
        'appdate': pres.appointmentDate,
        'symptom': pres.symptom,
        'medicine': pres.medicine,
        'medicineFee': pres.medicineFee,
        'doctorFee': pres.doctorFee,
        'otherCharges': pres.otherCharges,
        'total': pres.total,
    }
    return render_to_pdf('basic_app/download.html', dict)

def download_doctor(request, pk):
    pres = Prescription.objects.get(patientid=pk)
    dict = {
        'patientName': pres.patientName,
        'doctorName': pres.doctorName,
        'patientPhone': pres.patientPhone,
        'appdate': pres.appointmentDate,
        'symptom': pres.symptom,
        'medicine': pres.medicine,
        'medicineFee': pres.medicineFee,
        'doctorFee': pres.doctorFee,
        'otherCharges': pres.otherCharges,
        'total': pres.total,
    }
    return render_to_pdf('basic_app/download.html', dict)

def insurance(request):
    price = None
    insurance_plans = [
        ('Edelweiss Health Insurance', '2578+', 115.0, 'https://www.edelweissinsurance.com/health-insurance'),
        ('United India Health Insurance', '7000+', 110.95, 'https://uiic.co.in/product/health'),
        ('Oriental Health Insurance', '4300+', 108.8, 'https://orientalinsurance.org.in/health-products'),
        ('National Health Insurance', '6000+', 107.64, 'https://www.nhp.gov.in/national-health-insurance-schemes_pg'),
        ('New India Assurance Health Insurance', '3000+', 103.74, 'https://www.newindia.co.in'),
        ('IFFCO Tokio Health Insurance', '5000+', 102.0, 'https://www.iffcotokio.co.in/health-insurance'),
        ('Universal Sompo Health Insurance', '5000+', 92.0, 'https://www.universalsompo.com/health-insurance'),
        ('Bharti AXA Health Insurance', '4500+', 89.0, 'https://www.bharti-axagi.co.in/health-insurance'),
        ('Bajaj Allianz Health Insurance', '6500+', 85.0, 'https://www.bajajallianz.com/health/policy'),
        ('Liberty Health Insurance', '5000+', 82.0, 'https://www.libertyinsurance.in/health-insurance/')
    ]
    context = {'price': price, 'insurance_plans': insurance_plans}

    if request.method == 'POST':
        age = int(request.POST.get('age'))
        sex = int(request.POST.get('sex'))
        bmi = int(request.POST.get('bmi'))
        children = int(request.POST.get('children'))
        smoker = int(request.POST.get('smoker'))
        region = int(request.POST.get('region'))
        lgbm = joblib.load('files/lgbm_model.pkl')
        price = lgbm.predict([[age, sex, bmi, children, smoker, region]])
        context = {'price': int(price[0]), 'insurance_plans': insurance_plans}

    return render(request, 'basic_app/insurance.html', context)

def diet(request):
    bodytype = None
    food = None
    context = {'bodytype': bodytype, 'food': food}
    if request.method == 'POST':
        age = int(request.POST.get('age'))
        height = int(request.POST.get('height'))
        weight = int(request.POST.get('weight'))
        bmi = weight / ((height / 100) ** 2)
        if bmi < 18.5:
            bodytype = 'According to your BMI you are Underweight.'
            food = Weight_Gain(age, 1, weight, height)
        elif bmi < 25:
            bodytype = 'According to your BMI you are Healthy.'
            food = Healthy(age, 1, weight, height)
        else:
            bodytype = 'According to your BMI you are Overweight.'
            food = Weight_Loss(age, 1, weight, height)
        if len(food) > 7:
            food = food[:6]
        context = {'bodytype': bodytype, 'food': food, 'bmi': bmi}
    return render(request, 'basic_app/diet.html', context)

def main(request):
    result = ""
    description = ""
    precaution = []
    medication = []
    if request.method == "POST":
        with open('files/prognosis.csv', 'r') as f:
            d_reader = csv.DictReader(f)
            headers = d_reader.fieldnames
        headers.remove(headers[132])
        all_symptoms = headers
        symptoms_experienced = request.POST.getlist('framework[]')
        for i in range(len(all_symptoms)):
            if all_symptoms[i] in symptoms_experienced:
                all_symptoms[i] = 1
            else:
                all_symptoms[i] = 0
        mdl = joblib.load('files/disease.pkl')
        prediction_result = mdl.predict([all_symptoms])
        result = ''.join(prediction_result)

        with open('files/symptom_Description.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == result:
                    description = row[1]

        with open('files/symptom_precaution.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == result:
                    for i in range(1, 5):
                        if row[i] != '':
                            precaution.append(row[i])

        with open('files/medicine.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if row[0] == result:
                    for i in range(1, 4):
                        if row[i] != '':
                            medication.append(row[i])

    context = {'text': result, 'des': description, 'pre': precaution, 'med': medication}
    return render(request, 'basic_app/main.html', context)

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))