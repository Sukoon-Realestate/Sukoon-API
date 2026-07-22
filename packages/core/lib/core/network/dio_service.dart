import 'dart:developer';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../../config/language/languages.dart' show Languages;
import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../error/exceptions.dart';
import '../base_crud/code/domain/usecases/pagination_response.dart';
import '../extensions/object.dart';
import '../helpers/cache_service.dart';
import '../helpers/helpers.dart';
import 'extensions.dart';
import 'fire_store.dart';
import 'interceptors/log_interceptor.dart';
import 'interceptors/unauthorized_interceptor.dart';
import 'network_request.dart';
import 'network_service.dart';

class DioService implements NetworkService {
  late final Dio _dio;
  DioService() {
    _initDio();
  }

  void _initDio() {
    _dio = Dio()
      // ..options.baseUrl = ConstantManager.testUrl
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
            Languages.currentLanguage.locale.languageCode,
      })
      ..options.responseType = ResponseType.json;

    _dio.interceptors.add(UnauthorizedInterceptor(_dio));
    if (kDebugMode) {
      _dio.interceptors.add(LoggerInterceptor());
    }
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
  Future<void> updateBaseUrl() async {
    final baseUrl = await getBaseUrl();
    _dio.options.baseUrl = baseUrl;
  }

  @override
  void setToken(String token) {
    _dio.options.headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
  }

  @override
  void removeToken() {
    _dio.options.headers.remove(HttpHeaders.authorizationHeader);
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
      _handleIncomingResponse(
        path: networkRequest.path,
        response: e.response?.data,
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
}
