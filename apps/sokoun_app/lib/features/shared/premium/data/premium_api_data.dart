import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'premium_json.dart';
import 'premium_api_constants.dart';
import 'package:sokoun_app/features/main_view/data/account_access.dart';

abstract final class PremiumApiData {
  static Future<Result<BaseModel<T>, Failure>> get<T>({
    required String endpoint,
    required String key,
    required T Function(Map<String, dynamic>) fromJson,
    required Map<String, dynamic> Function(T) toJson,
    Map<String, dynamic>? query,
    bool Function(T)? valid,
  }) async {
    if (endpoint != PremiumApiConstants.configuration &&
        !AccountAccess.isVerified) {
      return Error(ServerFailure(LocaleKeys.accountVerificationRequired));
    }
    final generation = AccountSession.generation;
    final result = await injector<BaseCrudUseCase>().call(
      CrudBaseParmas<T>(
        api: endpoint,
        httpRequestType: HttpRequestType.get,
        queryParameters: query,
        cacheKey: AccountSession.cacheKey(key),
        mapper: (json) => fromJson(premiumMap(json)),
        fromCacheJson: fromJson,
        toJson: toJson,
      ),
    );
    if (endpoint != PremiumApiConstants.configuration &&
        !AccountAccess.isVerified) {
      return Error(ServerFailure(LocaleKeys.accountVerificationRequired));
    }
    return result.when(
      (response) =>
          generation == AccountSession.generation &&
              (valid?.call(response.data) ?? true)
          ? Success(response)
          : Error(ServerFailure(LocaleKeys.paidInvalidResponse)),
      Error.new,
    );
  }

  static Future<Result<BaseModel<T>, Failure>> mutate<T>({
    required String endpoint,
    required Map<String, dynamic> body,
    required T Function(Map<String, dynamic>) fromJson,
    required bool Function(T) valid,
    HttpRequestType method = HttpRequestType.post,
  }) async {
    if (!AccountAccess.isVerified) {
      return Error(ServerFailure(LocaleKeys.accountVerificationRequired));
    }
    final generation = AccountSession.generation;
    final result = await injector<BaseCrudUseCase>().call(
      CrudBaseParmas<T>(
        api: endpoint,
        httpRequestType: method,
        body: body,
        mapper: (json) => fromJson(premiumMap(json)),
      ),
    );
    if (!AccountAccess.isVerified) {
      return Error(ServerFailure(LocaleKeys.accountVerificationRequired));
    }
    return result.when(
      (response) =>
          generation == AccountSession.generation && valid(response.data)
          ? Success(response)
          : Error(ServerFailure(LocaleKeys.paidInvalidResponse)),
      Error.new,
    );
  }

  static Future<(List<T>, PaginationData)> page<T>({
    required String endpoint,
    required int page,
    required T Function(Map<String, dynamic>) fromJson,
    Map<String, dynamic> query = const {},
  }) async {
    AccountAccess.requireVerification();
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        path: endpoint,
        method: RequestMethod.get,
        queryParameters: {...query, 'page': page, 'page_size': 20},
      ),
      mapper: (json) =>
          parsePage(premiumMap(json), page: page, fromJson: fromJson),
    );
    AccountAccess.requireVerification();
    return response.data;
  }

  static (List<T>, PaginationData) parsePage<T>(
    Map<String, dynamic> json, {
    required int page,
    required T Function(Map<String, dynamic>) fromJson,
  }) {
    final perPage = (premiumInt(json['per_page']) ?? 20).clamp(1, 100);
    final count = premiumInt(json['count']);
    final pages =
        premiumInt(json['total_pages']) ??
        (count != null
            ? (count / perPage).ceil()
            : json['next'] == null
            ? page
            : page + 1);
    return (
      premiumMaps(json['results']).map(fromJson).toList(growable: false),
      PaginationData(perPage: perPage, totalPages: pages.clamp(1, 100000)),
    );
  }
}
