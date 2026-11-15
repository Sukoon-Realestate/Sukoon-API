# Folder-name sheet controller lifecycle

The reported blank screen followed hot reload. The first exception identified saved_folders_screen.dart: a TextEditingController was used after disposal. Subsequent inherited-widget and deactivated-ancestor assertions were cascading errors.

Cause: _name created a controller in the caller, awaited the sheet result, then disposed the controller. A modal route completes its result before its reverse animation unmounts the text field. A rebuild during that interval reuses the disposed controller.

Fix: a private stateful folder-name sheet initializes and disposes its own controller. The route now owns its full lifecycle. Existing creation, initial rename text, trimming, 60-character limit, cancellation and folder persistence remain. Sheet content is scrollable for keyboard/compact layouts.

Verification: the initial regression run reproduced the disposed-controller exception before the fix. After the fix, 54 checks passed: four save/rename/dismissal cases with widget-tree reassembly during closing, normal/reduced motion, plus 50 saved-card checks. App analysis has the same 12 unrelated diagnostics. A hot restart loaded the fix into the existing simulator. Device Hub inspection confirmed the saved properties screen rendered again with the saved card and organization/removal controls, preserving stored data. No live folders were created or deleted for verification.
