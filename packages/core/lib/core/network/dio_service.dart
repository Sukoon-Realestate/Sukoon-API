import 'dart:developer';
import 'dart:io';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
import 'package:dio_cookie_manager/dio_cookie_manager.dart';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

import '../../config/language/languages.dart' show Languages;
import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../error/exceptions.dart';
import '../base_crud/code/domain/usecases/pagination_response.dart';
import '../extensions/object.dart';
import '../helpers/cache_service.dart';
import '../helpers/helpers.dart';
import 'api_endpoints.dart';
import 'extensions.dart';
import 'fire_store.dart';
import 'interceptors/cookie_token_header_interceptor.dart';
import 'interceptors/log_interceptor.dart';
import 'interceptors/unauthorized_interceptor.dart';
import 'network_request.dart';
import 'network_service.dart';
import 'session_auth_service.dart';

class DioService implements NetworkService, SessionAuthService {
  DioService({
    String initialBaseUrl = '',
    String? initialLanguageCode,
    Future<Directory> Function()? cookieDirectoryProvider,
  }) : _cookieDirectoryProvider =
           cookieDirectoryProvider ?? getApplicationSupportDirectory {
    _initDio(
      initialBaseUrl: initialBaseUrl,
      initialLanguageCode: initialLanguageCode,
    );
  }

  late final Dio _dio;
  final Future<Directory> Function() _cookieDirectoryProvider;
  PersistCookieJar? _cookieJar;
  Future<void>? _cookieInitialization;
  Future<bool>? _sessionRefresh;

  void _initDio({
    required String initialBaseUrl,
    required String? initialLanguageCode,
  }) {
    _dio = Dio()
      ..options.baseUrl = initialBaseUrl
      ..options.connectTimeout = const Duration(
        seconds: ConstantManager.connectTimeoutDuration,
      )
      ..options.receiveTimeout = const Duration(
        seconds: ConstantManager.recieveTimeoutDuration,
      )
      ..options.headers.addAll({
        HttpHeaders.acceptHeader: ContentType.json,
        Headers.contentTypeHeader: Headers.jsonContentType,
        HttpHeaders.acceptLanguageHeader:
            initialLanguageCode ??
            Languages.currentLanguage.locale.languageCode,
      })
      ..options.responseType = ResponseType.json;

    if (kDebugMode) {
      _dio.interceptors.add(LoggerInterceptor());
    }
  }

  Future<void> _ensureCookieManager() {
    final Future<void>? initialization = _cookieInitialization;
    if (initialization != null) {
      return initialization;
    }

    final Future<void> nextInitialization = _initCookieManager();
    _cookieInitialization = nextInitialization;
    return nextInitialization;
  }

  Future<void> _initCookieManager() async {
    final Directory supportDirectory = await _cookieDirectoryProvider();
    final String cookiePath = [
      supportDirectory.path,
      'network_cookies',
    ].join(Platform.pathSeparator);
    final PersistCookieJar cookieJar = PersistCookieJar(
      persistSession: true,
      ignoreExpires: false,
      storage: FileStorage(cookiePath),
    );
    await cookieJar.forceInit();

    _cookieJar = cookieJar;
    _dio.interceptors
      ..insert(0, CookieManager(cookieJar))
      ..insert(1, CookieTokenHeaderInterceptor(cookieJar: cookieJar))
      ..insert(
        2,
        UnauthorizedInterceptor(
          dio: _dio,
          canRefreshSession: () async {
            final Uri refreshUri = Uri.parse(
              _dio.options.baseUrl,
            ).resolve(ApiConstants.refreshToken);
            final List<Cookie> cookies = await cookieJar.loadForRequest(
              refreshUri,
            );

            return cookies.isNotEmpty;
          },
          onSessionExpired: cookieJar.deleteAll,
        ),
      );
  }

  Future<String> getBaseUrl() async {
    final bool isDev = Helpers.currentFlavor.isDev;

    final String primaryKey = isDev
        ? SecureLocalVariableKeys.devBaseUrlKey
        : SecureLocalVariableKeys.baseUrlKey;

    log('the primaryKey is $primaryKey');
    final String primary = await SecureStorage.read(primaryKey) ?? '';
    return primary;
  }

