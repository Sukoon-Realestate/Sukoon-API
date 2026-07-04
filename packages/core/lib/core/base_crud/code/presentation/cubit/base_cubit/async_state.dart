part of 'async_cubit.dart';

class AsyncState<T> extends Equatable {
  final BaseStatus status;
  final T data;
  final String? msg;

  const AsyncState({
    this.status = BaseStatus.initial,
    required this.data,
    this.msg,
  });

  factory AsyncState.initial({
    required T data,
    String? errorMessage,
  }) {
    return AsyncState<T>(
      status: BaseStatus.initial,
      data: data,
      msg: errorMessage,
    );
  }

  AsyncState<T> loading({
    T? data,
    String? msg,
  }) {
    return AsyncState<T>(
      status: BaseStatus.loading,
      data: data ?? this.data,
      msg: msg ?? this.msg,
    );
  }
  AsyncState<T> loadingMore({T? data, String? errorMessage}) {
    return AsyncState<T>(
      status: BaseStatus.loadingMore,
      data: data ?? this.data,
      msg: errorMessage ?? msg,
    );
  }

  AsyncState<T> success({
    required T data,
    String? msg,
  }) {
    return AsyncState<T>(
      status: BaseStatus.success,
      data: data,
      msg: msg ?? this.msg,
    );
  }

  AsyncState<T> error({
    String? errorMessage,
    T? data,
  }) {
    return AsyncState<T>(
      status: BaseStatus.error,
      data: data ?? this.data,
      msg: errorMessage ?? msg,
    );
  }

  @override
  List<Object?> get props => [status, data, msg];

  bool get isInitial => status.isInitial;

  bool get isLoading => status.isLoading;

  bool get isLoadingMore => status.isLoadingMore;

  bool get isSuccess => status.isSuccess;

  bool get isError => status.isError;

  AsyncState<T> copyWith({
    BaseStatus? status,
    T? data,
    String? msg,
  }) {
    return AsyncState<T>(
      status: status ?? this.status,
      data: data ?? this.data,
      msg: msg ?? this.msg,
    );
  }
}
