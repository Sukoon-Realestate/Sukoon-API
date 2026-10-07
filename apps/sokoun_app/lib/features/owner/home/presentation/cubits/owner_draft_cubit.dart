import 'dart:async';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/network/account_session.dart';
import '../../data/owner_draft_data.dart';
import '../../data/models/owner_property_draft.dart';

class OwnerDraftCubit extends Cubit<OwnerPropertyDraft> {
  OwnerDraftCubit({required OwnerDraftStore store})
    : _store = store,
      super(const OwnerPropertyDraft.initial());
  final OwnerDraftStore _store;
  final int _sessionGeneration = AccountSession.generation;
  Future<void> _writes = Future.value();
  Timer? _debounce;
  OwnerPropertyDraft? _pending;
  bool get _active =>
      !isClosed && _sessionGeneration == AccountSession.generation;
  Future<void> load() async {
    final draft = await _store.read();
    if (_active) emit(draft);
  }

  void schedule(OwnerPropertyDraft draft) {
    if (!_active) return;
    _pending = draft;
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 400), () {
      unawaited(flush().catchError((Object _) {}));
    });
  }

  Future<void> save(OwnerPropertyDraft draft) {
    _debounce?.cancel();
    _pending = null;
    final write = _writes.then((_) async {
      if (!_active) throw StateError(LocaleKeys.freeLocalSaveFailed);
      try {
        final saved = await _store.write(draft);
        if (!_active) throw StateError(LocaleKeys.freeLocalSaveFailed);
        emit(saved.copyWith(localSaveFailed: false));
      } catch (_) {
        if (_active) emit(state.copyWith(localSaveFailed: true));
        rethrow;
      }
    });
    _writes = write.catchError((Object _) {});
    return write;
  }

  Future<void> flush() async {
    _debounce?.cancel();
    final draft = _pending;
    _pending = null;
    if (draft != null) await save(draft);
    await _writes;
  }

  Future<void> clear() async {
    _debounce?.cancel();
    _pending = null;
    await _writes;
    if (!_active) return;
    await _store.clear();
    if (_active) emit(const OwnerPropertyDraft.initial());
  }

  @override
  Future<void> close() async {
    try {
      await flush();
    } finally {
      await super.close();
    }
  }
}