  @override
  Future<Uri?> getBaseUri() async {
    await _ensureCookieManager();
    if (_dio.options.baseUrl.isEmpty) {
      await updateBaseUrl();
    }

    final Uri? uri = Uri.tryParse(_dio.options.baseUrl);
    if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
      return null;
    }
    return uri;
  }

  @override
  Future<String?> getAccessToken() async {
    final Uri? baseUri = await getBaseUri();
    if (baseUri == null) return null;

    final List<Cookie> cookies = await _cookieJar!.loadForRequest(baseUri);
    for (final Cookie cookie in cookies) {
      if (cookie.name == 'access_token' && cookie.value.isNotEmpty) {
        return cookie.value;
      }
    }
    return null;
  }

  @override
  Future<bool> refreshSession() {
    final Future<bool>? pendingRefresh = _sessionRefresh;
    if (pendingRefresh != null) return pendingRefresh;

    final Future<bool> refresh = _refreshSession();
    _sessionRefresh = refresh;
    return refresh.whenComplete(() {
      if (identical(_sessionRefresh, refresh)) {
        _sessionRefresh = null;
      }
    });
  }

  Future<bool> _refreshSession() async {
    try {
      final Uri? baseUri = await getBaseUri();
      if (baseUri == null) return false;

      final Uri refreshUri = baseUri.resolve(ApiConstants.refreshToken);
      final List<Cookie> cookies = await _cookieJar!.loadForRequest(refreshUri);
      final bool hasRefreshToken = cookies.any(
        (cookie) => cookie.name == 'refresh_token' && cookie.value.isNotEmpty,
      );
      if (!hasRefreshToken) return false;

      await _dio.post<void>(ApiConstants.refreshToken);
      return (await getAccessToken())?.isNotEmpty ?? false;
    } catch (_) {
      return false;
    }
  }

  @override
  Future<void> updateBaseUrl() async {
    final baseUrl = await getBaseUrl();
    _dio.options.baseUrl = baseUrl;
  }

  @override
  Future<bool> hasSessionCookies() async {
    await _ensureCookieManager();
    if (_dio.options.baseUrl.isEmpty) {
      await updateBaseUrl();
    }

    final Uri? baseUri = Uri.tryParse(_dio.options.baseUrl);
    if (baseUri == null || !baseUri.hasScheme || baseUri.host.isEmpty) {
      return false;
    }

    final List<Cookie> requestCookies = await _cookieJar!.loadForRequest(
      baseUri,
    );
    final List<Cookie> refreshCookies = await _cookieJar!.loadForRequest(
      baseUri.resolve(ApiConstants.refreshToken),
    );
    return requestCookies.isNotEmpty || refreshCookies.isNotEmpty;
  }

  @override
  Future<void> clearSessionCookies() async {
    await _ensureCookieManager();
    await _cookieJar!.deleteAll();
    _dio.options.headers
      ..remove(HttpHeaders.authorizationHeader)
      ..remove(HttpHeaders.cookieHeader);
  }

  void _handleIncomingResponse({
    required String path,
    required Map<String, dynamic> response,
  }) {
    if (FireStoreService.isInitialized && kReleaseMode) {
      FireStoreService.instance.storeResponse(path: path, response: response);
    }
  }

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    try {
      await _ensureCookieManager();
      if (_dio.options.baseUrl.isNull || _dio.options.baseUrl.isEmpty) {
        await updateBaseUrl();
      }
      await networkRequest.prepareRequestData();
      if (FireStoreService.isInitialized && kReleaseMode) {
        FireStoreService.instance.storeRequest(networkRequest);
      }
      final response = await _dio.request(
        networkRequest.path,
        data: networkRequest.hasBodyAndProgress()
            ? networkRequest.isFormData
                  ? FormData.fromMap(networkRequest.body!)
                  : networkRequest.body
            : networkRequest.body,
        queryParameters: networkRequest.queryParameters,
        onSendProgress: networkRequest.hasBodyAndProgress()
            ? networkRequest.onSendProgress
            : null,
        onReceiveProgress: networkRequest.hasBodyAndProgress()
            ? networkRequest.onReceiveProgress
            : null,
        options: Options(
          method: networkRequest.asString(),
          headers: networkRequest.headers,
        ),
      );

      _handleIncomingResponse(
        path: networkRequest.path,
        response: response.data,
      );
      if (mapper != null) {
        return BaseModel.fromJson(response.data, jsonToModel: mapper);
      } else {
        return BaseModel.fromJson(response.data);
      }
    } on DioException catch (e) {
      log('error is ${e.response?.data}');
      _handleIncomingResponse(
        path: networkRequest.path,
        response: e.response?.data ?? {'error': e.toString()},
      );
      return _handleError(e);
    }
  }

  dynamic _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        throw NoInternetConnectionException(LocaleKeys.checkInternet);
      case DioExceptionType.badResponse:
        switch (error.response!.statusCode) {
          case HttpStatus.badRequest:
            throw BadRequestException(
              error.response?.data['message'] ?? LocaleKeys.badRequest,
            );
          case HttpStatus.unauthorized:
            throw UnauthorizedException(
              error.response?.data['message'] ?? LocaleKeys.unauthorized,
            );
          case HttpStatus.locked:
            throw BlockedException(
              error.response?.data['message'] ?? LocaleKeys.unauthorized,
            );
          case HttpStatus.notFound:
            throw NotFoundException(LocaleKeys.notFound);
          case HttpStatus.conflict:
            throw ConflictException(
              error.response?.data['message'] ?? LocaleKeys.serverError,
            );
          case HttpStatus.internalServerError:
            throw InternalServerErrorException(
              error.response?.data['message'] ?? LocaleKeys.serverError,
            );
          default:
            throw ServerException(LocaleKeys.serverError);
        }
      case DioExceptionType.cancel:
        throw ServerException(LocaleKeys.intenetWeakness);
      case DioExceptionType.unknown:
        throw ServerException(
          error.response?.data['message'] ?? LocaleKeys.exceptionError,
        );
      default:
        throw ServerException(
          error.response?.data['message'] ?? LocaleKeys.exceptionError,
        );
    }
  }
}

final class SecureLocalVariableKeys {
  static const String baseUrlKey = "base_url";
  static const String devBaseUrlKey = "dev_base_url";
  static const String socetIoUrl = "socet_io_url";
  static const String fireStoreAvailabilityKey = "fire_store_availability_key";
  static const String minAppVersionKey = 'min_app_version';
}
