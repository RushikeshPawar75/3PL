# Copyright (c) 2023, Dexciss Technology Pvt Ltd and contributors
# For license information, please see license.txt
import frappe
import pyotp
from frappe import _, sendmail


@frappe.whitelist()
def send_otp(docname):
    # Retrieve the customer record
    print('&&&&&&&&&&& docname ',docname)
    customer = frappe.get_doc("Customer", docname)
    if not customer:
        frappe.throw("Customer not found.")

    # Get the customer's email address
    email_id = customer.email_id

    # Get the customer's mobile number
    mobile_no = customer.mobile_no

    # Generate a new TOTP secret
    totp_secret = pyotp.random_base32()

    # Create a TOTP object using the secret
    totp = pyotp.TOTP(totp_secret)

    # Generate the OTP
    otp = totp.now()

    # Send the OTP via email if email_id is available
    if email_id:
        msg = f"Dear {customer.customer_name},\n\n"
        msg += f"Your verification code is: {otp}\n\n"
        msg += "This is a system-generated email. Please do not reply."

        sendmail(
            recipients=email_id,
            subject=_("Customer Verification OTP"),
            message=msg
        )

    # Send the OTP via SMS if mobile_no is available and SMS gateway URL is set
    if mobile_no and frappe.db.get_single_value("SMS Settings", "sms_gateway_url"):
        send_token_via_sms(totp_secret, otp, mobile_no)

    # If both email and SMS options are not available, raise an error
    if not email_id and (not mobile_no or not frappe.db.get_single_value("SMS Settings", "sms_gateway_url")):
        frappe.throw("OTP sending options are not available. Please configure email or SMS settings.")
    print("Generated otp:--------->", otp)
    print("MSG:------->",msg)
    return otp


def send_token_via_sms(otp_secret, token, phone_no):
    """Send token as SMS to user."""
    try:
        from frappe.core.doctype.sms_settings.sms_settings import send_request
    except Exception:
        return False

    if not phone_no:
        return False

    ss = frappe.get_doc("SMS Settings", "SMS Settings")
    if not ss.sms_gateway_url:
        return False

    hotp = pyotp.HOTP(otp_secret)
    otp_message = f"Your verification code is: {hotp.at(int(token))}"
    args = {ss.message_parameter: otp_message}

    for d in ss.get("parameters"):
        args[d.parameter] = d.value

    args[ss.receiver_parameter] = phone_no

    sms_args = {"params": args, "gateway_url": ss.sms_gateway_url, "use_post": ss.use_post}
    frappe.enqueue(
        method=send_request,
        queue="short",
        timeout=300,
        event=None,
        is_async=True,
        job_name=None,
        now=False,
        **sms_args,
    )
    return True
