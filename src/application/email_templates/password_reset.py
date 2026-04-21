PASSWORD_RESET_EMAIL_SUBJECT = "Reset Your Password - Cheatsheet App"

PASSWORD_RESET_EMAIL_TEMPLATE = """Hello, {display_name}!

We received a request to reset the password for your Cheatsheet App account.

To reset your password, click the link below:
{reset_url}

This link will expire in {expires_in_minutes} minutes.

If you did not request a password reset, please ignore this email.
Your password will remain unchanged and your account is secure.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For security reasons, this link can only be used once.

Need help? Contact us at {support_email}

Best regards,
The Cheatsheet App Team

---
This is an automated message. Please do not reply to this email.
"""
