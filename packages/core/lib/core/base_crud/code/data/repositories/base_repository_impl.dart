part of '../base_data_imports.dart';

@LazySingleton(as: BaseRepository)
class BaseRepositoryImpl implements BaseRepository {
  final BaseRemoteDataSource baseRemoteDataSource;
  final BaseLocalDataSource baseLocalDataSource;

  BaseRepositoryImpl({
    required this.baseRemoteDataSource,
    required this.baseLocalDataSource,
  });

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) async {
    return await baseRemoteDataSource
        .getData<T>(param)
        .handleCallbackWithFailure();
  }

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    if (params.cachePolicy?.persist != false &&
        params.mapper.isNotNull &&
        params.toJson.isNotNull &&
        params.httpRequestType == HttpRequestType.get) {
      return await _crudCallWithCache(params);
    }
    return await baseRemoteDataSource
        .crudCall<T>(params)
        .handleCallbackWithFailure();
  }

  Future<Result<BaseModel<T>, Failure>> _crudCallWithCache<T>(
    CrudBaseParmas<T> params,
  ) {
    final int generation = AccountSession.generation;
    final String cacheScope = ReadCacheContext.scope;
    return baseRemoteDataSource
        .crudCall<T>(params)
        .handleCallbackWithCache(
          cacheKey: params.cacheKey ?? params.api,
          fromCacheJson: params.fromCacheJson ?? (json) => params.mapper!(json),
          toJson: params.toJson!,
          onInvalidate: (key) {
            if (generation == AccountSession.generation &&
                cacheScope == ReadCacheContext.scope) {
              ObjectBoxCacheService.remove(key);
            }
          },
          onSave: (key, json) {
            if (generation == AccountSession.generation &&
                cacheScope == ReadCacheContext.scope &&
                !(params.cancelToken?.isCancelled ?? false)) {
              if (params.cachePolicy?.publicContent == true && json.isEmpty) {
                ObjectBoxCacheService.remove(key);
                return;
              }
              if (params.cachePolicy != null) {
                ObjectBoxCacheService.save(
                  key,
                  json,
                  policy: params.cachePolicy,
                );
              } else {
                baseLocalDataSource.save(key, json);
              }
            }
          },
          onRead: (key) =>
              generation == AccountSession.generation &&
                  cacheScope == ReadCacheContext.scope &&
                  !(params.cancelToken?.isCancelled ?? false)
              ? params.cachePolicy != null
                    ? ObjectBoxCacheService.read(
                        key,
                        policy: params.cachePolicy,
                      )
                    : baseLocalDataSource.read(key)
              : null,
        );
  }
}
