import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';

class PropertyFilterOptionsCubit
    extends AsyncCubit<PropertyFilterOptionsModel> {
  PropertyFilterOptionsCubit()
    : super(const PropertyFilterOptionsModel.initial());

  Future<void> getFilterOptions() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyFilterOptionsModel>(
          api: ApiConstants.propertyFilterOptions,
          httpRequestType: HttpRequestType.get,
          mapper: (json) => PropertyFilterOptionsModel.fromJson(
            json is Map<String, dynamic> ? json : const {},
          ),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
