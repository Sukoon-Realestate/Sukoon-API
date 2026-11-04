import pytest


@pytest.fixture
def public_content_pages(db):
    """Restore reviewed page fixtures after transaction tests flush seed rows."""
    from .content.public_pages_v2 import CONTENT
    from .content_models import PublicContentPage

    for slug, languages in CONTENT.items():
        PublicContentPage.objects.update_or_create(slug=slug, defaults={
            f'{field}_{language}': values[index]
            for language, values in languages.items()
            for index, field in enumerate(('title', 'content'))
        })
