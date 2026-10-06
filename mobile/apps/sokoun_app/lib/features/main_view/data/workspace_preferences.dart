import 'package:melos_core/core/helpers/cache_service.dart';

import 'enums/app_workspace.dart';

abstract final class WorkspacePreferences {
  static String keyFor(String userId) => 'workspace_v1_$userId';

  /// Run before authentication can overwrite the legacy cached account.
  static Future<void> migrateLegacy() async {
    final Object? legacy = CacheStorage.read('current_user_type');
    final Map<String, dynamic>? user = CacheStorage.read(
      'user',
      isDecoded: true,
    );
    final String id = user?['id']?.toString() ?? '';
    if (id.isNotEmpty && id != '0' && CacheStorage.read(keyFor(id)) == null) {
      await CacheStorage.write(
        keyFor(id),
        AppWorkspaceX.fromName(legacy ?? user?['type']).name,
      );
    }
    await CacheStorage.delete('current_user_type');
  }

  static AppWorkspace read(String userId) =>
      AppWorkspaceX.fromName(CacheStorage.read(keyFor(userId)));

  static Future<void> write(String userId, AppWorkspace workspace) =>
      CacheStorage.write(keyFor(userId), workspace.name);
}
