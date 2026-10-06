import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import '../../data/models/lease_configuration.dart';

class LeaseConfigurationCubit extends AsyncCubit<LeaseConfiguration> {
  LeaseConfigurationCubit() : super(const LeaseConfiguration.initial());
  bool _isCached = true;
  bool get isCached => _isCached;
  Future<void> load({required String language}) async {
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: PremiumApiConstants.leaseConfiguration,
        key: 'premium_lease_configuration_$language',
        query: {'lang': language},
        fromJson: LeaseConfiguration.fromJson,
        toJson: (model) => model.toJson(),
      ),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
