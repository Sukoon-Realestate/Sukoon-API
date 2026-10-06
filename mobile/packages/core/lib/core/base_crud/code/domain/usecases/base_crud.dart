// ignore_for_file: public_member_api_docs, sort_constructors_first
part of '../base_domain_imports.dart';

@LazySingleton()
class BaseCrudUseCase {
  final BaseRepository repository;
  BaseCrudUseCase({required this.repository});
  Future<Result<BaseModel<T>, Failure>> call<T>(CrudBaseParmas<T> param) async {
    return await repository.crudCall<T>(param);
  }
}

class CrudResponse {}

enum HttpRequestType {
  get(requestMethod: RequestMethod.get),
  post(requestMethod: RequestMethod.post),
  put(requestMethod: RequestMethod.put),
  patch(requestMethod: RequestMethod.patch),
  delete(requestMethod: RequestMethod.delete);

  final RequestMethod requestMethod;
  const HttpRequestType({required this.requestMethod});
}

class CrudBaseParmas<T> {
  final String api;
  final String? cacheKey;
  final HttpRequestType httpRequestType;
  final Map<String, dynamic>? body;
  final Map<String, dynamic>? queryParameters;
  final T Function(dynamic json)? mapper;
  final T Function(Map<String, dynamic> json)? fromCacheJson;
  final bool isFromData;
  final void Function(int, int)? onSendProgress;
  final void Function(int, int)? onReceiveProgress;
  final CancelToken? cancelToken;
  final Duration? sendTimeout;
  final Map<String, dynamic> Function(T)? toJson;
  CrudBaseParmas({
    required this.api,
    required this.httpRequestType,
    this.cacheKey,
    this.body,
    this.queryParameters,
    this.onSendProgress,
    this.onReceiveProgress,
    this.cancelToken,
    this.sendTimeout,
    this.isFromData = false,
    this.mapper,
    this.fromCacheJson,
    this.toJson,
  });

  CrudBaseParmas<T> copyWith({
    String? api,
    HttpRequestType? httpRequestType,
    Map<String, dynamic>? body,
    Map<String, dynamic>? queryParameters,
    T Function(dynamic)? mapper,
    T Function(Map<String, dynamic>)? fromCacheJson,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
    CancelToken? cancelToken,
    Duration? sendTimeout,
    bool? isFromData,
    String? cacheKey,
    Map<String, dynamic> Function(T)? toJson,
  }) {
    return CrudBaseParmas<T>(
      api: api ?? this.api,
      cacheKey: cacheKey ?? this.cacheKey,
      fromCacheJson: fromCacheJson ?? this.fromCacheJson,
      onSendProgress: onSendProgress ?? this.onSendProgress,
      onReceiveProgress: onReceiveProgress ?? this.onReceiveProgress,
      cancelToken: cancelToken ?? this.cancelToken,
      sendTimeout: sendTimeout ?? this.sendTimeout,
      httpRequestType: httpRequestType ?? this.httpRequestType,
      body: body ?? this.body,
      queryParameters: queryParameters ?? this.queryParameters,
      mapper: mapper ?? this.mapper,
      isFromData: isFromData ?? this.isFromData,
      toJson: toJson ?? this.toJson,
    );
  }
}
