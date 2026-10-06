import 'dart:math' as math;
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'models/my_review.dart';

abstract final class MyReviewsData {
  static const cacheKey = 'my_reviews_v1';
  static Future<(List<MyReview>, PaginationData)> getPage(int page) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: ApiConstants.myRates,
        method: RequestMethod.get,
        queryParameters: {'page': page, 'page_size': 10},
      ),
      mapper: (json) =>
          parsePage(Map<String, dynamic>.from(json as Map), page: page),
    );
    return response.data;
  }

  static (List<MyReview>, PaginationData) parsePage(
    Map<String, dynamic> json, {
    required int page,
  }) {
    final List<MyReview> items = (json['results'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => MyReview.fromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);
    final int perPage = math.max(1, (json['per_page'] as num?)?.toInt() ?? 10);
    final int totalPages =
        (json['total_pages'] as num?)?.toInt() ??
        (json['count'] is num
            ? ((json['count'] as num) / perPage).ceil()
            : (json['next'] == null ? page : page + 1));
    return (
      items,
      PaginationData(perPage: perPage, totalPages: math.max(1, totalPages)),
    );
  }
}
