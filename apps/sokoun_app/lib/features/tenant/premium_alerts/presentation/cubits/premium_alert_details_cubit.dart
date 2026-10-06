import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import '../../data/models/premium_search_alert.dart';

class PremiumAlertDetailsCubit extends AsyncCubit<PremiumSearchAlert> {
  PremiumAlertDetailsCubit() : super(const PremiumSearchAlert.initial());
  Future<void> load(String id) async {
    if (id.isEmpty || isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: PremiumApiConstants.alert(id),
        key: premiumCacheKey('premium_search_alert', [id]),
        fromJson: PremiumSearchAlert.fromJson,
        toJson: (model) => model.toJson(),
      ),
      withInternetInterceptor: true,
    );
  }
}
