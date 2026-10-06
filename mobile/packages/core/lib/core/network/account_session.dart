import 'dart:async';

/// Identifies requests/cache entries belonging to a single signed-in session.
abstract final class AccountSession {
  static String? _userId;
  static int _generation = 0;
  static final StreamController<void> _expired =
      StreamController<void>.broadcast();

  static String? get userId => _userId;
  static int get generation => _generation;
  static Stream<void> get expired => _expired.stream;
  static String cacheKey(String key) => 'account_v1_${_userId ?? 'guest'}_$key';

  static void begin(String userId) {
    _userId = userId;
    _generation++;
  }

  static void end() {
    _userId = null;
    _generation++;
  }

  static void notifyExpired() {
    if (_userId == null) return;
    end();
    _expired.add(null);
  }
}
