import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import '../../data/models/comparison_property.dart';

class PropertyComparisonCubit
    extends VerifiedActionCubit<List<ComparisonProperty>> {
  PropertyComparisonCubit() : super(const []);
  Future<void> load(List<String> propertyIds) async {
    if (isClosed || isLoading) return;
    final ids = propertyIds.where((id) => id.isNotEmpty).toSet().take(3);
    await executeAsyncWithBaseModel(
      operation: () async {
        final properties = await Future.wait(
          ids.map((id) async {
            final result = await baseCrudUseCase.call(
              CrudBaseParmas<PropertyDetailsModel>(
                api: ApiConstants.propertyDetails(id),
                httpRequestType: HttpRequestType.get,
                cacheKey:
                    'property_comparison_${UserModel.currentUser?.id ?? 'guest'}_$id',
                mapper: (json) => PropertyDetailsModel.fromJson(
                  Map<String, dynamic>.from(json as Map),
                ),
                fromCacheJson: PropertyDetailsModel.fromJson,
                toJson: (property) => property.toJson(),
              ),
            );
            return result.when(
              (response) => ComparisonProperty(
                propertyId: id,
                property: response.data,
                isCached: response.key == 'fromCache',
              ),
              (failure) =>
                  ComparisonProperty(propertyId: id, error: failure.message),
            );
          }),
        );
        return Success(BaseModel(key: 'success', msg: '', data: properties));
      },
      withInternetInterceptor: true,
    );
  }
}
