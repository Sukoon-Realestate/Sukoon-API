import 'dart:convert';
import 'dart:io';

void main() {
  final bootstrapFile = File('build/web/flutter_bootstrap.js');
  final bootstrap = bootstrapFile.readAsStringSync();
  final revision = RegExp(
    r'"engineRevision":"([a-f0-9]+)"',
  ).firstMatch(bootstrap)?.group(1);
  if (revision == null || !bootstrap.contains("new URL('canvaskit/',")) {
    throw StateError('Cannot version the bundled Flutter renderer.');
  }
  // Renderer filenames are otherwise reused across Flutter SDK upgrades.
  // A revisioned URL permits long browser caching without mixing engines.
  final renderer = Directory('build/web/canvaskit');
  final versioned = renderer.renameSync('build/web/canvaskit-$revision');
  renderer.createSync();
  versioned.renameSync('${renderer.path}/$revision');
  bootstrapFile.writeAsStringSync(
    bootstrap.replaceFirst(
      "new URL('canvaskit/',",
      "new URL('canvaskit/$revision/',",
    ),
  );

  final manifestFile = File('build/web/assets/FontManifest.json');
  final manifest = (jsonDecode(manifestFile.readAsStringSync()) as List)
      .cast<Map<String, dynamic>>();
  const usedFamilies = {
    'MaterialIcons',
    'Roboto',
    'packages/melos_core/Tajawal',
  };
  // Flutter eagerly loads every entry in FontManifest before its first frame.
  // The shared mobile package also declares Riyal and Iconsax, which the
  // landing page never uses. Keep the original assets and all Tajawal weights
  // available; only omit these unused families from eager startup loading.
  final kept = manifest
      .where((family) => usedFamilies.contains(family['family']))
      .toList();
  for (final name in usedFamilies) {
    if (!kept.any((family) => family['family'] == name)) {
      throw StateError('Missing required landing page font: $name');
    }
  }
  var savedBytes = 0;
  for (final family in manifest.where(
    (family) => !usedFamilies.contains(family['family']),
  )) {
    for (final font in family['fonts'] as List) {
      savedBytes += File('build/web/assets/${font['asset']}').lengthSync();
    }
  }
  manifestFile.writeAsStringSync(jsonEncode(kept));
  stdout.writeln('Removed $savedBytes bytes of unused fonts from startup.');
}
