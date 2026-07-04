import 'dart:developer';
import 'dart:io';
import 'package:dio/dio.dart';

import '../../config/language/languages.dart';
import 'backend_configuation.dart';

class ConfigurationInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers.addAll({
      HttpHeaders.acceptHeader: ContentType.json,
      Headers.contentTypeHeader: Headers.jsonContentType,
      'lang': Languages.currentLanguage.locale.languageCode
    });
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (BackendConfiguation.type.isPhp) {
      _handleError(response);
    }
    handler.next(response);
  }

  void _handleError(Response response) {
    final errorKey = response.data['key'];
    final errorMessage = response.data['msg'];

    log('response data $errorMessage $errorKey ${response.statusCode}');

    final statusCode = _mapErrorKeyToStatusCode(errorKey);
    if (statusCode != null) {
      throw DioException(
        type: DioExceptionType.badResponse,
        requestOptions: response.requestOptions,
        response: Response(
          requestOptions: response.requestOptions,
          data: {
            'message': errorMessage,
          },
          statusCode: statusCode,
        ),
        error: {
          'message': errorMessage,
        },
      );
    }
  }

  // bool isNeedApproval(String key) {
  //   if (key == 'needApproval') {
  //     UserCubit.instance.setUserStatus(UserStatus.needApproval);
  //   }
  //   UserCubit.instance.setUserStatus(UserStatus.needApproval);
  //   return false;
  // }

  int? _mapErrorKeyToStatusCode(String errorKey) {
    switch (errorKey) {
      case 'fail':
      case 'notApproved':
        return HttpStatus.badRequest;
      case 'unauthenticated':
        return HttpStatus.unauthorized;
      case 'blocked':
        return HttpStatus.locked;
      case 'exception':
        return HttpStatus.internalServerError;

      default:
        return null;
    }
  }
}
