import 'package:easy_localization/easy_localization.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:upgrader/upgrader.dart';

import 'widgets/whats_new_sheet.dart';

class WhatsNewService {
  static const Duration _storeLookupTimeout = Duration(seconds: 5);
  static const int _maxChangelogItems = 20;

  static List<String> _itemsFor(String version) {
    final String prefix = 'whats_new_v_${version.replaceAll('.', '_')}_item_';
    final List<String> items = [];

    for (int i = 1; i <= _maxChangelogItems; i++) {
      final String key = '$prefix$i';
      final String value = key.tr();
      if (value == key) break;
      items.add(value);
    }

    return items;
  }

  static Future<void> showIfNeeded({required Upgrader upgrader}) async {
    final PackageInfo info = await PackageInfo.fromPlatform();
    final String currentVersion = info.version;
    final String? lastSeen =
        CacheStorage.read(CacheConstant.lastSeenWhatsNewVersion) as String?;

    // A fresh install should not immediately show release notes.
    if (lastSeen == null) {
      await CacheStorage.write(
        CacheConstant.lastSeenWhatsNewVersion,
        currentVersion,
      );
      return;
    }

    if (lastSeen == currentVersion) return;

    // Record the version before resolving notes so a failed store lookup does
    // not repeat on every launch.
    await CacheStorage.write(
      CacheConstant.lastSeenWhatsNewVersion,
      currentVersion,
    );

    final List<String> items = await _resolveItems(upgrader, currentVersion);
    if (items.isEmpty) return;

    await showWhatsNewSheet(items: items, version: currentVersion);
  }

  static Future<List<String>> _resolveItems(
    Upgrader upgrader,
    String currentVersion,
  ) async {
    final List<String> storeNotes = await _storeReleaseNotes(upgrader);
    if (storeNotes.isNotEmpty) return storeNotes;
    return _itemsFor(currentVersion);
  }

  static Future<List<String>> _storeReleaseNotes(Upgrader upgrader) async {
    try {
      await upgrader.initialize().timeout(_storeLookupTimeout);

      // Store notes are only valid for the installed version. If the store is
      // ahead, those notes describe an update the user has not installed yet.
      final bool onLatest =
          upgrader.currentAppStoreVersion == upgrader.currentInstalledVersion;
      return _splitNotes(onLatest ? upgrader.releaseNotes : null);
    } catch (_) {
      return const [];
    }
  }

  static List<String> _splitNotes(String? notes) {
    if (notes == null || notes.trim().isEmpty) return const [];

    return notes
        .split('\n')
        .map(
          (line) => line.trim().replaceFirst(RegExp(r'^[-•*]\s*'), '').trim(),
        )
        .where((line) => line.isNotEmpty)
        .toList();
  }
}
