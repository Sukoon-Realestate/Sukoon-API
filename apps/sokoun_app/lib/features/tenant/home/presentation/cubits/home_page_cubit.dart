import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';

class HomePageCubit extends AsyncCubit<HomePageModel> {
  HomePageCubit() : super(const HomePageModel.initial());

  int _currentPage = 0;
  int _requestId = 0;
  bool _isFetching = false;
  Future<void>? _refreshRequest;

  bool get canLoadMore =>
      !isClosed &&
      !_isFetching &&
      state.isSuccess &&
      _currentPage > 0 &&
      (state.data.next?.trim().isNotEmpty ?? false);

  Future<void> getHomePage() {
    if (isClosed) return Future<void>.value();
    return _refreshRequest ??= _getPage(
      page: 1,
    ).whenComplete(() => _refreshRequest = null);
  }

  Future<void> loadMoreHomePage() async {
    final String? next = state.data.next;
    if (!canLoadMore || next == null) return;
    final String? nextPage = Uri.tryParse(next)?.queryParameters['page'];
    final int page = int.tryParse(nextPage ?? '') ?? _currentPage + 1;
    if (page <= _currentPage) return;
    await _getPage(page: page);
  }

  Future<void> _getPage({required int page}) async {
    final int requestId = ++_requestId;
    final int sessionGeneration = AccountSession.generation;
    final bool isFirstPage = page == 1;
    _isFetching = true;
    emit(isFirstPage ? state.loading() : state.loadingMore());

    try {
      // The base executor always emits full-page loading, so pagination owns
      // these transitions to keep the loaded properties visible.
      final result = await baseCrudUseCase.call(
        CrudBaseParmas<HomePageModel>(
          api: ApiConstants.homePage,
          httpRequestType: HttpRequestType.get,
          queryParameters: {'page': page},
          cacheKey: isFirstPage ? 'tenant_home_page' : 'tenant_home_page_$page',
          mapper: (json) => HomePageModel.fromJson(json),
          fromCacheJson: HomePageModel.fromJson,
          toJson: (model) => model.toJson(),
        ),
      );
      if (isClosed ||
          requestId != _requestId ||
          sessionGeneration != AccountSession.generation) {
        return;
      }

      result.when((success) {
        _currentPage = page;
        final HomePageModel pageData = success.data;
        emit(
          state.success(
            data: isFirstPage
                ? pageData
                : pageData.copyWith(
                    results: [...state.data.results, ...pageData.results],
                    banner: pageData.banner ?? state.data.banner,
                  ),
            msg: '',
          ),
        );
      }, (failure) => _setPageError(failure.message, isFirstPage: isFirstPage));
    } catch (_) {
      if (!isClosed &&
          requestId == _requestId &&
          sessionGeneration == AccountSession.generation) {
        _setPageError(LocaleKeys.exceptionError, isFirstPage: isFirstPage);
      }
    } finally {
      if (requestId == _requestId) _isFetching = false;
    }
  }

  void _setPageError(String message, {required bool isFirstPage}) {
    emit(
      isFirstPage
          ? state.error(errorMessage: message)
          : state.success(data: state.data, msg: message),
    );
  }
}
