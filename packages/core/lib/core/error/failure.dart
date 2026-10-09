import 'package:equatable/equatable.dart';
import 'exceptions.dart';

class Failure extends Equatable {
  final String message;

  final int? statusCode;
  final TransportFailureKind? transport;
  const Failure(this.message, {this.statusCode, this.transport});
  bool get revokesCachedContent =>
      const [401, 403, 404, 410, 423].contains(statusCode);
  bool get outcomeUnknown =>
      (statusCode ?? 0) >= 500 ||
      transport == TransportFailureKind.sendTimeout ||
      transport == TransportFailureKind.receiveTimeout ||
      transport == TransportFailureKind.unknown;
  factory Failure.fromException(ServerException error) => Failure(
    error.message,
    statusCode: error.statusCode,
    transport: error.transport,
  );
  @override
  List<Object?> get props => [message, statusCode, transport];
}

class ServerFailure extends Failure {
  const ServerFailure(super.message, {super.statusCode, super.transport});
}

class RequestCancelledFailure extends Failure {
  const RequestCancelledFailure() : super('');
}
