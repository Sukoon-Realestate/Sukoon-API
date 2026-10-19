"""Publish supported defaults only with an identified current policy administrator."""

import json
import uuid
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_apps.users.models import User
from core_apps.features.models import PolicyDecisionHead
from core_apps.features.services import business_policies as policies
from core_apps.features.services.business_policy_catalog import CATALOG
from rest_framework.exceptions import APIException


class Command(BaseCommand):
    help = "Review or publish the supported policy pack. Existing published families are never replaced."

    def add_arguments(self, parser):
        parser.add_argument("--actor-id", required=True)
        parser.add_argument("--evidence-reference", required=True)
        parser.add_argument("--policy-version", default="2026-10-19.1")
        parser.add_argument("--apply", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            actor = User.objects.get(id=options["actor_id"])
            policies.administrator(actor)
            results = []
            for code, spec in CATALOG.items():
                if policies.current(code):
                    results.append(
                        {"code": code, "result": "existing_version_preserved"}
                    )
                    continue
                head = PolicyDecisionHead.objects.filter(code=code).first()
                data = {
                    "code": code,
                    "rules": spec["rules"],
                    "version": options["policy_version"],
                    "expected_head_revision": head.revision if head else 0,
                    "request_key": str(
                        uuid.uuid5(
                            uuid.NAMESPACE_URL,
                            f"sokoun-policy-pack:{code}:{options['policy_version']}",
                        )
                    ),
                    "evidence_reference": options["evidence_reference"],
                    "reason": "Product-owner delegated policy selection, researched supported behavior and prospective application. No retroactive charges or consent from silence.",
                }
                if options["apply"]:
                    policies.publish(actor, data)
                results.append(
                    {
                        "code": code,
                        "result": "published" if options["apply"] else "review_only",
                        "rules": spec["rules"],
                    }
                )
            self.stdout.write(
                json.dumps({"applied": options["apply"], "items": results})
            )
        except (User.DoesNotExist, ValueError, APIException) as error:
            raise CommandError(str(error)) from None
