import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/api_endpoints.dart';

import '../../data/models/property_review_summary.dart';

class PropertyReviewSummaryCubit extends AsyncCubit<PropertyReviewSummary> {
  PropertyReviewSummaryCubit() : super(const PropertyReviewSummary.initial());

  Future<void> load({required String propertyId}) async {
    if (isClosed || isLoading || propertyId.isEmpty) return;
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        CrudBaseParmas<PropertyReviewSummary>(
          api: ApiConstants.propertyReviews(propertyId),
          httpRequestType: HttpRequestType.get,
          queryParameters: const {'page': 1, 'page_size': 10},
          cacheKey: 'property_review_summary_$propertyId',
          mapper: (json) => PropertyReviewSummary.fromJson(
            json is Map && json['summary'] is Map
                ? Map<String, dynamic>.from(json['summary'] as Map)
                : const {},
          ),
          fromCacheJson: PropertyReviewSummary.fromJson,
          toJson: (summary) => summary.toJson(),
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
