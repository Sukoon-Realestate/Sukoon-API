import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/feature_configuration_data.dart';
import '../../data/models/feature_configuration.dart';

class FeatureConfigurationCubit extends AsyncCubit<FeatureConfiguration> {
  FeatureConfigurationCubit() : super(const FeatureConfiguration.initial());
  bool isCached = false;
  Future<void> load(AppWorkspace workspace, {required String language}) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () async {
        final result = await FeatureConfigurationData.get(
          workspace,
          language: language,
        );
        return result.when((response) {
          if (response.data.workspace != workspace.name) {
            return Error<BaseModel<FeatureConfiguration>, Failure>(
              ServerFailure(LocaleKeys.paidInvalidResponse),
            );
          }
          isCached = response.key == 'fromCache';
          return Success<BaseModel<FeatureConfiguration>, Failure>(response);
        }, (error) => Error<BaseModel<FeatureConfiguration>, Failure>(error));
      },
      withInternetInterceptor: true,
    );
  }
}
