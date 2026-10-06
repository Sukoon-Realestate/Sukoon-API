part of '../base_data_imports.dart';

abstract class BaseLocalDataSource {
  void save(String key, Map<String, dynamic> json);
  Map<String, dynamic>? read(String key);
}

@LazySingleton(as: BaseLocalDataSource)
class BaseLocalDataSourceImpl implements BaseLocalDataSource {
  @override
  void save(String key, Map<String, dynamic> json) =>
      ObjectBoxCacheService.save(key, json);

  @override
  Map<String, dynamic>? read(String key) => ObjectBoxCacheService.read(key);
}
