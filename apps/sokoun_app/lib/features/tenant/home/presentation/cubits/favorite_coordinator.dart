import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:multiple_result/multiple_result.dart';
import '../../data/models/favorite_target.dart';

/// One confirmed baseline and latest intention per account/property/offer.
class FavoriteCoordinator extends Cubit<Map<FavoriteTarget, FavoriteState>> {
  FavoriteCoordinator() : super(const {});
  static final FavoriteCoordinator instance = FavoriteCoordinator();
  final Map<FavoriteTarget, Future<Result<BaseModel<bool>, Failure>>> _lanes =
      {};
  int _generation = AccountSession.generation;
  bool _registered = false;
  void _ensureSession() {
    if (!_registered) {
      _registered = true;
      AccountSession.registerCleanup((_) async {
        if (!isClosed) emit(const {});
      });
    }
    if (_generation != AccountSession.generation) {
      _generation = AccountSession.generation;
      _lanes.clear();
      emit(const {});
    }
  }

  FavoriteState? value(FavoriteTarget target) {
    _ensureSession();
    return state[target];
  }

  void seed(FavoriteTarget target, bool saved) {
    _ensureSession();
    if (state.containsKey(target)) return;
    emit({...state, target: FavoriteState(confirmed: saved, desired: saved)});
  }

  /// Only reads started at the current mutation revision may update a baseline.
  void reconcile(FavoriteTarget target, bool saved, int requestRevision) {
    _ensureSession();
    final FavoriteState? current = state[target];
    if (current == null) {
      seed(target, saved);
      return;
    }
    if (current.busy || current.revision != requestRevision) return;
    emit({
      ...state,
      target: FavoriteState(
        confirmed: saved,
        desired: saved,
        revision: current.revision,
      ),
    });
  }

  Future<Result<BaseModel<bool>, Failure>> request({
    required FavoriteTarget target,
    required bool desired,
    required Future<Result<BaseModel<bool>, Failure>> Function(bool) send,
  }) {
    _ensureSession();
    final FavoriteState current =
        state[target] ?? FavoriteState(confirmed: !desired, desired: !desired);
    emit({
      ...state,
      target: FavoriteState(
        confirmed: current.confirmed,
        desired: desired,
        revision: current.revision + 1,
        busy: true,
      ),
    });
    return _lanes[target] ??= _drain(target, send, _generation);
  }

  Future<Result<BaseModel<bool>, Failure>> _drain(
    FavoriteTarget target,
    Future<Result<BaseModel<bool>, Failure>> Function(bool) send,
    int generation,
  ) async {
    // Defer start until request has registered its lane, allowing coalescing.
    await Future<void>.value();
    Result<BaseModel<bool>, Failure>? last;
    while (!isClosed && generation == AccountSession.generation) {
      final FavoriteState? current = state[target];
      if (current == null) break;
      if (current.desired == current.confirmed) {
        emit({
          ...state,
          target: FavoriteState(
            confirmed: current.confirmed,
            desired: current.desired,
            revision: current.revision,
          ),
        });
        _lanes.remove(target);
        return last?.isError() == true
            ? last!
            : Success(
                BaseModel(
                  key: '',
                  msg: last?.tryGetSuccess()?.msg ?? '',
                  data: current.confirmed,
                ),
              );
      }
      final bool sent = current.desired;
      final int revision = current.revision;
      Result<BaseModel<bool>, Failure> result;
      try {
        result = await send(sent);
      } catch (_) {
        result = const Error(Failure(''));
      }
      if (isClosed || generation != AccountSession.generation) break;
      final FavoriteState latest = state[target]!;
      final Failure? failure = result.tryGetError();
      if (failure != null) {
        if (latest.revision == revision) {
          emit({
            ...state,
            target: FavoriteState(
              confirmed: latest.confirmed,
              desired: latest.confirmed,
              revision: latest.revision,
              error: failure.message,
            ),
          });
          _lanes.remove(target);
          return Error(failure);
        }
        // A stale failure cannot undo newer intent. Continue from the baseline.
      } else {
        emit({
          ...state,
          target: FavoriteState(
            confirmed: sent,
            desired: latest.desired,
            revision: latest.revision,
            busy: latest.desired != sent,
          ),
        });
        last = result;
      }
    }
    if (generation == _generation) _lanes.remove(target);
    return const Error(RequestCancelledFailure());
  }
}
