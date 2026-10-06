import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'models/property_review.dart';

abstract final class PropertyReviewsData {
  static Future<(List<PropertyReview>, PaginationData)> getPage({
    required String propertyId,
    required int page,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: ApiConstants.propertyReviews(propertyId),
        method: RequestMethod.get,
        queryParameters: {'page': page, 'page_size': 10},
      ),
      mapper: (json) {
        final Map<String, dynamic> data = Map<String, dynamic>.from(
          json as Map,
        );
        return (
          (data['results'] as List? ?? const [])
              .whereType<Map>()
              .map(
                (item) =>
                    PropertyReview.fromJson(Map<String, dynamic>.from(item)),
              )
              .toList(),
          PaginationData(
            perPage: (data['per_page'] as num?)?.toInt() ?? 10,
            totalPages: (data['total_pages'] as num?)?.toInt() ?? 1,
          ),
        );
      },
    );
    return response.data;
  }
}
