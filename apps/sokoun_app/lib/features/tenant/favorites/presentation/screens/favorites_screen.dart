import 'package:sokoun_app/shared_widgets/property_filter_button.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/helpers/status_stream.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorites_data.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorite_property_filter.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/saved_properties_response.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_filter_screen.dart';

import '../widgets/imports.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key, this.initialItems});

  final List<FavoritePropertyContent>? initialItems;

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  // Count, filters, and visible items form one screen-wide content projection.
  late final PagifyController<FavoritePropertyContent> _pagifyController;
  late final PropertySaveCubit? _saveCubit;
  late final List<FavoritePropertyContent>? _initialFavorites;
  late int _itemCount;
  late PropertySearchFilters _filters;
  final List<FavoritePropertyContent> _loadedFavorites = [];
  final Set<String> _pendingPropertyIds = {};

  @override
  void initState() {
    super.initState();
    _pagifyController = PagifyController<FavoritePropertyContent>();
    _initialFavorites = widget.initialItems == null
        ? null
        : List<FavoritePropertyContent>.of(widget.initialItems!);
    _saveCubit = widget.initialItems == null ? PropertySaveCubit() : null;
    _itemCount = _initialFavorites?.length ?? 0;
    _filters = const PropertySearchFilters.initial();
  }

  @override
  void dispose() {
    _saveCubit?.close();
    super.dispose();
  }

  Future<(List<FavoritePropertyContent>, PaginationData)> _getFavoritesPage(
    BuildContext context,
    int page,
  ) async {
    if (page == 1) _loadedFavorites.clear();
    final (SavedPropertiesResponse response, PaginationData pagination) =
        await FavoritesData.getSavedPropertiesPage(page: page);
    if (page == 1 && mounted && _itemCount != response.count) {
      setState(() => _itemCount = response.count);
    }

    return (response.results, pagination);
  }

  Future<void> _removeFavorite(FavoritePropertyContent item) async {
    if (_pendingPropertyIds.contains(item.id)) return;

    final List<FavoritePropertyContent>? initialFavorites = _initialFavorites;
    if (initialFavorites != null) {
      final int removedIndex = initialFavorites.indexWhere(
        (favorite) => favorite.id == item.id,
      );
      if (removedIndex < 0) return;

      setState(() {
        initialFavorites.removeAt(removedIndex);
        _itemCount = initialFavorites.length;
      });
      _showRemovedMessage(item: item, removedIndex: removedIndex);
      return;
    }

    final int removedIndex = _loadedFavorites.indexWhere(
      (favorite) => favorite.id == item.id,
    );
    if (removedIndex < 0) return;

    final PropertySaveCubit? saveCubit = _saveCubit;
    _loadedFavorites.removeAt(removedIndex);
    _pagifyController.removeWhere((favorite) => favorite.id == item.id);
    setState(() {
      if (_itemCount > 0) _itemCount--;
    });
    if (saveCubit != null) {
      bool requestFailed = false;
      _pendingPropertyIds.add(item.id);
      await saveCubit.unsaveProperty(
        propertyId: item.id,
        onError: (_) {
          requestFailed = true;
          if (!mounted) return;
          _loadedFavorites.insert(
            removedIndex.clamp(0, _loadedFavorites.length),
            item.copyWith(isSaved: true),
          );
          _applyFiltersToPagify();
          setState(() => _itemCount++);
        },
      );
      _pendingPropertyIds.remove(item.id);
      if (!mounted || requestFailed) return;
    }

    _showRemovedMessage(item: item, removedIndex: removedIndex);
  }

  void _showRemovedMessage({
    required FavoritePropertyContent item,
    required int removedIndex,
  }) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(
            LocaleKeys.favoritesRemovedMessage,
            style: AppTextStyles.base,
          ),
          action: SnackBarAction(
            label: LocaleKeys.favoritesUndoAction,
            textColor: AppColors.mint,
            onPressed: () =>
                _restoreFavorite(item: item, removedIndex: removedIndex),
          ),
        ),
      );
  }

  Future<void> _restoreFavorite({
    required FavoritePropertyContent item,
    required int removedIndex,
  }) async {
    final List<FavoritePropertyContent>? initialFavorites = _initialFavorites;
    if (initialFavorites != null) {
      if (initialFavorites.any((favorite) => favorite.id == item.id)) return;

      final int restoredIndex = removedIndex.clamp(0, initialFavorites.length);
      setState(() {
        initialFavorites.insert(restoredIndex, item.copyWith(isSaved: true));
        _itemCount = initialFavorites.length;
      });
      return;
    }

    if (_pendingPropertyIds.contains(item.id) ||
        _loadedFavorites.any((favorite) => favorite.id == item.id)) {
      return;
    }

    final PropertySaveCubit? saveCubit = _saveCubit;
    final int restoredIndex = removedIndex.clamp(0, _loadedFavorites.length);
    _loadedFavorites.insert(restoredIndex, item.copyWith(isSaved: true));
    _applyFiltersToPagify();
    setState(() => _itemCount++);
    if (saveCubit != null) {
      _pendingPropertyIds.add(item.id);
      await saveCubit.saveProperty(
        propertyId: item.id,
        onError: (_) {
          if (!mounted) return;
          _loadedFavorites.removeWhere((favorite) => favorite.id == item.id);
          _applyFiltersToPagify();
          setState(() {
            if (_itemCount > 0) _itemCount--;
          });
        },
      );
      _pendingPropertyIds.remove(item.id);
    }
  }

  List<FavoritePropertyContent>? get _visibleInitialFavorites {
    final List<FavoritePropertyContent>? favorites = _initialFavorites;
    if (favorites == null) return null;
    return FavoritePropertyFilter.apply(favorites, _filters);
  }

  bool get _hasLocalFilters =>
      _filters.search.trim().isNotEmpty || _filters.activeCount > 0;

  int get _visibleItemCount {
    final List<FavoritePropertyContent>? initialFavorites =
        _visibleInitialFavorites;
    if (initialFavorites != null) return initialFavorites.length;
    return _hasLocalFilters ? _pagifyController.items.length : _itemCount;
  }

  Future<void> _openFilters() async {
    await Go.to<void>(
      TenantFilterScreen(
        initialFilters: _filters,
        onFiltersApplied: _applyFilters,
      ),
    );
  }

  void _applyFilters(PropertySearchFilters filters) {
    if (!mounted) return;
    setState(() => _filters = filters.copyWith(page: 1));
    if (_initialFavorites == null) _applyFiltersToPagify();
  }

  void _clearFilters() {
    _applyFilters(PropertySearchFilters.initial(pageSize: _filters.pageSize));
  }

  void _onPagifyStatusChanged(PagifyAsyncCallStatus status) {
    if (!status.isSuccess || !mounted) return;
    for (final FavoritePropertyContent item in _pagifyController.items) {
      final int index = _loadedFavorites.indexWhere(
        (favorite) => favorite.id == item.id,
      );
      if (index < 0) {
        _loadedFavorites.add(item);
      } else {
        _loadedFavorites[index] = item;
      }
    }
    if (_hasLocalFilters) {
      _applyFiltersToPagify();
    } else {
      setState(() {});
    }
  }

  void _applyFiltersToPagify() {
    final List<FavoritePropertyContent> filtered = FavoritePropertyFilter.apply(
      _loadedFavorites,
      _filters,
    );
    _pagifyController.clear();
    for (final FavoritePropertyContent item in filtered) {
      _pagifyController.addItem(item);
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.favoritesTitle,
      showBackButton: true,
      actions: [
        PropertyFilterButton(
          activeCount: _filters.activeCount,
          onPressed: _openFilters,
        ),
      ],
      backgroundColor: AppColors.scaffoldBackground,
      contentWidth: SokounContentWidth.wide,
      body: SafeArea(
        child: FavoritesContentView(
          itemCount: _visibleItemCount,
          initialItems: _visibleInitialFavorites,
          pagifyController: _pagifyController,
          loadPage: _getFavoritesPage,
          onFavoriteRemoved: _removeFavorite,
          activeFilterCount: _filters.activeCount,
          onClearFiltersPressed: _clearFilters,
          onPagifyStatusChanged: _onPagifyStatusChanged,
        ),
      ),
    );
  }
}
