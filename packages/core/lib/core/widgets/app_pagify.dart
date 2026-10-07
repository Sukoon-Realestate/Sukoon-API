import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/toast_messages/toast_message.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/errors.dart';
import 'package:pagify/helpers/status_stream.dart';
import 'package:pagify/pagify.dart';
import '../../config/language/locale_keys.g.dart';
import '../error/exceptions.dart';
import '../extensions/widget_extension.dart';
import '../local_db/objectbox_cache_service.dart';
import '../network/account_session.dart';
import '../shared/base_state.dart';
import 'app_text.dart';
import 'custom_loading.dart';
import 'exeption_view.dart';

enum Ranking { listView, gridView, adaptiveGrid }

class AppPagify<T> extends StatefulWidget {
  final ScrollPhysics? physics;

  /// Natural-height rows for cards that must accommodate larger text.
  final double minimumItemWidth;
  final int maximumColumns;
  final double gridSpacing;
  final int crossAxisCount;
  final double childAspectRatio;
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

  /// Set to false when the caller owns and disposes the controller.
  final bool disposeController;

  /// Uses the shared pull refresher and waits for the first page to finish.
  final bool enablePullRefresh;

  /// Keeps the last successful collection visible while its first page changes.
  /// The notice must explain that these items belong to the previous response.
  final bool retainItemsOnRefresh;
  final Widget Function(bool isLoading, VoidCallback retry)?
  retainedItemsNotice;
  final FutureOr<void> Function(PagifyAsyncCallStatus)? onUpdateStatus;
  final bool shrinkWrap;
  final Widget? emptyListView;

  /// Scrolls above list/adaptive-grid content, including loading and errors.
  final Widget? header;

  /// Optional display projection for locally filtered collections. Source
  /// items, cache contents and server page boundaries remain untouched.
  final List<T> Function(List<T> items)? filterItems;
  final Widget Function(
    BuildContext context,
    bool hasMorePages,
    bool isLoading,
    String? errorMessage,
    VoidCallback loadMore,
  )?
  filteredFooterBuilder;

  /// Insets collection rows and states without narrowing the scrolling header.
  final EdgeInsetsGeometry contentPadding;
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
    this.disposeController = true,
    this.enablePullRefresh = false,
    this.retainItemsOnRefresh = false,
    this.retainedItemsNotice,
    this.physics,
    this.minimumItemWidth = 320,
    this.maximumColumns = 3,
    this.gridSpacing = 16,
    this.crossAxisCount = 2,
    this.childAspectRatio = 1,
    this.scrollController,
    this.rankingType = Ranking.listView,
    this.onUpdateStatus,
    this.shrinkWrap = true,
    this.emptyListView,
    this.header,
    this.filterItems,
    this.filteredFooterBuilder,
    this.contentPadding = EdgeInsets.zero,
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
  }) : assert(header == null || rankingType != Ranking.gridView),
       assert(header == null || itemExtent == null),
       assert(!retainItemsOnRefresh || retainedItemsNotice != null),
       assert(!retainItemsOnRefresh || rankingType != Ranking.gridView),
       assert(filterItems == null || rankingType != Ranking.gridView),
       assert(filterItems == null || itemExtent == null),
       assert(filterItems == null || !isReverse);

  @override
  State<AppPagify<T>> createState() => _AppPagifyState<T>();
}

class _AppPagifyState<T> extends State<AppPagify<T>> {
  final int _sessionGeneration = AccountSession.generation;
  int _requestGeneration = 0;
  PagifyException? _requestError;
  Completer<void>? _refreshCompleter;
  List<T> _lastSuccessfulItems = const [];
  bool _hasMorePages = false;
  List<T>? _visibleItems;
  VoidCallback? _retryPendingPage;

  Future<void> _refresh() {
    final Completer<void>? pending = _refreshCompleter;
    if (pending != null) return pending.future;
    if (widget.pagifyController.isLoading && _retryPendingPage == null) {
      return Future.value();
    }
    final completer = Completer<void>();
    _refreshCompleter = completer;
    // Pagify starts its request without awaiting it. Complete on terminal status.
    unawaited(widget.pagifyController.refresh());
    return completer.future;
  }

  void _completeRefresh() {
    _refreshCompleter?.complete();
    _refreshCompleter = null;
  }

  Future<void> _onUpdateStatus(PagifyAsyncCallStatus status) async {
    _visibleItems = null;
    try {
      await widget.onUpdateStatus?.call(status);
    } finally {
      if (status.isSuccess || status.isError || status.isNetworkError) {
        _completeRefresh();
      }
    }
  }

