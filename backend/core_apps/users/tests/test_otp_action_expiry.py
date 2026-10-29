"""Mail copy uses the saved action deadline; ordinary verification is unchanged."""

import logging
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.utils import timezone, translation
from core_apps.users.services import otp_service


@pytest.mark.parametrize("language", ["en", "ar"])
def test_ordinary_verification_mail_keeps_existing_ten_minute_copy(language, settings, monkeypatch, mailoutbox):
    settings.SITE_NAME = "Sukoon"
    monkeypatch.setattr(otp_service, "OTP_EXPIRATION_SECONDS", 600)
    with translation.override(language):
        assert otp_service.send_otp_email("ordinary@example.test", "739251", user_name="Test")
    mail = mailoutbox[0]
    if language == "ar":
        assert mail.subject == "[Sukoon] رمز التحقق من البريد الإلكتروني"
        assert mail.body == "رمز التحقق الخاص بك: 739251\n\nتنتهي صلاحيته خلال 10 دقائق.\nإذا لم تطلب هذا الرمز، تجاهل الرسالة."
    else:
        assert mail.subject == "[Sukoon] Verify Your Email - OTP"
        assert mail.body == (
            "Hello Test,\n\nYour verification code is: 739251\n\n"
            "This code will expire in 10 minutes.\n"
            "If you did not request this verification, please ignore this email.\n\n"
            "Best regards,\nThe Sukoon Team"
        )


@pytest.mark.parametrize("language", ["en", "ar"])
@pytest.mark.parametrize("seconds,expected", [
    (1, "2026-10-30 12:00:01 (UTC+02:00)"),
    (120, "2026-10-30 12:02:00 (UTC+02:00)"),
    (300, "2026-10-30 12:05:00 (UTC+02:00)"),
])
def test_action_mail_uses_exact_saved_deadline_not_email_ttl(language, seconds, expected, mailoutbox):
    expiry = datetime(2026, 10, 30, 10, tzinfo=dt_timezone.utc) + timedelta(seconds=seconds)
    with translation.override(language), timezone.override("America/Los_Angeles"):
        assert otp_service.send_otp_email("actor@example.test", "739251", action_expires_at=expiry)
    mail = mailoutbox[0]
    assert expected in mail.body
    assert "10 minutes" not in mail.body and "10 دقائق" not in mail.body
    assert "five minutes" not in mail.body and "خمس دقائق" not in mail.body
    assert ("للعملية المطلوبة فقط" if language == "ar" else "requested action only") in mail.body
    assert ("بتوقيت القاهرة" if language == "ar" else "Cairo time") in mail.body
    assert mail.to == ["actor@example.test"] and "739251" in mail.body


@pytest.mark.parametrize("instant,expected", [
    (datetime(2026, 10, 29, 20, 30, tzinfo=dt_timezone.utc), "2026-10-29 23:30:00 (UTC+03:00)"),
    (datetime(2026, 10, 29, 21, 30, tzinfo=dt_timezone.utc), "2026-10-29 23:30:00 (UTC+02:00)"),
    (datetime(2026, 4, 23, 22, tzinfo=dt_timezone.utc), "2026-04-24 01:00:00 (UTC+03:00)"),
])
def test_cairo_transition_deadlines_are_unambiguous(instant, expected, mailoutbox):
    with translation.override("en"):
        assert otp_service.send_otp_email("actor@example.test", "739251", action_expires_at=instant)
    assert expected in mailoutbox[0].body


def test_delayed_delivery_does_not_move_saved_action_deadline(mailoutbox):
    expiry = datetime(2026, 10, 30, 10, 5, tzinfo=dt_timezone.utc)
    with translation.override("en"), patch.object(timezone, "now", return_value=expiry + timedelta(hours=1)):
        assert otp_service.send_otp_email("actor@example.test", "739251", action_expires_at=expiry)
    assert "2026-10-30 12:05:00 (UTC+02:00)" in mailoutbox[0].body


def test_action_mail_failure_does_not_log_recipient_code_or_exception_message(caplog, mailoutbox):
    recipient, code = "private-actor@example.test", "739251"
    with caplog.at_level(logging.INFO), patch.object(otp_service, "send_mail", side_effect=RuntimeError(f"{recipient} {code}")):
        assert not otp_service.send_otp_email(recipient, code, action_expires_at=datetime(2026, 10, 30, 10, tzinfo=dt_timezone.utc))
    assert recipient not in caplog.text and code not in caplog.text and not mailoutbox


def test_naive_action_deadline_is_not_silently_assigned_an_offset(mailoutbox):
    with pytest.raises(ValueError):
        otp_service.send_otp_email("actor@example.test", "739251", action_expires_at=datetime(2026, 10, 30, 10))
    assert not mailoutbox
