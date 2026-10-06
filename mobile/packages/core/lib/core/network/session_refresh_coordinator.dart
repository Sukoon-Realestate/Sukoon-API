import '../error/exceptions.dart';
import 'account_session.dart';

/// Shares refresh work between HTTP retries and socket reconnections.
class SessionRefreshCoordinator {
  SessionRefreshCoordinator({required Future<void> Function(int) refresh})
    : _refresh = refresh;

  static const revisionKey = 'session_refresh_revision';

  final Future<void> Function(int) _refresh;
  Future<void>? _pending;
  int? _generation;
  int _revision = 0;

  int get revision => _revision;

  Future<void> refresh(int generation, {int? requestRevision}) {
    if (generation != AccountSession.generation) {
      return Future.error(const RequestCancelledException());
    }
    if (_pending != null && _generation == generation) return _pending!;
    // A late 401 for an older access token can use the refresh already completed.
    if (requestRevision != null && requestRevision < _revision) {
      return Future.value();
    }
    _generation = generation;
    late final Future<void> request;
    request = _performRefresh(generation).whenComplete(() {
      if (identical(_pending, request)) _pending = null;
    });
    _pending = request;
    return request;
  }

  Future<void> _performRefresh(int generation) async {
    await _refresh(generation);
    if (generation != AccountSession.generation) {
      throw const RequestCancelledException();
    }
    _revision++;
  }
}
