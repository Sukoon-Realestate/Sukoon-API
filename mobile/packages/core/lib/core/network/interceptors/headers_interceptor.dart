import 'package:dio/dio.dart';

class HeadersInterceptor extends Interceptor {
  HeadersInterceptor({required Map<String, dynamic> Function() headersProvider})
    : _headersProvider = headersProvider;

  final Map<String, dynamic> Function() _headersProvider;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    for (final header in _headersProvider().entries) {
      options.headers.putIfAbsent(header.key, () => header.value);
    }
    handler.next(options);
  }
}
