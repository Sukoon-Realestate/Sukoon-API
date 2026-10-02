import 'dart:developer';
import 'dart:io';

import 'package:cookie_jar/cookie_jar.dart';
import 'package:dio/dio.dart';
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
import 'account_session.dart';
import 'extensions.dart';
import 'fire_store.dart';
import 'interceptors/cookie_token_header_interceptor.dart';
import 'interceptors/log_interceptor.dart';
import 'interceptors/unauthorized_interceptor.dart';
import 'interceptors/session_cookie_manager.dart';
import 'network_request.dart';
import 'network_service.dart';
import 'session_auth_service.dart';
import 'session_refresh_coordinator.dart';
import 'session_token_cookies.dart';
import 'network_logging_policy.dart';

class DioService implements NetworkService, SessionAuthService {
  DioService({
    String initialBaseUrl = '',
    String? initialLanguageCode,
    Future<Directory> Function()? cookieDirectoryProvider,
    HttpClientAdapter? httpClientAdapter,
  }) : _cookieDirectoryProvider =
           cookieDirectoryProvider ?? getApplicationSupportDirectory {
    _initDio(
      initialBaseUrl: initialBaseUrl,
      initialLanguageCode: initialLanguageCode,
    );
    if (httpClientAdapter != null) _dio.httpClientAdapter = httpClientAdapter;
  }

  late final Dio _dio;
  final Future<Directory> Function() _cookieDirectoryProvider;
  PersistCookieJar? _cookieJar;
  SessionCookieManager? _sessionCookies;
  Future<void>? _cookieInitialization;
  late final SessionRefreshCoordinator _refreshCoordinator =
      SessionRefreshCoordinator(refresh: _performSessionRefresh);

