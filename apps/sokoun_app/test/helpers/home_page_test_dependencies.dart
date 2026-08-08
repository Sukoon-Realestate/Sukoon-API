import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';

/// Registers a fake [BaseCrudUseCase] so widget tests can pump screens
/// that create `AsyncCubit`s (e.g. `HomePageCubit`) without a network.
void registerHomePageTestDependencies() {
  if (injector.isRegistered<BaseCrudUseCase>()) {
    return;
  }
  injector.registerLazySingleton<BaseCrudUseCase>(
    () => BaseCrudUseCase(repository: _FakeBaseRepository()),
  );
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
        ? params.mapper!(const <String, dynamic>{'count': 0, 'results': []})
        : throw UnimplementedError();
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }
}
