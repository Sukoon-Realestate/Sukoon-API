import 'dart:async';

/// Identifies requests/cache entries belonging to a single signed-in session.
abstract final class AccountSession {
  static String? _userId;
  static int _generation = 0;
  static final StreamController<void> _expired =
      StreamController<void>.broadcast();
  static final Set<Future<void> Function(String)> _cleanup = {};
  static Future<void>? _cleanupWork;
  static final Set<String> _cleanupAccounts = {};

  static String? get userId => _userId;
  static int get generation => _generation;
  static Stream<void> get expired => _expired.stream;
  static bool get hasPendingCleanup => _cleanupAccounts.isNotEmpty;
  static String cacheKey(String key) => 'account_v1_${_userId ?? 'guest'}_$key';

  static void begin(String userId) {
    if (_userId != null && _userId != userId) end();
    _userId = userId;
    _generation++;
  }

  static void end({String? persistedAccountId}) {
    final String? previous = _userId ?? persistedAccountId;
    _userId = null;
    _generation++;
    if (previous == null) return;
    _cleanupAccounts.add(previous);
    // Invoke synchronously so participants stop timers/sockets before deletion.
    final List<Future<void>> work = [
      for (final callback in List.of(_cleanup))
        Future.sync(() => callback(previous)),
    ];
    final Future<void>? previousWork = _cleanupWork;
    late final Future<void> next;
    next =
        Future.wait([
          if (previousWork != null) previousWork.catchError((Object _) {}),
          ...work,
        ]).then((_) {
          _cleanupAccounts.remove(previous);
        });
    _cleanupWork = next;
    // Expiry can start cleanup without an awaiting UI owner.
    unawaited(
      next.then<void>(
        (_) {
          if (identical(_cleanupWork, next)) _cleanupWork = null;
        },
        onError: (Object _, StackTrace __) {
          if (identical(_cleanupWork, next)) _cleanupWork = null;
        },
      ),
    );
  }

  static void Function() registerCleanup(
    Future<void> Function(String) callback,
  ) {
    _cleanup.add(callback);
    return () => _cleanup.remove(callback);
  }

  static Future<void> finishCleanup() async {
    await _cleanupWork?.catchError((Object _) {});
    for (final String account in _cleanupAccounts.toList()) {
      await Future.wait([
        for (final callback in List.of(_cleanup))
          Future.sync(() => callback(account)),
      ]);
      _cleanupAccounts.remove(account);
    }
  }

  static void notifyExpired() {
    if (_userId == null) return;
    end();
    _expired.add(null);
  }
}
