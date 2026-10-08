import 'dart:convert';
import 'package:melos_core/core/network/account_session.dart';
import 'package:uuid/uuid.dart';

/// Retries keep their key; a changed subject, revision or intent gets a new one.
class PremiumRequestKeys {
  final Map<String, String> _keys = {};
  String forAction(String action, Iterable<Object?> values) {
    final identity = jsonEncode([AccountSession.generation, action, ...values]);
    return _keys.putIfAbsent(identity, () => const Uuid().v4());
  }
}
