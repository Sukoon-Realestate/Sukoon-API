import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestStaticPagesAPI:
    def test_about_us_page_default_en(self, api_client):
        url = reverse("page-about-us")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["slug"] == "about-us"
        assert data["title"] == "About Us"
        assert data["language"] == "en"
        assert data["content_format"] == "plain_text"
        assert "Sokoun" in data["content"]

    def test_about_us_page_arabic_via_query_param(self, api_client):
        url = f"{reverse('page-about-us')}?lang=ar"
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["language"] == "ar"
        assert data["title"] == "عن سكون"

    def test_privacy_policy_page(self, api_client):
        url = reverse("page-privacy-policy")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["slug"] == "privacy-policy"
        assert data["title"] == "Privacy Policy"

    def test_terms_page(self, api_client):
        url = reverse("page-terms")
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()["data"]
        assert data["slug"] == "terms"
        assert data["title"] == "Terms and Conditions"

    def test_nonexistent_page_returns_404(self, api_client):
        url = reverse("page-dynamic", kwargs={"slug": "nonexistent-page"})
        res = api_client.get(url)
        assert res.status_code == status.HTTP_404_NOT_FOUND
