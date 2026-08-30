import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';

class PropertyTypesCubit extends AsyncCubit<PropertyTypesModel> {
  PropertyTypesCubit() : super(const PropertyTypesModel.initial());

  Future<void> getPropertyTypes() async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyTypesModel>(
          api: ApiConstants.propertyTypes,
          httpRequestType: HttpRequestType.get,
          cacheKey: 'property_types',
          mapper: (json) => PropertyTypesModel.fromJson(json),
          fromCacheJson: PropertyTypesModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
