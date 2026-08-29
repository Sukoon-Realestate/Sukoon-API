import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/saved_properties_response.dart';

abstract final class FavoritesData {
  static Future<SavedPropertiesResponse> getSavedProperties({
    required int page,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.savedProperties,
        queryParameters: {'page': page},
      ),
      mapper: (json) => SavedPropertiesResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    return response.data;
  }
}
