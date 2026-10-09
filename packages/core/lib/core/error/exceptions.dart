import 'package:easy_localization/easy_localization.dart';
import 'package:equatable/equatable.dart';

import '../../config/language/locale_keys.g.dart';

enum TransportFailureKind { connection, sendTimeout, receiveTimeout, unknown }

class ServerException extends Equatable implements Exception {
  final String message;
  final int? statusCode;
  final TransportFailureKind? transport;
  const ServerException(this.message, {this.statusCode, this.transport});

  @override
  String toString() => message;

  @override
  List<Object?> get props => [message, statusCode, transport];
}

class FetchDataException extends ServerException {
  const FetchDataException(super.message);
}

class BadRequestException extends ServerException {
  const BadRequestException(String message) : super(message, statusCode: 400);
}

class UnauthorizedException extends ServerException {
  const UnauthorizedException(String message) : super(message, statusCode: 401);
}

class NotFoundException extends ServerException {
  const NotFoundException(String message) : super(message, statusCode: 404);
}

class ConflictException extends ServerException {
  const ConflictException(String message) : super(message, statusCode: 409);
}

class InternalServerErrorException extends ServerException {
  InternalServerErrorException([String? message])
    : super(message ?? LocaleKeys.checkInternet, statusCode: 500);
}

class NoInternetConnectionException extends ServerException {
  NoInternetConnectionException([
    String? message,
    TransportFailureKind? transport,
  ]) : super(
         message ?? LocaleKeys.checkInternet.tr(),
         transport: transport ?? TransportFailureKind.connection,
       );
}

class CacheException implements Exception {}

/// An obsolete request, not an error to display or resolve from cache.
class RequestCancelledException implements Exception {
  const RequestCancelledException();

  @override
  String toString() => 'Request cancelled';
}

class ForbiddenException extends ServerException {
  const ForbiddenException(String message) : super(message, statusCode: 403);
}

class BlockedException extends ServerException {
  const BlockedException(String message) : super(message, statusCode: 423);
}
