from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_blood_match_email(donor, blood_request):
    context = {
        "donor_name": donor.user.get_full_name(),
        "patient_name": blood_request.patient_name,
        "blood_type": blood_request.required_blood_type,
        "hospital": blood_request.hospital.hospital_name,
    }

    html_message = render_to_string("email/blood_match.html", context)

    send_mail(
        subject=f"Blood Match Request - {blood_request.required_blood_type}",
        message="A new blood donation request matches your profile.",
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lifelink.com"),
        recipient_list=[donor.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_sms_alert(phone, message):
    try:
        from twilio.rest import Client

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone,
        )
        return True
    except Exception:
        return False