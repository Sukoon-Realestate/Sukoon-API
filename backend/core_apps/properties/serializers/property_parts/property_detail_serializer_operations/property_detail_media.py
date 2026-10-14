"""PropertyDetailMedia operations owned by PropertyDetailSerializer."""

import json
from typing import Optional
from ....models import Property
from ..property_list_serializer import PropertyImageSerializer


class PropertyDetailMediaMixin:
    def get_rental_inventory(self, obj: Property) -> dict:
        inventory = json.loads(json.dumps(obj.rental_inventory or {}))
        request = self.context.get("request")
        is_owner = bool(
            request
            and request.user.is_authenticated
            and (request.user == obj.owner or request.user.is_staff)
        )
        offers = []
        for offer in inventory.get("offers", []):
            if not is_owner and (
                offer.get("archived") or offer.get("availability") != "available"
            ):
                continue
            offer["offer_link"] = (
                f"https://sokoun.app/properties/{obj.id}/offers/{offer.get('id')}"
            )
            if not is_owner:
                offer.pop("actions", None)
            offers.append(offer)
        inventory["offers"] = offers
        return inventory

    def get_ownership_proof(self, obj: Property) -> Optional[str]:
        request = self.context.get("request")
        if (
            not request
            or not getattr(request, "user", None)
            or not request.user.is_authenticated
        ):
            return None
        if request.user == obj.owner or getattr(request.user, "is_staff", False):
            if obj.ownership_proof:
                return getattr(obj.ownership_proof, "url", str(obj.ownership_proof))
        return None

    def _get_cover_and_images(self, obj: Property):
        all_images = list(obj.images.all())
        main_img_url = ""
        if obj.main_image:
            main_img_url = getattr(obj.main_image, "url", str(obj.main_image))

        cover_img = None
        if main_img_url:
            for img in all_images:
                img_url = getattr(img.image, "url", str(img.image))
                if img_url == main_img_url:
                    cover_img = img
                    break

        if not cover_img and all_images:
            cover_img = all_images[0]

        ordered_images = []
        if cover_img:
            ordered_images.append(cover_img)
            for img in all_images:
                if img.pkid != cover_img.pkid:
                    ordered_images.append(img)
        else:
            ordered_images = all_images

        return cover_img, ordered_images

    def get_main_image_id(self, obj: Property) -> Optional[str]:
        cover_img, _ = self._get_cover_and_images(obj)
        return str(cover_img.id) if cover_img else None

    def get_main_image_name(self, obj: Property) -> str:
        cover_img, _ = self._get_cover_and_images(obj)
        return (cover_img.name or "").strip() if cover_img else ""

    def get_main_image_description(self, obj: Property) -> str:
        cover_img, _ = self._get_cover_and_images(obj)
        return (cover_img.description or "").strip() if cover_img else ""

    def get_images(self, obj: Property) -> list[dict]:
        _, ordered_images = self._get_cover_and_images(obj)
        return PropertyImageSerializer(
            ordered_images, many=True, context=self.context
        ).data
