import 'dart:math' as math;
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'models/profile_contract_content.dart';
import 'profile_json.dart';

abstract final class ProfileContractsData {
  static const String cacheKey = 'tenant_contracts_v1';
  static Future<(List<ProfileContractContent>, PaginationData)> getPage(
    int page,
  ) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: ApiConstants.accountContracts,
        method: RequestMethod.get,
        queryParameters: {'page': page, 'page_size': 20},
      ),
      mapper: (json) => parsePage(profileJsonMap(json), page: page),
    );
    return response.data;
  }

  static (List<ProfileContractContent>, PaginationData) parsePage(
    Map<String, dynamic> json, {
    required int page,
  }) {
    final int perPage = math.max(1, profileInt(json['per_page'] ?? 20));
    final int pages = json['total_pages'] != null
        ? profileInt(json['total_pages'])
        : json['count'] != null
        ? (profileInt(json['count']) / perPage).ceil()
        : json['next'] == null
        ? page
        : page + 1;
    return (
      (json['results'] as List? ?? const [])
          .whereType<Map>()
          .map((item) => ProfileContractContent.fromJson(profileJsonMap(item)))
          .toList(growable: false),
      PaginationData(perPage: perPage, totalPages: math.max(1, pages)),
    );
  }
}
