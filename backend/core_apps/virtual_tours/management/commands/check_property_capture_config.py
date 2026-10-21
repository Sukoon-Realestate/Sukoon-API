"""Secret-free development preflight; never certifies a real device or 3D output."""

import importlib.metadata
import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.migrations.executor import MigrationExecutor
from django.db import connection
from core_apps.virtual_tours import storage
from core_apps.virtual_tours import capture_reconstruction


class Command(BaseCommand):
    help = "Check capture configuration, migrations, private storage and optional Gemini connectivity."

    def add_arguments(self, parser):
        parser.add_argument("--probe-gemini", action="store_true")
        parser.add_argument("--strict", action="store_true")

    def handle(self, *args, **options):
        installed = {}
        for package in (
            "Django",
            "djangorestframework",
            "numpy",
            "Pillow",
            "opencv-python-headless",
            "pycolmap",
            "torch",
            "gsplat",
        ):
            try:
                installed[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                installed[package] = None
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        root = storage.root()
        writable = False
        try:
            with tempfile.NamedTemporaryFile(dir=root) as file:
                file.write(b"capture-private-preflight")
                file.flush()
                os.fsync(file.fileno())
                writable = True
        except OSError:
            pass
        secret_file = Path(settings.BASE_DIR) / ".envs" / ".env.local"
        protected = not secret_file.exists() or secret_file.stat().st_mode & 0o077 == 0
        result = {
            "captureEnabled": settings.PROPERTY_CAPTURE_ENABLED,
            "databaseVendor": connection.vendor,
            "migrationsApplied": not pending,
            "privateStorageWritable": writable,
            "secretConfigured": bool(settings.GEMINI_API_KEY),
            "localSecretPermissionsRestricted": protected,
            "coachModel": settings.GEMINI_COACH_MODEL,
            "coachDailySessionLimit": settings.COACH_DAILY_SESSION_LIMIT,
            "maxSessionBytes": settings.CAPTURE_MAX_SESSION_BYTES,
            "retentionDays": settings.CAPTURE_RETENTION_DAYS,
            "freeDiskBytes": shutil.disk_usage(root).free,
            "packages": installed,
            "colmapCommandAvailable": shutil.which("colmap") is not None,
            "cudaCommandAvailable": shutil.which("nvidia-smi") is not None,
            "reconstructionPipelineImplemented": True,
            "reconstructionRuntimeEnabled": bool(
                getattr(settings, "CAPTURE_RECONSTRUCTION_ENABLED", False)
            ),
            "reconstructionRuntimeAvailable": False,
            "reconstructionRuntimeCode": "GPU_RUNTIME_NOT_CONFIGURED",
            "realDeviceCaptureValidated": False,
            "releaseReady": False,
        }
        runtime = capture_reconstruction.runtime_status()
        result["reconstructionRuntimeAvailable"] = runtime["available"]
        result["reconstructionRuntimeCode"] = runtime["code"]
        if options["probe_gemini"]:
            request = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                + settings.GEMINI_COACH_MODEL,
                headers={"x-goog-api-key": settings.GEMINI_API_KEY},
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    model = json.load(response)
                    result["geminiModelReachable"] = response.status == 200
                    result["geminiLiveSupported"] = "bidiGenerateContent" in model.get(
                        "supportedGenerationMethods", []
                    )
            except (urllib.error.URLError, ValueError):
                result["geminiModelReachable"] = False
                result["geminiLiveSupported"] = False
        result["localConfigurationReady"] = all(
            (
                result["captureEnabled"],
                result["migrationsApplied"],
                result["privateStorageWritable"],
                result["localSecretPermissionsRestricted"],
                result["secretConfigured"],
                settings.GEMINI_COACH_MODEL,
                installed["opencv-python-headless"],
                installed["numpy"],
                installed["Pillow"],
                settings.CAPTURE_MAX_SESSION_BYTES > 0,
                settings.CAPTURE_RETENTION_DAYS > 0,
                settings.COACH_DAILY_SESSION_LIMIT > 0,
                not options["probe_gemini"]
                or (
                    result.get("geminiModelReachable", False)
                    and result.get("geminiLiveSupported", False)
                ),
            )
        )
        self.stdout.write(json.dumps(result, indent=2))
        if options["strict"] and not result["localConfigurationReady"]:
            raise CommandError(
                "Local capture configuration is incomplete. See the nonsecret preflight fields."
            )
