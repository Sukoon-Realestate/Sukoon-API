import 'package:dio/dio.dart';

import '../helpers/helpers.dart';

enum RequestMethod { get, post, put, delete, patch }


class NetworkRequest<GenericModel> {
  final String path;
  final RequestMethod method;
  final Map<String, dynamic>? body;
  final Map<String, dynamic>? queryParameters;
  final Map<String, dynamic>? headers;
  bool isFormData;
  final ProgressCallback? onSendProgress;
  final ProgressCallback? onReceiveProgress;

  NetworkRequest({
    required this.method,
    required this.path,
    this.body,
    this.queryParameters,
    this.isFormData = false,
    this.onSendProgress,
    this.headers,
    this.onReceiveProgress,
  });

  Map<String, dynamic> toJson() => {
    'flavor' : Helpers.currentFlavor.name,
    'path': path,
    'method': method.name,
    'body': body,
    'query_parameters': queryParameters,
    'headers': headers,
    'is_form_data': isFormData,
  };

  factory NetworkRequest.fromJson(Map<String, dynamic> json) => NetworkRequest(
    path: json['path'] ?? '',
    method: RequestMethod.values.firstWhere(
      (m) => m.name == json['method'],
      orElse: () => RequestMethod.get,
    ),
    body: (json['body'] as Map?)?.cast<String, dynamic>(),
    queryParameters: (json['query_parameters'] as Map?)?.cast<String, dynamic>(),
    headers: (json['headers'] as Map?)?.cast<String, dynamic>(),
    isFormData: json['is_form_data'] ?? false,
  );



  NetworkRequest copyWith({
    String? path,
    RequestMethod? method,
    Map<String, dynamic>? body,
    Map<String, dynamic>? queryParameters,
    Map<String, dynamic>? headers,
    bool? requestWithOutToken,
    bool? isFormData,
    ProgressCallback? onSendProgress,
    ProgressCallback? onReceiveProgress,
  }) {
    return NetworkRequest(
      path: path ?? this.path,
      method: method ?? this.method,
      body: body ?? this.body,
      headers: headers ?? this.headers,
      queryParameters: queryParameters ?? this.queryParameters,
      isFormData: isFormData ?? this.isFormData,
      onSendProgress: onSendProgress ?? this.onSendProgress,
      onReceiveProgress: onReceiveProgress ?? this.onReceiveProgress,
    );
  }
}
