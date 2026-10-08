import 'package:sokoun_app/features/main_view/data/account_access.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import '../../data/decision_tools_data.dart';
import '../../data/models/decision_notebook.dart';

class DecisionToolsCubit extends Cubit<DecisionNotebook> {
  DecisionToolsCubit({required this.accountId, DecisionToolsStore? store})
    : _store = store ?? const DecisionToolsData(),
      super(const DecisionNotebook.initial());
  final String accountId;
  final DecisionToolsStore _store;
  final int _sessionGeneration = AccountSession.generation;
  Future<void> _writes = Future.value();
  bool _loaded = false;
  bool get _active =>
      !isClosed &&
      AccountAccess.isVerified &&
      _sessionGeneration == AccountSession.generation;
  Future<void> load() async {
    await _writes;
    if (!_active) return;
    final notebook = await _store.read(accountId);
    if (!_active) return;
    _loaded = true;
    emit(notebook);
  }

  Future<void> _mutate(DecisionNotebook Function(DecisionNotebook) change) {
    final write = _writes.then((_) async {
      if (!_active || !_loaded) {
        throw StateError('The account session changed.');
      }
      AccountAccess.requireVerification();
      final notebook = change(state);
      await _store.write(accountId, notebook);
      if (_active) emit(notebook);
    });
    _writes = write.catchError((Object _) {});
    return write;
  }

  Future<bool> toggleComparison(PropertyDecision property) async {
    if (property.propertyId.isEmpty) return false;
    var changed = false;
    await _mutate((notebook) {
      final ids = List<String>.of(notebook.comparisonIds);
      if (!ids.remove(property.propertyId)) {
        if (ids.length >= 3) return notebook;
        ids.add(property.propertyId);
      }
      changed = true;
      final properties = List<PropertyDecision>.of(notebook.properties);
      if (!properties.any((entry) => entry.propertyId == property.propertyId)) {
        properties.add(property);
      }
      return notebook.copyWith(
        comparisonIds: List.unmodifiable(ids),
        properties: List.unmodifiable(properties),
      );
    });
    return changed;
  }

  Future<void> saveDecision(PropertyDecision property) =>
      property.propertyId.isEmpty
      ? Future.value()
      : _mutate(
          (notebook) => notebook.copyWith(
            properties: [
              for (final entry in notebook.properties)
                if (entry.propertyId != property.propertyId) entry,
              property,
            ],
          ),
        );
  Future<void> removeDecision(String propertyId) => _mutate(
    (notebook) => notebook.copyWith(
      properties: notebook.properties
          .where((entry) => entry.propertyId != propertyId)
          .toList(),
      comparisonIds: notebook.comparisonIds
          .where((id) => id != propertyId)
          .toList(),
    ),
  );
  Future<void> saveSearch(String name, PropertySearchFilters filters) {
    if (name.trim().isEmpty || !filters.hasValidPriceRange) {
      throw ArgumentError('A valid name and price range are required.');
    }
    final id = filters.copyWith(page: 1).cacheKey;
    return _mutate(
      (notebook) => notebook.copyWith(
        searches: [
          for (final search in notebook.searches)
            if (search.id != id) search,
          SavedPropertySearch(
            id: id,
            name: name.trim(),
            filters: filters.copyWith(page: 1),
          ),
        ],
      ),
    );
  }

  Future<void> removeSearch(String searchId) => _mutate(
    (notebook) => notebook.copyWith(
      searches: notebook.searches
          .where((search) => search.id != searchId)
          .toList(),
    ),
  );
  Future<void> flush() => _writes;
  @override
  Future<void> close() async {
    await _writes;
    return super.close();
  }
}
