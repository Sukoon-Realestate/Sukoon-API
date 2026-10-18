"""Apply the original structured-term rules before accepting changed consent."""

from rest_framework.exceptions import ValidationError


def validate_changed_terms(terms):
    from ..rental_serializers import RentalTermsSerializer

    serializer = RentalTermsSerializer(data=terms)
    if not serializer.is_valid():
        raise ValidationError({"terms": serializer.errors})
    # Validate without rewriting the reviewed JSON or any signed document.


def changed_terms_blocker(item):
    from ..models import RentalChange

    if item.kind not in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
        return None
    try:
        validate_changed_terms(item.terms)
    except ValidationError:
        return "The proposed terms require correction and fresh participant review before signing or execution."
    if item.status == RentalChange.Status.SIGNED and (
        not item.document_id or not item.document_hash
    ):
        return (
            "The signed document identity requires operational review before execution."
        )
    return None
