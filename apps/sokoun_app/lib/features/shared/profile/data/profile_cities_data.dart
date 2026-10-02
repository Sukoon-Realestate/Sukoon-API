part of '../imports.dart';

abstract final class ProfileCitiesData {
  static const cacheKey = 'profile_city_choices';
  static const pageSize = 10;

  static Future<(List<ProfileCity>, PaginationData)> getPage(int page) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: ApiConstants.propertyCities,
        method: RequestMethod.get,
        queryParameters: {'page': page, 'page_size': pageSize},
      ),
      mapper: (json) {
        final Map<String, dynamic> data = _profileJsonMap(json);
        final cities = (data['results'] as List? ?? const [])
            .whereType<Map>()
            .map(
              (item) => ProfileCity.fromJson(Map<String, dynamic>.from(item)),
            )
            .where((city) => city.id.isNotEmpty)
            .toList(growable: false);
        final count = _profileInt(data['count']);
        final int totalPages = count > 0
            ? (count + pageSize - 1) ~/ pageSize
            : data['next'] != null
            ? page + 1
            : page;
        return (
          cities,
          PaginationData(perPage: pageSize, totalPages: totalPages),
        );
      },
    );
    return response.data;
  }
}
