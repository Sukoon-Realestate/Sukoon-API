import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import '../../data/models/advanced_analytics_content.dart';

class AdvancedAnalyticsCubit extends AsyncCubit<AdvancedAnalyticsContent> {
  AdvancedAnalyticsCubit() : super(const AdvancedAnalyticsContent.initial());
  int _revision = 0;
  Future<void> load({
    required String propertyId,
    required int periodDays,
    required String language,
  }) async {
    if (isClosed ||
        propertyId.isEmpty ||
        !const [7, 30, 90].contains(periodDays)) {
      return;
    }
    final revision = ++_revision;
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: PremiumApiConstants.analytics(propertyId),
        key: premiumCacheKey('analytics', [propertyId, periodDays, language]),
        query: {'period_days': periodDays, 'lang': language},
        fromJson: AdvancedAnalyticsContent.fromJson,
        valid: (content) =>
            content.propertyId == propertyId &&
            content.periodDays == periodDays,
        toJson: (content) => content.toJson(),
      ),
      withInternetInterceptor: true,
      shouldApplyResult: () => revision == _revision,
    );
  }
}
