// GENERATED CODE - DO NOT MODIFY BY HAND

// **************************************************************************
// InjectableConfigGenerator
// **************************************************************************

// ignore_for_file: type=lint
// coverage:ignore-file

// ignore_for_file: no_leading_underscores_for_library_prefixes
import 'package:get_it/get_it.dart' as _i174;
import 'package:injectable/injectable.dart' as _i526;

import '../../base_crud/code/data/base_data_imports.dart' as _i241;
import '../../base_crud/code/domain/base_domain_imports.dart' as _i267;
import '../../base_crud/code/presentation/cubit/get_base_name_and_id/get_base_name_and_id_cubit.dart'
    as _i30;
import '../../network/network_service.dart' as _i632;

extension GetItInjectableX on _i174.GetIt {
// initializes the registration of main-scope dependencies inside of GetIt
  _i174.GetIt init({
    String? environment,
    _i526.EnvironmentFilter? environmentFilter,
  }) {
    final gh = _i526.GetItHelper(
      this,
      environment,
      environmentFilter,
    );
    gh.factory<_i30.GetBaseEntityCubit<dynamic>>(
        () => _i30.GetBaseEntityCubit());
    gh.lazySingleton<_i241.BaseLocalDataSource>(
        () => _i241.BaseLocalDataSourceImpl());
    gh.lazySingleton<_i241.BaseRemoteDataSource>(() =>
        _i241.BaseRemoteDataSourceImpl(dioService: gh<_i632.NetworkService>()));
    gh.lazySingleton<_i267.BaseRepository>(() => _i241.BaseRepositoryImpl(
          baseRemoteDataSource: gh<_i241.BaseRemoteDataSource>(),
          baseLocalDataSource: gh<_i241.BaseLocalDataSource>(),
        ));
    gh.lazySingleton<_i267.BaseCrudUseCase>(
        () => _i267.BaseCrudUseCase(repository: gh<_i267.BaseRepository>()));
    gh.lazySingleton<_i267.GetBaseEntityUseCase>(() =>
        _i267.GetBaseEntityUseCase(repository: gh<_i267.BaseRepository>()));
    return this;
  }
}
