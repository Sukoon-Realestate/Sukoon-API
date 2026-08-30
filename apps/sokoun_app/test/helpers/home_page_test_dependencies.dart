import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:multiple_result/multiple_result.dart';

/// Registers a fake [BaseCrudUseCase] so widget tests can pump screens
/// that create `AsyncCubit`s (e.g. `HomePageCubit`) without a network.
void registerHomePageTestDependencies() {
  if (!injector.isRegistered<BaseCrudUseCase>()) {
    injector.registerLazySingleton<BaseCrudUseCase>(
      () => BaseCrudUseCase(repository: _FakeBaseRepository()),
    );
  }
  if (!injector.isRegistered<NetworkService>()) {
    injector.registerLazySingleton<NetworkService>(_FakeNetworkService.new);
  }
}

class _FakeNetworkService implements NetworkService {
  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    const Map<String, dynamic> response = {
      'count': 0,
      'per_page': 20,
      'total_pages': 1,
      'results': [],
    };
    final Model data = mapper == null ? response as Model : mapper(response);
    return BaseModel<Model>(key: '', msg: '', data: data);
  }

  @override
  Future<void> clearSessionCookies() async {}

  @override
  Future<bool> hasSessionCookies() async => false;

  @override
  Future<void> updateBaseUrl() async {}
}

class _FakeBaseRepository implements BaseRepository {
  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    final T data = params.mapper != null
        ? params.mapper!(const <String, dynamic>{
            'count': 0,
            'results': [],
            'banner': 'visit',
          })
        : throw UnimplementedError();
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }
}
