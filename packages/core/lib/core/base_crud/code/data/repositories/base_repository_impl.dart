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
      GetBaseEntityParams? param) async {
    return await baseRemoteDataSource
        .getData<T>(param)
        .handleCallbackWithFailure();
  }

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(CrudBaseParmas<T> params) async {
    if (params.mapper.isNotNull && params.toJson.isNotNull && params.httpRequestType == HttpRequestType.get) {
      return await _crudCallWithCache(params);
    }
    return await baseRemoteDataSource.crudCall<T>(params).handleCallbackWithFailure();
  }

  Future<Result<BaseModel<T>, Failure>> _crudCallWithCache<T>(
      CrudBaseParmas<T> params) {
    return baseRemoteDataSource.crudCall<T>(params).handleCallbackWithCache(
      cacheKey: params.cacheKey ?? params.api,
      fromCacheJson: params.fromCacheJson ?? (json) => params.mapper!(json),
      toJson: params.toJson!,
      onSave: baseLocalDataSource.save,
      onRead: baseLocalDataSource.read,
    );
  }
}
