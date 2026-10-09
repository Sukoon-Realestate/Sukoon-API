import 'dart:developer';
import 'dart:core';
import 'package:flutter/foundation.dart';
import 'package:multiple_result/multiple_result.dart';

import '../base_crud/code/domain/usecases/pagination_response.dart';
import '../error/exceptions.dart';
import '../error/failure.dart';
import 'object.dart';

extension ErrorHandlerWithCache<M> on Future<BaseModel<M>> {
  Future<Result<BaseModel<M>, Failure>> handleCallbackWithCache({
    required String cacheKey,
    required M Function(Map<String, dynamic> json) fromCacheJson,
    required Map<String, dynamic> Function(M) toJson,
    required void Function(String key, Map<String, dynamic> json) onSave,
    required Map<String, dynamic>? Function(String key) onRead,
    void Function(String key)? onInvalidate,
  }) async {
    try {
      final result = await this;
      try {
        onSave(cacheKey, toJson(result.data));
      } catch (e) {
        if (kDebugMode) log('Cache save failed for key $cacheKey: $e');
      }
      return Success(result);
    } on RequestCancelledException {
      return const Error(RequestCancelledFailure());
    } on ServerException catch (e) {
      final Failure failure = Failure.fromException(e);
      if (failure.revokesCachedContent) {
        onInvalidate?.call(cacheKey);
        return Error(failure);
      }
      return _resolveFromCache(
        cacheKey,
        fromCacheJson,
        e.message,
        onRead,
        failure: failure,
      );
    } catch (e, s) {
      if (kDebugMode) log('Unexpected error: ${e.toString()}', stackTrace: s);
      return _resolveFromCache(cacheKey, fromCacheJson, e.toString(), onRead);
    }
  }
}

Result<BaseModel<M>, Failure> _resolveFromCache<M>(
  String cacheKey,
  M Function(Map<String, dynamic> json) fromCacheJson,
  String errorMessage,
  Map<String, dynamic>? Function(String key) onRead, {
  Failure? failure,
}) {
  try {
    final cached = onRead(cacheKey);
    if (cached.isNotNull) {
      return Success(
        BaseModel(
          key: 'fromCache',
          msg: errorMessage,
          data: fromCacheJson(cached!),
        ),
      );
    }
  } catch (_) {}
  return Error(failure ?? Failure(errorMessage));
}

extension ErrorHandler<T> on Future<T> {
  Future<Result<T, Failure>> handleCallbackWithFailure() async {
    try {
      return await _defaultHandler();
    } catch (e, s) {
      _logUnexpectedError(e, s);
      return Error(Failure(_getErrorMessage(e)));
    }
  }

  Future<Result<T, Failure>> _defaultHandler() async {
    try {
      final result = await this;
      return Success(result);
    } on RequestCancelledException {
      return const Error(RequestCancelledFailure());
    } on ServerException catch (e) {
      return Error(Failure.fromException(e));
    }
  }

  void _logUnexpectedError(Object e, StackTrace s) {
    if (kDebugMode) {
      log('Unexpected error: ${e.toString()}', stackTrace: s);
    }
  }

  String _getErrorMessage(Object e) {
    return kDebugMode ? e.toString() : 'An unexpected error occurred';
  }
}
