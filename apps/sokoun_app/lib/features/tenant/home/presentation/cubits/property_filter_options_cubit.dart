import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/config/language/languages.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';

class PropertyFilterOptionsCubit
    extends AsyncCubit<PropertyFilterOptionsModel> {
  PropertyFilterOptionsCubit({PropertyFilterOptionsModel? initialOptions})
    : super(initialOptions ?? const PropertyFilterOptionsModel.initial()) {
    if (initialOptions != null) emit(state.success(data: initialOptions));
  }

  Future<void> getFilterOptions({
    void Function(PropertyFilterOptionsModel)? onLoaded,
  }) async {
    if (isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyFilterOptionsModel>(
          api: ApiConstants.propertyFilterOptions,
          httpRequestType: HttpRequestType.get,
          cacheKey:
              'property_filter_options_${Languages.currentLanguage.languageCode}',
          mapper: (json) => PropertyFilterOptionsModel.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
          fromCacheJson: PropertyFilterOptionsModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      onSuccess: (model) => onLoaded?.call(model.data),
      withInternetInterceptor: true,
    );
  }
}
