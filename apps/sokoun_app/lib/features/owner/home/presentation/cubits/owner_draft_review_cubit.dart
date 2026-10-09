import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

class OwnerDraftReviewCubit extends AsyncCubit<PropertyDetailsModel> {
  OwnerDraftReviewCubit() : super(const PropertyDetailsModel.initial());
  Future<PropertyDetailsModel?> fresh(String id) async {
    PropertyDetailsModel? current;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyDetailsModel>(
          api: ApiConstants.propertyDetails(id),
          httpRequestType: HttpRequestType.get,
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheKey: 'owner_draft_review_$id',
          mapper: (json) => PropertyDetailsModel.fromJson(json),
          fromCacheJson: PropertyDetailsModel.fromJson,
          toJson: (value) => value.toJson(),
        ),
      ),
      onSuccess: (response) {
        if (response.data.id == id) current = response.data;
      },
      withInternetInterceptor: true,
    );
    return current;
  }
}
