import 'package:flutter/material.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';

class ChatStatusBuilder<C extends AsyncCubit<T>, T> extends StatelessWidget {
  const ChatStatusBuilder({
    super.key,
    required this.request,
    required this.onRetry,
    required this.initialData,
    required this.builder,
    this.emptyView,
    this.errorType = ErrorType.defaultView,
    this.errorWidget,
  });

  final Future<void> request;
  final Future<void> Function() onRetry;
  final T initialData;
  final Widget Function(T data) builder;
  final Widget? emptyView;
  final ErrorType errorType;
  final Widget? errorWidget;

  @override
  Widget build(BuildContext context) {
    return StatusBuilder<C, T>.withShimmer(
      onRetry: onRetry,
      initialDataForShimmer: initialData,
      emptyView: emptyView,
      errorType: errorType,
      errorWidget: errorWidget,
      builder: builder,
    );
  }
}
