import 'dart:async';
import 'package:melos_core/core/network/account_session.dart';

/// Coalesces settings while keeping one server-confirmed baseline per key.
class PreferenceWriteQueue {
  final int _generation = AccountSession.generation;
  final Map<String, bool> _confirmed = {}, _desired = {};
  final Map<String, int> _revisions = {};
  final List<String> _pending = [];
  final Set<String> _failed = {};
  Future<void>? _work;
  bool get busy => _work != null;
  bool valueFor(String key, bool fallback) => _desired[key] ?? fallback;
  Future<bool> update({
    required String key,
    required bool baseline,
    required bool value,
    required Future<bool> Function(String, bool) send,
  }) async {
    if (_generation != AccountSession.generation) return false;
    _confirmed.putIfAbsent(key, () => baseline);
    _desired[key] = value;
    _failed.remove(key);
    _revisions[key] = (_revisions[key] ?? 0) + 1;
    if (!_pending.contains(key)) _pending.add(key);
    _work ??= _drain(send);
    await _work;
    return _generation == AccountSession.generation &&
        _confirmed[key] == _desired[key] &&
        !_failed.contains(key);
  }

  Future<void> _drain(Future<bool> Function(String, bool) send) async {
    await Future<void>.value();
    try {
      while (_pending.isNotEmpty && _generation == AccountSession.generation) {
        final String key = _pending.first;
        final bool value = _desired[key]!;
        final int revision = _revisions[key]!;
        if (_confirmed[key] == value) {
          _pending.removeAt(0);
          continue;
        }
        bool succeeded = false;
        try {
          succeeded = await send(key, value);
        } catch (_) {
          /* Keep the confirmed value. */
        }
        if (_generation != AccountSession.generation) return;
        if (succeeded) {
          _confirmed[key] = value;
        } else if (_revisions[key] == revision) {
          _desired[key] = _confirmed[key]!;
          _failed.add(key);
        }
      }
    } finally {
      _work = null;
    }
  }
}
