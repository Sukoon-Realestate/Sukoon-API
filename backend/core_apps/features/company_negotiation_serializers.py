from rest_framework import serializers as s
from .company_serializers import StrictBody, CommandBody


class NegotiatedTerms(StrictBody):
    monthly_rent_minor = s.IntegerField(min_value=1, max_value=10**12)
    deposit_minor = s.IntegerField(min_value=0, max_value=10**12)
    starts_on = s.DateField()
    ends_on_exclusive = s.DateField()
    occupants = s.IntegerField(min_value=1, max_value=100000)
    included_services = s.ListField(child=s.CharField(max_length=500), max_length=50)
    excluded_services = s.ListField(child=s.CharField(max_length=500), max_length=50)


class StartTerms(CommandBody):
    terms = NegotiatedTerms()
    expires_at = s.DateTimeField()


class DecideTerms(CommandBody):
    terms_digest = s.CharField(max_length=64)
    reason = s.CharField(max_length=2000, allow_blank=True, default="")


class ReviseTerms(DecideTerms):
    terms = NegotiatedTerms()
