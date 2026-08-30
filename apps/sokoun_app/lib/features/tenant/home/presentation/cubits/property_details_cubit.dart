import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class PropertyDetailsCubit extends AsyncCubit<PropertyDetailsModel> {
  PropertyDetailsCubit() : super(PropertyDetailsModel.initial());

  Future<void> getPropertyDetails(String id) async {
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(id),
          httpRequestType: HttpRequestType.get,
          cacheKey: 'property_details_$id',
          mapper: (json) => PropertyDetailsModel.fromJson(json),
          fromCacheJson: PropertyDetailsModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