  void _initDio({
    required String initialBaseUrl,
    required String? initialLanguageCode,
  }) {
    _dio = Dio()
      ..options.baseUrl = initialBaseUrl
      ..options.connectTimeout = const Duration(
        seconds: ConstantManager.connectTimeoutDuration,
      )
      ..options.sendTimeout = const Duration(
        seconds: ConstantManager.sendTimeoutDuration,
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
    final SessionCookieManager manager = SessionCookieManager(
      cookieJar,
      refreshRevision: () => _refreshCoordinator.revision,
    );
    _sessionCookies = manager;
    _dio.interceptors
      ..insert(0, manager)
      ..insert(1, CookieTokenHeaderInterceptor(cookieJar: cookieJar))
      ..insert(
        2,
        UnauthorizedInterceptor(
          dio: _dio,
          refreshCoordinator: _refreshCoordinator,
          canRefreshSession: () async {
            final Uri refreshUri = Uri.parse(
              _dio.options.baseUrl,
            ).resolve(ApiConstants.refreshToken);
            final List<Cookie> cookies = await cookieJar.loadForRequest(
              refreshUri,
            );

            return SessionTokenCookies.refreshToken(cookies) != null;
          },
          onSessionExpired: (generation) =>
              manager.clear(generation: generation, expire: true),
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
    final int generation = AccountSession.generation;
    final Uri? baseUri = await getBaseUri();
    if (baseUri == null) return null;

    final List<Cookie> cookies = await _cookieJar!.loadForRequest(baseUri);
    if (generation != AccountSession.generation) return null;
    return SessionTokenCookies.accessToken(cookies);
  }

  @override
  Future<bool> refreshSession() async {
    final int generation = AccountSession.generation;
    try {
      await _refreshCoordinator.refresh(generation);
      final String? token = await getAccessToken();
      return generation == AccountSession.generation &&
          (token?.isNotEmpty ?? false);
    } catch (_) {
      return false;
    }
  }

  Future<void> _performSessionRefresh(int generation) async {
    final Uri? baseUri = await getBaseUri();
    if (baseUri == null) throw StateError('No API base URI configured.');
    final List<Cookie> cookies = await _cookieJar!.loadForRequest(
      baseUri.resolve(ApiConstants.refreshToken),
    );
    if (generation != AccountSession.generation) {
      throw const RequestCancelledException();
    }
    if (SessionTokenCookies.refreshToken(cookies) == null) {
      await _sessionCookies!.clear(generation: generation, expire: true);
      throw StateError('No refresh token available.');
    }
    try {
      await _dio.post<void>(
        ApiConstants.refreshToken,
        options: Options(
          extra: {SessionCookieManager.generationKey: generation},
        ),
      );
    } on DioException catch (error) {
      if (error.response?.statusCode == HttpStatus.unauthorized &&
          generation == AccountSession.generation) {
        await _sessionCookies!.clear(generation: generation, expire: true);
      }
      rethrow;
    }
  }

  @override
  Future<void> updateBaseUrl() async {
    final baseUrl = await getBaseUrl();
    _dio.options.baseUrl = baseUrl;
  }

  @override
  Future<bool> hasSessionCookies() async {
    final int generation = AccountSession.generation;
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
    if (generation != AccountSession.generation) return false;
    return SessionTokenCookies.accessToken(requestCookies) != null ||
        SessionTokenCookies.refreshToken(refreshCookies) != null;
  }

  @override
  Future<void> clearSessionCookies() async {
    final int generation = AccountSession.generation;
    await _ensureCookieManager();
    await _sessionCookies!.clear(generation: generation);
    _dio.options.headers
      ..remove(HttpHeaders.authorizationHeader)
      ..remove(HttpHeaders.cookieHeader);
  }

  void _handleIncomingResponse({
    required String path,
    required dynamic response,
  }) {
    if (NetworkLoggingPolicy.isSensitive(path)) return;
    if (FireStoreService.isInitialized && kReleaseMode) {
      final finalResponse = response is String ? {'data': response} : response;
      FireStoreService.instance.storeResponse(
        path: path,
        response: finalResponse,
      );
    }
  }

  @override
  Future<BaseModel<Model>> callApi<Model>(
    NetworkRequest networkRequest, {
    Model Function(dynamic json)? mapper,
  }) async {
    final int generation = AccountSession.generation;
    try {
      if (networkRequest.cancelToken?.isCancelled ?? false) {
        throw networkRequest.cancelToken!.cancelError!;
      }
      await _ensureCookieManager();
      if (_dio.options.baseUrl.isNull || _dio.options.baseUrl.isEmpty) {
        await updateBaseUrl();
      }
      if (networkRequest.cancelToken?.isCancelled ?? false) {
        throw networkRequest.cancelToken!.cancelError!;
      }
      await networkRequest.prepareRequestData();
      if (networkRequest.cancelToken?.isCancelled ?? false) {
        throw networkRequest.cancelToken!.cancelError!;
      }
      if (FireStoreService.isInitialized &&
          kReleaseMode &&
          !NetworkLoggingPolicy.isSensitive(networkRequest.path)) {
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
        onReceiveProgress: networkRequest.onReceiveProgress,
        cancelToken: networkRequest.cancelToken,
        options: Options(
          method: networkRequest.asString(),
          headers: networkRequest.headers,
          sendTimeout: networkRequest.sendTimeout,
          extra: {SessionCookieManager.generationKey: generation},
        ),
      );

      if (networkRequest.cancelToken?.isCancelled ?? false) {
        throw networkRequest.cancelToken!.cancelError!;
      }
      if (generation != AccountSession.generation) {
        throw const RequestCancelledException();
      }

      // Password recovery returns 204 with no JSON response envelope.
      final dynamic responseBody = response.statusCode == HttpStatus.noContent
          ? const <String, dynamic>{'data': null}
          : response.data;
      _handleIncomingResponse(
        path: networkRequest.path,
        response: responseBody,
      );
      if (mapper != null) {
        return BaseModel.fromJson(responseBody, jsonToModel: mapper);
      } else {
        return BaseModel.fromJson(responseBody);
      }
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) throw const RequestCancelledException();
      if (!NetworkLoggingPolicy.isSensitive(networkRequest.path)) {
        log('error is ${e.response?.data}');
      }
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
          case HttpStatus.forbidden:
            throw ForbiddenException(
              error.response?.data['message'] ?? LocaleKeys.unauthorized,
            );
          case HttpStatus.notFound:
            throw NotFoundException(
              error.response?.data['message'] ?? LocaleKeys.notFound,
            );
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
        throw const RequestCancelledException();
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
