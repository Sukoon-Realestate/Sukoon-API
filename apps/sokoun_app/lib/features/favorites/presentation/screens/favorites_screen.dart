import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/favorites/data/models/favorites_content.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_search_screen.dart';

import '../widgets/imports.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key, this.initialItems});

  final List<FavoritePropertyContent>? initialItems;

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  late final List<FavoritePropertyContent> _favorites;

  @override
  void initState() {
    super.initState();
    _favorites = List.of(widget.initialItems ?? FavoritesContent.initialItems);
  }

  void _removeFavorite(FavoritePropertyContent item) {
    final removedIndex = _favorites.indexOf(item);
    if (removedIndex < 0) {
      return;
    }

    setState(() => _favorites.removeAt(removedIndex));

    final messenger = ScaffoldMessenger.of(context);
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(
        SnackBar(
          content: Text(LocaleKeys.favoritesRemovedMessage),
          action: SnackBarAction(
            label: LocaleKeys.favoritesUndoAction,
            textColor: AppColors.mint,
            onPressed: () {
              if (!mounted || _favorites.contains(item)) {
                return;
              }
              final restoredIndex = removedIndex.clamp(0, _favorites.length);
              setState(() => _favorites.insert(restoredIndex, item));
            },
          ),
        ),
      );
  }

  void _browseProperties() => Go.off(const TenantSearchScreen());

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
              FavoritesHeader(itemCount: _favorites.length),
              Expanded(
                child: FavoritesList(
                  items: _favorites,
                  onFavoriteRemoved: _removeFavorite,
                  onBrowsePressed: _browseProperties,
                ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: const FavoritesBottomNavigation(),
      ),
    );
  }
}
