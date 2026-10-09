import 'dart:convert';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/helpers/helpers.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/dio_service.dart';

/// Workspace is used only for workspace-owned entities, never chat/profile.
class RecoveryScope {
  const RecoveryScope({
    required this.environment,
    required this.accountId,
    required this.flow,
    this.entityId = '',
    this.workspace = '',
  });
  final String environment;
  final String accountId;
  final String flow;
  final String entityId;
  final String workspace;
  String get key =>
      'sokoun_private_v2_${base64Url.encode(utf8.encode(jsonEncode([environment, accountId, workspace, flow, entityId])))}';

  static Future<String> currentEnvironment() async {
    final String base =
        await SecureStorage.read(
          Helpers.currentFlavor.isDev
              ? SecureLocalVariableKeys.devBaseUrlKey
              : SecureLocalVariableKeys.baseUrlKey,
        ) ??
        '';
    final Uri? uri = Uri.tryParse(base);
    final String normalized =
        uri != null && uri.hasScheme && uri.host.isNotEmpty
        ? uri
              .replace(query: '', fragment: '')
              .toString()
              .replaceFirst(RegExp(r'/+$'), '')
        : 'unconfigured';
    return '${Helpers.currentFlavor.name}|$normalized';
  }

  static Future<RecoveryScope> current({
    required String flow,
    String entityId = '',
    String workspace = '',
  }) async {
    final String accountId = AccountSession.userId ?? '';
    return RecoveryScope(
      environment: await currentEnvironment(),
      accountId: accountId,
      flow: flow,
      entityId: entityId,
      workspace: workspace,
    );
  }
}
