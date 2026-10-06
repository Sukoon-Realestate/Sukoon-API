import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import '../../data/models/digital_lease.dart';

class DigitalLeaseDetailsCubit extends AsyncCubit<DigitalLease> {
  DigitalLeaseDetailsCubit() : super(const DigitalLease.initial());
  bool _isCached = true;
  bool get isCached => _isCached;
  Future<void> load(String id) async {
    if (id.isEmpty || isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: PremiumApiConstants.lease(id),
        key: premiumCacheKey('digital_lease', [id]),
        fromJson: DigitalLease.fromJson,
        toJson: (model) => model.toJson(),
      ),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
