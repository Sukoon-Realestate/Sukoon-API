import 'dart:async';
import 'package:flutter/material.dart';
import 'package:lottie/lottie.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:melos_core/generated/assets.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/helpers/status_stream.dart';
import 'package:pagify/pagify.dart';
import '../../config/language/locale_keys.g.dart';
import '../local_db/objectbox_cache_service.dart';
import '../shared/base_state.dart';
import 'app_text.dart';
import 'custom_loading.dart';
import 'exeption_view.dart';

enum Ranking { listView, gridView }

class AppPagify<T> extends StatefulWidget {
  final ScrollPhysics? physics;
  final Ranking rankingType;
  final ScrollController? scrollController;
  final Future<(List<T>, PaginationData)> Function(
    BuildContext context,
    int page,
  )
  asyncCall;
  final Widget Function(
    BuildContext context,
    List<T> data,
    int index,
    T element,
  )
  itemBuilder;
  final PagifyController<T> pagifyController;
  final FutureOr<void> Function(PagifyAsyncCallStatus)? onUpdateStatus;
  final bool shrinkWrap;
  final Widget? emptyListView;
  final bool isReverse;
  final double? cacheExtent;
  final double? itemExtent;
  final String? noConnectionText;
  final Widget? loadingBuilder;
  final Widget Function(PagifyException error)? errorBuilder;
  final PagifyErrorMapper? errorMapper;
  final FutureOr<void> Function()? onLoading;
  final FutureOr<void> Function(BuildContext, int, PagifyException)? onError;
  final FutureOr<void> Function(BuildContext, List<T>)? onSuccess;
  final FutureOr<void> Function(bool isConnected)? onConnectivityChanged;

  /// Optional — provide all three together to enable offline cache support.
  final String? cacheKey;
  final Map<String, dynamic> Function(T item)? cacheToJson;
  final T Function(Map<String, dynamic> json)? cacheFromJson;

  const AppPagify({
    super.key,
    required this.asyncCall,
    required this.itemBuilder,
    required this.pagifyController,
    this.physics,
    this.scrollController,
    this.rankingType = Ranking.listView,
    this.onUpdateStatus,
    this.shrinkWrap = true,
    this.emptyListView,
    this.isReverse = false,
    this.cacheExtent,
    this.itemExtent,
    this.noConnectionText,
    this.loadingBuilder,
    this.errorBuilder,
    this.errorMapper,
    this.onLoading,
    this.onError,
    this.onSuccess,
    this.onConnectivityChanged,
    this.cacheKey,
    this.cacheToJson,
    this.cacheFromJson,
  });

  @override
  State<AppPagify<T>> createState() => _AppPagifyState<T>();
}

class _AppPagifyState<T> extends State<AppPagify<T>> {
  @override
  void dispose() {
    widget.pagifyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final hasCacheConfig =
        widget.cacheKey != null &&
        widget.cacheToJson != null &&
        widget.cacheFromJson != null;

    void onSaveCache(String key, List<Map<String, dynamic>> items) =>
        ObjectBoxCacheService.save(key, {'items': items});

    List<Map<String, dynamic>>? onReadCache(String key) {
      final cached = ObjectBoxCacheService.read(key);
      if (cached == null) return null;
      return (cached['items'] as List?)?.cast<Map<String, dynamic>>();
    }

    if (widget.rankingType == Ranking.listView) {
      return Pagify<(List<T>, PaginationData), T>.listView(
        key: widget.key,
        isReverse: widget.isReverse,
        physics: widget.physics,
        cacheExtent: widget.cacheExtent,
        itemExtent: widget.itemExtent,
        noConnectionText: widget.noConnectionText,
        onLoading: widget.onLoading,
        onError:
            widget.onError ??
            (context, page, error) => Messages.showToast(
              status: BaseStatus.error,
              title: LocaleKeys.operationFaild,
              msg: error.msg,
            ),
        onSuccess: widget.onSuccess,
        onConnectivityChanged: widget.onConnectivityChanged,
        onUpdateStatus: widget.onUpdateStatus,
        shrinkWrap: widget.shrinkWrap,
        emptyListView:
            widget.emptyListView ??
            Center(
              child: Column(
                children: [
                  // Lottie.asset(Assets.lottie.notFound2.path),
                  AppText(LocaleKeys.notFound),
                ],
              ),
            ),
        controller: widget.pagifyController,
        asyncCall: widget.asyncCall,
        loadingBuilder:
            widget.loadingBuilder ?? CustomLoading.showLoadingView(),
        mapper: (data) => PagifyData(
          data: data.$1,
          paginationData: PaginationData(
            perPage: data.$2.perPage,
            totalPages: data.$2.totalPages,
          ),
        ),
        errorBuilder: widget.errorBuilder ?? (error) => const ExceptionView(),
        errorMapper:
            widget.errorMapper ??
            PagifyErrorMapper(
              errorWhenDio: (e) {
                final String? msg = e.response?.data['message'];
                return PagifyApiRequestException(
                  msg ?? 'network error occur',
                  pagifyFailure: RequestFailureData(
                    statusCode: e.response?.statusCode,
                    statusMsg: e.response?.statusMessage,
                  ),
                );
              },
            ),
        cacheKey: widget.cacheKey,
        cacheToJson: hasCacheConfig ? widget.cacheToJson : null,
        cacheFromJson: hasCacheConfig ? widget.cacheFromJson : null,
        onSaveCache: hasCacheConfig ? onSaveCache : null,
        onReadCache: hasCacheConfig ? onReadCache : null,
        itemBuilder: widget.itemBuilder,
      );
    } else {
      return Pagify<(List<T>, PaginationData), T>.gridView(
        key: widget.key,
        onUpdateStatus: widget.onUpdateStatus,
        controller: widget.pagifyController,
        asyncCall: widget.asyncCall,
        physics: widget.physics,
        errorBuilder: (e) => Column(
          children: [
            Lottie.asset(Assets.lottie.notFound2.path),
            AppText(LocaleKeys.notFound),
          ],
        ),
        emptyListView:
            widget.emptyListView ??
            Column(
              children: [
                Lottie.asset(Assets.lottie.notFound2.path),
                AppText(LocaleKeys.notFound),
              ],
            ),
        loadingBuilder: CustomLoading.showLoadingView(),
        mapper: (data) => PagifyData(
          data: data.$1,
          paginationData: PaginationData(
            perPage: data.$2.perPage,
            totalPages: data.$2.totalPages,
          ),
        ),
        errorMapper: PagifyErrorMapper(
          errorWhenDio: (error) => error.response?.data['message'],
        ),
        cacheKey: widget.cacheKey,
        cacheToJson: hasCacheConfig ? widget.cacheToJson : null,
        cacheFromJson: hasCacheConfig ? widget.cacheFromJson : null,
        onSaveCache: hasCacheConfig ? onSaveCache : null,
        onReadCache: hasCacheConfig ? onReadCache : null,
        itemBuilder: widget.itemBuilder,
      );
    }
  }
}
