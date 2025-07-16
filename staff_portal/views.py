# nec_cybersec/views.py
from django.core.cache import cache
import pickle
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from .forms import StaffRegisterForm
from .models import CustomUser, Device, PendingAccess, UnauthorizedAttempt
import random, json
import face_recognition

otp_store = {}

@csrf_exempt
def device_verification_bridge(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode())
            bios = data.get("bios")
            baseboard = data.get("baseboard")
            username = data.get("username")

            if not bios or not baseboard or not username:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Check if device exists and belongs to user
            user = CustomUser.objects.filter(username=username).first()
            if not user:
                return JsonResponse({"error": "User not found."}, status=404)

            match = Device.objects.filter(
                registered_by=user,
                serial_bios=bios,
                serial_baseboard=baseboard
            ).exists()

            if match:
                # Store in session cache to confirm device was verified
                cache_key = f"device_verified_{username}"
                cache.set(cache_key, {
                    "username": username,
                    "bios": bios,
                    "baseboard": baseboard
                }, timeout=120)  # valid for 2 mins
                return JsonResponse({"status": "verified"})
            else:
                UnauthorizedAttempt.objects.create(
                    bios=bios,
                    baseboard=baseboard
                )
                return JsonResponse({"status": "unrecognized"}, status=403)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return HttpResponseForbidden()

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Save attempt
        PendingAccess.objects.create(username=username)
        request.session['pending_username'] = username

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

        # Check device verification from cache
        cache_key = f"device_verified_{username}"
        verified = cache.get(cache_key)

        if not verified or verified.get("username") != username:
            return render(request, 'wait_helper.html')  # still waiting

        # Passed device verification
        try:
            staff = CustomUser.objects.get(username=username)

            if not staff.is_active:
                return render(request, 'login.html', {'error': 'Account not active. Contact admin.'})

            # Check if device info matches
            device_match = Device.objects.filter(
                registered_by=staff,
                serial_bios=verified.get('bios'),
                serial_baseboard=verified.get('baseboard')
            ).exists()

            if not device_match:
                return render(request, 'login.html', {'error': 'Device not recognized. Please contact admin.'})

            # All passed – send OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['username'] = username
            print("OTP is:", otp)
            return redirect('otp')

        except CustomUser.DoesNotExist:
            return render(request, 'login.html', {'error': 'Unauthorized user. Registration required.'})

    return render(request, 'login.html')

def check_verification(request):
    username = request.session.get('pending_username')
    if not username:
        return JsonResponse({"verified": False})

    cache_key = f"device_verified_{username}"
    verified = cache.get(cache_key)

    if verified and verified.get('username') == username:
        # Generate OTP and set session once verification confirmed
        otp = str(random.randint(100000, 999999))
        request.session['otp'] = otp
        request.session['username'] = username
        print("OTP is:", otp)  # DEBUG

        return JsonResponse({
            "verified": True,
            "bios": verified.get('bios'),
            "baseboard": verified.get('baseboard'),
            "otp_generated": True  # you can add this flag if you want
        })

    return JsonResponse({"verified": False})

def otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')

        if entered_otp.strip() == str(stored_otp).strip():
            username = request.session.get('username')

            # Ensure device was verified
            cache_key = f"device_verified_{username}"
            verified = cache.get(cache_key)

            if not verified or verified.get('username') != username:
                return HttpResponse("Device not verified. Run helper app first.", status=403)

            user = CustomUser.objects.get(username=username)
            login(request, user)

            # ✅ Clean up now (after full success)
            cache.delete(cache_key)
            request.session.pop('otp', None)
            request.session.pop('device_verified', None)

            if user.is_superuser:
                return redirect('/admin/')
            else:
                return redirect('staff_dashboard')
        else:
            return render(request, 'otp.html', {'error': 'Invalid OTP'})

    return render(request, 'otp.html')

def register(request):
    if request.method == 'POST':
        form = StaffRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_admin = False
            user.save()
            return redirect('login')
    else:
        form = StaffRegisterForm()
    return render(request, 'register.html', {'form': form})

@login_required
def staff_dashboard(request):
    return render(request, 'staff_dashboard.html')

@login_required
def admin_panel(request):
    if not request.user.is_admin:
        return redirect('login')
    devices = Device.objects.all()
    attempts = UnauthorizedAttempt.objects.all()
    if request.method == 'POST':
        delete_id = request.POST.get('delete_device')
        if delete_id:
            Device.objects.filter(id=delete_id).delete()
    return render(request, 'admin_panel.html', {'devices': devices, 'attempts': attempts})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@csrf_exempt
def api_check_device(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            bios = data.get('bios')
            baseboard = data.get('baseboard')
            if Device.objects.filter(serial_bios=bios, serial_baseboard=baseboard).exists():
                return JsonResponse({'status': 'Access Granted'})
            else:
                UnauthorizedAttempt.objects.create(bios=bios, baseboard=baseboard)
                return JsonResponse({'status': 'Access Denied'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return HttpResponseForbidden()

def encode_face(image_file): 
    image = face_recognition.load_image_file(image_file)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        return pickle.dumps(encodings[0])  # serialize encoding
    else:
        return None

def register_view(request):
    if request.method == 'POST':
        # Get form data including photo
        photo_file = request.FILES.get('photo')
        username = request.POST.get('username')
        password = request.POST.get('password')

        if photo_file:
            face_encoding = encode_face(photo_file)
            if not face_encoding:
                return render(request, 'register.html', {'error': 'No face detected in photo.'})
        else:
            return render(request, 'register.html', {'error': 'Photo is required.'})

        # Create user and save encoding
        user = CustomUser.objects.create_user(username=username, password=password)
        user.photo = photo_file
        user.face_encoding = face_encoding
        user.save()

        return redirect('login')

    return render(request, 'register.html')