  Future<(List<T>, PaginationData)> _loadPage(BuildContext context, int page) {
    if (page == 1) {
      _requestGeneration++;
      _hasMorePages = false;
      _retryPendingPage = null;
    }
    final int generation = _requestGeneration;
    _requestError = null;
    final completer = Completer<(List<T>, PaginationData)>();
    bool active() =>
        mounted &&
        generation == _requestGeneration &&
        _sessionGeneration == AccountSession.generation;
    // Pagify 0.3 does not cancel requests on disposal or refresh. Abandoned
    // futures intentionally stop delivering results (as a cancelled operation
    // does), so its disposed state can never receive a late success or error.
    Future<void> request() async {
      if (!active()) return;
      try {
        final result = await widget.asyncCall(context, page);
        if (active()) {
          _hasMorePages = page < result.$2.totalPages;
          completer.complete(result);
        }
      } on RequestCancelledException {
        // Replaced/disposed reads must not trigger Pagify cache fallback.
      } catch (error, stack) {
        if (active()) {
          // Pagify 0.3 replaces non-Dio messages with its own error text.
          // Preserve the original request message for the view and callback.
          if (error is PagifyException) {
            _requestError = error;
          } else if (error is ServerException) {
            _requestError = PagifyApiRequestException(
              error.message,
              pagifyFailure: RequestFailureData.initial(),
            );
          }
          if (page > 1 &&
              widget.filterItems != null &&
              widget.pagifyController.items.isNotEmpty) {
            // Pagify 0.3 does not await/catch failures from its scroll request.
            // Keep that same page future pending and retry it explicitly; a
            // failure must never advance the page or discard the source items.
            _requestError ??= PagifyApiRequestException(
              error is DioException && error.response?.data is Map
                  ? (error.response!.data as Map)['message']?.toString() ??
                        LocaleKeys.exceptionError
                  : LocaleKeys.exceptionError,
              pagifyFailure: RequestFailureData.initial(),
            );
            _retryPendingPage = () => unawaited(request());
            setState(() {});
            if (context.mounted) await _onError(context, page, _requestError!);
            return;
          }
          completer.completeError(
            error is Exception ? error : Exception(error.toString()),
            stack,
          );
        }
      }
    }

    unawaited(request());
    return completer.future;
  }

  PagifyException _resolveError(PagifyException error) =>
      error is PagifyNetworkException ? error : _requestError ?? error;

  Future<void> _onSuccess(BuildContext context, List<T> items) async {
    _visibleItems = null;
    if (widget.retainItemsOnRefresh) _lastSuccessfulItems = List<T>.of(items);
    await widget.onSuccess?.call(context, items);
  }

  bool get _canRetainItems =>
      widget.retainItemsOnRefresh &&
      _lastSuccessfulItems.isNotEmpty &&
      _sessionGeneration == AccountSession.generation;

