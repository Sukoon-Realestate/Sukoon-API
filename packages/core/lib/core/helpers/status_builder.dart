import 'package:flutter/cupertino.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/object.dart';
import '../base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../shared/base_state.dart';
import '../widgets/custom_loading.dart';
import '../widgets/custom_shimmer.dart';
import '../widgets/exeption_view.dart';
import '../widgets/not_contain_data.dart';
import '../widgets/retry_view.dart';

enum LoadingType { loadingIndicator, shimmer }

extension CheckLoadingType on LoadingType {
  bool get isLoadingIndicator => this == LoadingType.loadingIndicator;
  bool get isShimmer => this == LoadingType.shimmer;
}

enum ErrorType { withData, customView, defaultView }

extension CheckErrorType on ErrorType {
  bool get isWithData => this == ErrorType.withData;
  bool get isCustomView => this == ErrorType.customView;
  bool get isDefaultView => this == ErrorType.defaultView;
}

class StatusBuilder<C extends AsyncCubit<T>, T> extends StatelessWidget {
  final Function(T data) builder;
  final LoadingType loadingType;
  final ErrorType errorType;
  final Widget? errorWidget;
  final Widget? emptyView;
  final T? initialDataForShimmer;
  final Future<void> requestToTryAgainWhenError;
  final Future<void> Function() onRetry;

  const StatusBuilder({
    super.key,
    required this.builder,
    required this.requestToTryAgainWhenError,
    required this.onRetry,
    this.errorType = ErrorType.defaultView,
    this.errorWidget,
    this.emptyView,
  }) : loadingType = LoadingType.loadingIndicator,
       initialDataForShimmer = null;

  const StatusBuilder.withShimmer({
    super.key,
    required this.builder,
    required this.requestToTryAgainWhenError,
    required this.onRetry,
    this.errorType = ErrorType.defaultView,
    required this.initialDataForShimmer,
    this.errorWidget,
    this.emptyView,
  }) : loadingType = LoadingType.shimmer;

  bool _isEmpty(T data) {
    if (data is List) {
      if (data.isEmpty) {
        return true;
      }

      return false;
    }

    return false;
  }

  Widget get _loadingView {
    if (loadingType.isShimmer) {
      final T? shimmerData = initialDataForShimmer;
      if (shimmerData == null) {
        return const SizedBox.shrink();
      }
      return CustomShimmer(child: builder.call(shimmerData));
    } else if (loadingType.isLoadingIndicator) {
      return SizedBox.square(
        dimension: 50.sp,
        child: CustomLoading.showLoadingView(),
      );
    } else {
      return const CupertinoActivityIndicator();
    }
  }

  Widget _successView(T data) {
    if (_isEmpty(data)) {
      return _emptyView;
    } else {
      return builder(data);
    }
  }

  Widget get _emptyView {
    if (emptyView.isNotNull) {
      return emptyView!;
    } else {
      return NotContainData();
    }
  }

  Widget _errorView(AsyncState<T> state) {
    if (state.msg?.trim() == LocaleKeys.checkInternet.trim()) {
      return AppRetryView(onRetry: onRetry);
    }

    if (errorType.isWithData) {
      return builder.call(state.data);
    } else if (errorType.isCustomView && errorWidget.isNotNull) {
      return errorWidget!;
    }

    return const ExceptionView();
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<C, AsyncState<T>>(
      builder: (context, state) => state.status.when(
        onLoading: () => _loadingView,
        onSuccess: () => _successView(state.data),
        onError: () => _errorView(state),
        // onLoadingMore: () {
        //   return _buildCircularLoading();
        // },
      ),
    );
  }
}
