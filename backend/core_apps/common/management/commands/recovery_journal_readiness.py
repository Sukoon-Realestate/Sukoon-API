"""Read-only journal/control review. Never grants operational approval or opens a scope."""

import json
from django.core.management.base import BaseCommand, CommandError
from core_apps.common.recovery import journal, state, RecoveryRequired


class Command(BaseCommand):
    help = "Verify independent journal integrity and unresolved instructions without enabling any scope."

    def handle(self, *args, **options):
        try:
            store = journal()
            if not hasattr(store, "health"):
                raise CommandError(
                    "The configured journal has no independent production health proof."
                )
            health = store.health()
            control = state()
            self.stdout.write(
                json.dumps(
                    {
                        "journal": health,
                        "control": {
                            key: control.get(key)
                            for key in [
                                "environment",
                                "mode",
                                "generation",
                                "security_epoch",
                                "scopes",
                            ]
                        },
                        "approval_granted": False,
                        "scopes_opened": [],
                        "remaining": [
                            "independent operator approval",
                            "provider-specific authoritative reconciliation",
                            "deployment failure-domain evidence",
                        ],
                    },
                    sort_keys=True,
                )
            )
        except RecoveryRequired as exc:
            raise CommandError(str(exc.detail)) from None
