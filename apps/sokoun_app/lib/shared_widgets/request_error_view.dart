import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/error/exceptions.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/helpers/errors.dart';

import 'retry_view.dart';

typedef AppRequestErrorViewBuilder =
    Widget Function({
      required Object? error,
      required Future<void> Function() onRetry,
    });

Widget buildAppRequestErrorView({
  required Object? error,
  required Future<void> Function() onRetry,
}) {
  return AppRequestErrorView(error: error, onRetry: onRetry);
}

class AppRequestErrorView extends StatelessWidget {
  const AppRequestErrorView({
    super.key,
    required this.error,
    required this.onRetry,
  });

  final Object? error;
  final Future<void> Function() onRetry;

  bool get _isNoInternetError {
    if (error is PagifyNetworkException ||
        error is NoInternetConnectionException) {
      return true;
    }

    return error?.toString().trim() == LocaleKeys.checkInternet.trim();
  }

  @override
  Widget build(BuildContext context) {
    if (_isNoInternetError) {
      return AppRetryView(onRetry: onRetry);
    }

    return const ExceptionView();
  }
}

class CubitRequestErrorView<C extends AsyncCubit<T>, T>
    extends StatelessWidget {
  const CubitRequestErrorView({
    super.key,
    required this.onRetry,
    this.errorViewBuilder = buildAppRequestErrorView,
  });

  final Future<void> Function() onRetry;
  final AppRequestErrorViewBuilder errorViewBuilder;

  @override
  Widget build(BuildContext context) {
    return BlocSelector<C, AsyncState<T>, String?>(
      selector: (state) => state.msg,
      builder: (context, error) =>
          errorViewBuilder(error: error, onRetry: onRetry),
    );
  }
}
