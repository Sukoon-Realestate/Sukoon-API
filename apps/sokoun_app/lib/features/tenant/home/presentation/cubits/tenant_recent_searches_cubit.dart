import 'package:melos_core/core/network/account_session.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_search_data.dart';

class TenantRecentSearchesCubit extends Cubit<List<RecentSearchContent>> {
  TenantRecentSearchesCubit() : super(const []);

  final int _generation = AccountSession.generation;
  Future<void> _pendingWrite = Future.value();
  List<RecentSearchContent> _persisted = const [];
  int _revision = 0;

  void loadRecentSearches() {
    if (isClosed || _generation != AccountSession.generation) return;
    _persisted = _unique(TenantSearchData.getRecentSearches());
    emit(_persisted);
  }

  Future<bool> addRecentSearch(String title) {
    final query = _normalize(title);
    if (query.isEmpty || isClosed) return Future.value(true);
    return _update(_unique([RecentSearchContent(title: query), ...state]));
  }

  Future<bool> removeRecentSearch(RecentSearchContent search) => _update([
    for (final item in state)
      if (_identity(item.title) != _identity(search.title)) item,
  ]);

  Future<bool> clearRecentSearches() => _update(const []);

  /// Retain searches made after deletion while restoring the removed entries.
  Future<bool> restoreRecentSearches(List<RecentSearchContent> snapshot) =>
      _update(
        _unique([
          ...state.where((item) => !snapshot.contains(item)),
          ...snapshot,
        ]),
      );

  Future<bool> _update(List<RecentSearchContent> next) {
    if (isClosed || _generation != AccountSession.generation) {
      return Future.value(false);
    }
    final revision = ++_revision;
    final snapshot = List<RecentSearchContent>.unmodifiable(next);
    emit(snapshot);
    // Serialize writes so rapid deletion/undo cannot persist an older snapshot.
    final operation = _pendingWrite.then((_) async {
      if (_generation != AccountSession.generation) return false;
      try {
        await TenantSearchData.saveRecentSearches(snapshot);
        if (_generation != AccountSession.generation) return false;
        _persisted = snapshot;
        return true;
      } catch (_) {
        if (!isClosed && revision == _revision) emit(_persisted);
        return false;
      }
    });
    _pendingWrite = operation.then((_) {});
    return operation;
  }

  static String _normalize(String value) =>
      value.trim().replaceAll(RegExp(r'\s+'), ' ');
  static String _identity(String value) => _normalize(value).toLowerCase();

  static List<RecentSearchContent> _unique(
    Iterable<RecentSearchContent> searches,
  ) {
    final seen = <String>{};
    return [
      for (final search in searches)
        if (_identity(search.title).isNotEmpty &&
            seen.add(_identity(search.title)))
          RecentSearchContent(title: _normalize(search.title)),
    ].take(TenantSearchData.maxRecentSearches).toList(growable: false);
  }
}