  Widget _buildRetainedItems({required bool isLoading}) => LayoutBuilder(
    builder: (context, constraints) {
      final int columns = _columnCount(context, constraints);
      return ListView.builder(
        physics: AlwaysScrollableScrollPhysics(parent: widget.physics),
        shrinkWrap: widget.shrinkWrap,
        itemCount: (_lastSuccessfulItems.length / columns).ceil() + 1,
        itemBuilder: (context, row) {
          if (row == 0) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (widget.header != null) widget.header!,
                widget.retainedItemsNotice!(
                  isLoading,
                  () => widget.pagifyController.refresh(),
                ),
              ],
            );
          }
          final int index = (row - 1) * columns;
          return _buildListItem(
            context,
            _lastSuccessfulItems,
            index,
            _lastSuccessfulItems[index],
            columns,
            includeHeader: false,
            includeFilterFooter: false,
          );
        },
      );
    },
  );

  Widget _buildErrorView(PagifyException error) {
    if (_canRetainItems) return _buildRetainedItems(isLoading: false);
    final PagifyException requestError = _resolveError(error);
    return _buildStateView(
      widget.errorBuilder?.call(requestError) ??
          ExceptionView(
            msg: requestError.msg,
            onRetry: () async => widget.pagifyController.retry(),
          ),
    );
  }

  Widget _buildStateView(Widget child) {
    final Widget content = _padContent(child);
    final Widget? header = widget.header;
    if (widget.enablePullRefresh) {
      return CustomScrollView(
        physics: AlwaysScrollableScrollPhysics(parent: widget.physics),
        shrinkWrap: widget.shrinkWrap,
        slivers: [
          if (header != null) SliverToBoxAdapter(child: header),
          SliverFillRemaining(
            hasScrollBody: false,
            child: ScrollConfiguration(
              behavior: ScrollConfiguration.of(
                context,
              ).copyWith(physics: const NeverScrollableScrollPhysics()),
              child: content,
            ),
          ),
        ],
      );
    }
    if (header == null) return content;
    return ListView(
      padding: EdgeInsets.zero,
      physics: widget.physics,
      shrinkWrap: widget.shrinkWrap,
      children: [header, content],
    );
  }

  Widget _padContent(Widget child) => widget.contentPadding == EdgeInsets.zero
      ? child
      : Padding(padding: widget.contentPadding, child: child);

  Widget get _loadingView => Builder(
    builder: (context) {
      final Widget loading =
          widget.loadingBuilder ?? CustomLoading.showLoadingView();
      if (_retryPendingPage != null) return const SizedBox.shrink();
      // Pagify uses this same widget for its first load and pagination footer.
      return widget.pagifyController.items.isEmpty
          ? (_canRetainItems
                ? _buildRetainedItems(isLoading: true)
                : _buildStateView(loading))
          : loading;
    },
  );

  Widget get _emptyView => _buildStateView(
    widget.emptyListView ??
        Center(child: Column(children: [AppText(LocaleKeys.notFound)])),
  );

  Widget _buildListItem(
    BuildContext context,
    List<T> data,
    int index,
    T item,
    int columns, {
    bool includeHeader = true,
    bool includeFilterFooter = true,
  }) {
    final filter = widget.filterItems;
    final List<T> visible = filter == null
        ? data
        : includeFilterFooter
        ? (_visibleItems ??= filter(List<T>.unmodifiable(data)))
        : filter(List<T>.unmodifiable(data));
    if (widget.filterItems != null && index > 0 && index >= visible.length) {
      return const SizedBox.shrink();
    }
    late final Widget row;
    if (widget.filterItems != null && visible.isEmpty) {
      row = widget.emptyListView ?? AppText(LocaleKeys.notFound);
    } else if (widget.rankingType == Ranking.adaptiveGrid) {
      if (index % columns != 0) return const SizedBox.shrink();
      row = Padding(
        padding: EdgeInsets.only(bottom: widget.gridSpacing),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (int column = 0; column < columns; column++) ...[
              if (column > 0) SizedBox(width: widget.gridSpacing),
              Expanded(
                child: index + column < visible.length
                    ? widget.itemBuilder(
                        context,
                        visible,
                        index + column,
                        visible[index + column],
                      )
                    : const SizedBox.shrink(),
              ),
            ],
          ],
        ),
      );
    } else {
      row = widget.itemBuilder(context, visible, index, visible[index]);
    }
    final Widget? header = widget.header;
    final bool lastVisibleRow =
        visible.isEmpty || index + columns >= visible.length;
    final Widget? footer =
        widget.filterItems != null && includeFilterFooter && lastVisibleRow
        ? Builder(
            builder: (footerContext) =>
                widget.filteredFooterBuilder?.call(
                  footerContext,
                  _hasMorePages,
                  widget.pagifyController.isLoading &&
                      _retryPendingPage == null,
                  _requestError?.msg,
                  () => _loadMoreFiltered(footerContext),
                ) ??
                const SizedBox.shrink(),
          )
        : null;
    final Widget content = _padContent(
      footer == null
          ? row
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [row, footer],
            ),
    );
    if (!includeHeader || index != 0 || header == null) return content;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [header, content],
    );
  }

  void _loadMoreFiltered(BuildContext itemContext) {
    final retry = _retryPendingPage;
    if (mounted && retry != null) {
      _retryPendingPage = null;
      _requestError = null;
      setState(() {});
      retry();
      return;
    }
    if (!mounted || !_hasMorePages || widget.pagifyController.isLoading) return;
    final ScrollPosition? position = Scrollable.maybeOf(itemContext)?.position;
    if (position == null) return;
    // Use Pagify's existing scroll/retry path. Its public loadMore method in
    // 0.3 resets to page one, which would repeatedly hide later-page matches.
    if (position.pixels == position.maxScrollExtent) {
      widget.pagifyController.retry();
    } else {
      position.jumpTo(position.maxScrollExtent);
    }
  }

  Future<void> _onError(
    BuildContext context,
    int page,
    PagifyException error,
  ) async {
    final PagifyException requestError = _resolveError(error);
    if (widget.onError != null) {
      await widget.onError!(context, page, requestError);
    } else {
      Messages.showToast(
        status: BaseStatus.error,
        title: LocaleKeys.operationFaild,
        msg: requestError.msg,
      );
    }
  }

  @override
  void dispose() {
    _completeRefresh();
    _requestGeneration++;
    if (widget.disposeController) widget.pagifyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final Widget collection = LayoutBuilder(
      builder: (context, constraints) => _buildCollection(context, constraints),
    );
    return widget.enablePullRefresh
        ? collection.withPullRefresher(onRefresh: _refresh)
        : collection;
  }

  int _columnCount(BuildContext context, BoxConstraints constraints) {
    final double scale = (MediaQuery.textScalerOf(context).scale(14) / 14)
        .clamp(1, 2);
    return widget.rankingType == Ranking.adaptiveGrid &&
            constraints.hasBoundedWidth
        ? ((constraints.maxWidth -
                      widget.contentPadding
                          .resolve(Directionality.of(context))
                          .horizontal +
                      widget.gridSpacing) /
                  (widget.minimumItemWidth * scale + widget.gridSpacing))
              .floor()
              .clamp(1, widget.maximumColumns)
        : 1;
  }

  Widget _buildCollection(BuildContext context, BoxConstraints constraints) {
    _visibleItems = null;
    final int columns = _columnCount(context, constraints);
    final hasCacheConfig =
        widget.cacheKey != null &&
        widget.cacheToJson != null &&
        widget.cacheFromJson != null;

    void onSaveCache(String key, List<Map<String, dynamic>> items) {
      if (mounted && _sessionGeneration == AccountSession.generation) {
        ObjectBoxCacheService.save(key, {'items': items});
      }
    }

    List<Map<String, dynamic>>? onReadCache(String key) {
      if (!mounted || _sessionGeneration != AccountSession.generation) {
        return null;
      }
      final cached = ObjectBoxCacheService.read(key);
      if (cached == null) return null;
      return (cached['items'] as List?)?.cast<Map<String, dynamic>>();
    }

    if (widget.rankingType != Ranking.gridView) {
      return Pagify<(List<T>, PaginationData), T>.listView(
        key: widget.key,
        isReverse: widget.isReverse,
        physics: widget.physics,
        cacheExtent: widget.cacheExtent,
        itemExtent: widget.rankingType == Ranking.adaptiveGrid
            ? null
            : widget.itemExtent,
        noConnectionText: widget.noConnectionText ?? LocaleKeys.checkInternet,
        onLoading: widget.onLoading,
        onError: _onError,
        onSuccess: _onSuccess,
        listenToNetworkConnectivityChanges:
            widget.onConnectivityChanged != null,
        onConnectivityChanged: widget.onConnectivityChanged,
        onUpdateStatus: _onUpdateStatus,
        shrinkWrap: widget.shrinkWrap,
        emptyListView: _emptyView,
        controller: widget.pagifyController,
        asyncCall: _loadPage,
        loadingBuilder: _loadingView,
        mapper: (data) => PagifyData(
          data: data.$1,
          paginationData: PaginationData(
            perPage: data.$2.perPage,
            totalPages: data.$2.totalPages,
          ),
        ),
        errorBuilder: _buildErrorView,
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
        itemBuilder: (context, data, index, item) =>
            _buildListItem(context, data, index, item, columns),
      );
    } else {
      return Pagify<(List<T>, PaginationData), T>.gridView(
        key: widget.key,
        padding: widget.contentPadding,
        isReverse: widget.isReverse,
        physics: widget.physics,
        cacheExtent: widget.cacheExtent,
        noConnectionText: widget.noConnectionText ?? LocaleKeys.checkInternet,
        onLoading: widget.onLoading,
        onError: _onError,
        onSuccess: _onSuccess,
        listenToNetworkConnectivityChanges:
            widget.onConnectivityChanged != null,
        onConnectivityChanged: widget.onConnectivityChanged,
        onUpdateStatus: _onUpdateStatus,
        crossAxisCount: widget.crossAxisCount,
        childAspectRatio: widget.childAspectRatio,
        mainAxisSpacing: widget.gridSpacing,
        crossAxisSpacing: widget.gridSpacing,
        emptyListView: _emptyView,
        controller: widget.pagifyController,
        asyncCall: _loadPage,
        loadingBuilder: _loadingView,
        mapper: (data) => PagifyData(
          data: data.$1,
          paginationData: PaginationData(
            perPage: data.$2.perPage,
            totalPages: data.$2.totalPages,
          ),
        ),
        errorBuilder: _buildErrorView,
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
    }
  }
}
