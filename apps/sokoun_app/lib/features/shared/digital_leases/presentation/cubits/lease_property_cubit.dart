import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

/// The owner collection is a summary; offer selection uses the full inventory.
class LeasePropertyCubit extends AsyncCubit<PropertyDetailsModel> {
  LeasePropertyCubit() : super(const PropertyDetailsModel.initial());
  bool _isCached = true;
  bool get isCached => _isCached;

  Future<void> load(String propertyId) async {
    if (isClosed || isLoading || propertyId.isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: ApiConstants.propertyDetails(propertyId),
        key: premiumCacheKey('lease_property', [propertyId]),
        fromJson: PropertyDetailsModel.fromJson,
        valid: (property) => property.id == propertyId,
        toJson: (property) => property.toJson(),
      ),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
