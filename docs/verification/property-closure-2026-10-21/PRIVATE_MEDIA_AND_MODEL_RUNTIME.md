# Private chat persistence and prepared-model runtime

Chat attachments now acknowledge readiness only after the private source and thumbnail have been saved to the configured authenticated provider. Existing authorization checks still run before any materialization; responses remain private/no-store. The local directory is a cache. Cloudinary objects use the separate `sokoun-chat-media` namespace, chunk checksums, a final manifest, byte limits, and server-only signed access. The hourly inline cleanup also applies chat retention, with no extra worker subscription.

Before replacing an existing service, restore any missing legacy files from verified originals, then run `python manage.py backfill_private_chat_media --watch-seconds 600`. Do not replace the service if any active source is missing. The live backfill on 2026-10-21 verified all six existing files against the provider before deployment. This included recovery of one voice attachment from the device cache, matched to the database upload fingerprint. No message/attachment identity was changed.

The current Python-only App Platform service needs the model validators installed at build time:

```
python scripts/install_tour_validators.py && DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic --noinput
```

The installer pins the official Node 22.23.4 Linux x64 archive SHA-256 and installs the existing locked validator dependencies. It creates `.runtime/node` inside the built service; it creates no paid resource. Enable `VIRTUAL_TOUR_MODEL_READ=true`, `VIRTUAL_TOUR_MODEL_WRITE=true`, and set the two validator commands to absolute paths ending in `tools/virtual_tours/validate-glb.sh` and `tools/virtual_tours/validate-spawns.sh` after a successful build. Existing production feature switches remain authoritative.

Validation before deployment: 73 tests passed, two PostgreSQL-selective cases skipped in the chosen test configuration. The prepared two-room fixture passes Khronos GLB validation and validates all three approved spawns. Actual provider survival, deployed model processing, device UI, and resource observations are recorded separately after execution.
