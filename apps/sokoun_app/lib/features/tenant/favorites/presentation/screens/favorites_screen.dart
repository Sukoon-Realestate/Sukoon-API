import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/tenant/favorites/data/favorites_data.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/tenant/favorites/data/models/saved_properties_response.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_save_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';

import '../widgets/imports.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key, this.initialItems});

  final List<FavoritePropertyContent>? initialItems;

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  late final PagifyController<FavoritePropertyContent> _pagifyController;
  late final PropertySaveCubit? _saveCubit;
  late final List<FavoritePropertyContent>? _initialFavorites;
  late int _itemCount;
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
  }

  @override
  void dispose() {
    if (_initialFavorites != null) _pagifyController.dispose();
    _saveCubit?.close();
    super.dispose();
  }

  Future<(List<FavoritePropertyContent>, PaginationData)> _getFavoritesPage(
    BuildContext context,
    int page,
  ) async {
    final SavedPropertiesResponse response =
        await FavoritesData.getSavedProperties(page: page);
    if (page == 1 && mounted && _itemCount != response.count) {
      setState(() => _itemCount = response.count);
    }

    return (
      response.results,
      PaginationData(
        perPage: response.perPage < 1 ? 9 : response.perPage,
        totalPages: response.totalPages < 1 ? 1 : response.totalPages,
      ),
    );
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

    final int removedIndex = _pagifyController.items.indexWhere(
      (favorite) => favorite.id == item.id,
    );
    if (removedIndex < 0) return;

    final PropertySaveCubit? saveCubit = _saveCubit;
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
          _pagifyController.addItemAt(
            removedIndex.clamp(0, _pagifyController.items.length),
            item.copyWith(isSaved: true),
          );
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
          content: Text(LocaleKeys.favoritesRemovedMessage),
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
        _pagifyController.items.any((favorite) => favorite.id == item.id)) {
      return;
    }

    final PropertySaveCubit? saveCubit = _saveCubit;
    final int restoredIndex = removedIndex.clamp(
      0,
      _pagifyController.items.length,
    );
    _pagifyController.addItemAt(restoredIndex, item.copyWith(isSaved: true));
    setState(() => _itemCount++);
    if (saveCubit != null) {
      _pendingPropertyIds.add(item.id);
      await saveCubit.saveProperty(
        propertyId: item.id,
        onError: (_) {
          if (!mounted) return;
          _pagifyController.removeWhere((favorite) => favorite.id == item.id);
          setState(() {
            if (_itemCount > 0) _itemCount--;
          });
        },
      );
      _pendingPropertyIds.remove(item.id);
    }
  }

  void _browseProperties() => Go.to(const TenantSearchScreen());

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              FavoritesHeader(itemCount: _itemCount),
              Expanded(
                child: _initialFavorites != null
                    ? FavoritesList(
                        items: _initialFavorites,
                        onFavoriteRemoved: _removeFavorite,
                        onBrowsePressed: _browseProperties,
                      )
                    : Padding(
                        padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 16.h),
                        child: AppPagify<FavoritePropertyContent>(
                          pagifyController: _pagifyController,
                          asyncCall: _getFavoritesPage,
                          shrinkWrap: false,
                          emptyListView: FavoritesEmptyState(
                            onBrowseTap: _browseProperties,
                          ),
                          itemBuilder: (context, data, index, item) => Padding(
                            padding: EdgeInsets.only(bottom: 12.h),
                            child: FavoritePropertyCard(
                              key: ValueKey(item.id),
                              item: item,
                              onRemove: () => _removeFavorite(item),
                            ),
                          ),
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
