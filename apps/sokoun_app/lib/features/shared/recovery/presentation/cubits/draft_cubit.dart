import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/network/account_session.dart';
import '../../data/private_recovery_data.dart';

enum LocalSaveStatus { initial, saving, saved, failed }

class DraftState<T> {
  const DraftState({this.record, this.status = LocalSaveStatus.initial});
  final DraftRecord<T>? record;
  final LocalSaveStatus status;
}

class DraftCubit<T> extends Cubit<DraftState<T>> {
  DraftCubit(this._store) : super(DraftState<T>());
  final PrivateDraftStore<T> _store;
  final int _generation = AccountSession.generation;
  Future<void> _writes = Future.value();
  Timer? _timer;
  T? _pending;
  T? _latest;
  bool _stopped = false;
  bool get active =>
      !isClosed && !_stopped && _generation == AccountSession.generation;
  Future<void> load() async {
    try {
      final DraftRecord<T>? record = await _store.read();
      if (active) emit(DraftState(record: record));
    } catch (_) {
      if (active) emit(DraftState(status: LocalSaveStatus.failed));
    }
  }

  void schedule(T value) {
    if (!active) return;
    _pending = value;
    _latest = value;
    emit(DraftState(record: state.record, status: LocalSaveStatus.saving));
    _timer?.cancel();
    _timer = Timer(const Duration(milliseconds: 400), () => unawaited(flush()));
  }

  Future<void> flush() async {
    _timer?.cancel();
    final T? value = _pending;
    _pending = null;
    if (value == null || !active) return _writes;
    final Future<void> next = _writes.then((_) async {
      if (!active) return;
      try {
        final DraftRecord<T> record = await _store.write(value);
        if (active) {
          emit(
            DraftState(
              record: record,
              status: _pending == null
                  ? LocalSaveStatus.saved
                  : LocalSaveStatus.saving,
            ),
          );
        }
      } catch (_) {
        if (active) {
          emit(
            DraftState(record: state.record, status: LocalSaveStatus.failed),
          );
        }
      }
    });
    _writes = next;
    await next;
  }

  Future<void> retry() async {
    final T? value = _latest;
    if (value == null || !active) return;
    schedule(value);
    await flush();
  }

  Future<void> clear() async {
    _timer?.cancel();
    _pending = null;
    _latest = null;
    await _writes;
    if (!active) return;
    await _store.clear();
    if (active) emit(DraftState<T>());
  }

  @override
  Future<void> close() async {
    await flush();
    _stopped = true;
    _timer?.cancel();
    await super.close();
  }
}
