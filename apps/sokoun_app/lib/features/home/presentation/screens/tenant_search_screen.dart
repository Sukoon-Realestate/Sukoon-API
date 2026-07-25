import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/favorites/presentation/screens/favorites_screen.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';

import '../widgets/tenant_search/imports.dart';
import '../widgets/tenant_widgets/imports.dart';
import 'tenant_search_results_screen.dart';

class TenantSearchScreen extends StatefulWidget {
  const TenantSearchScreen({super.key});

  @override
  State<TenantSearchScreen> createState() => _TenantSearchScreenState();
}

class _TenantSearchScreenState extends State<TenantSearchScreen> {
  late TenantSearchFormState _form;
  late final TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _form = TenantSearchFormState.initial();
    _searchController = TextEditingController(text: _form.query);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _updateQuery(String value) {
    setState(() {
      _form = _form.copyWith(query: value, clearSelectedArea: true);
    });
  }

  void _selectCategory(SearchCategoryContent category) {
    setState(() {
      _form = _form.copyWith(selectedCategory: category.label);
    });
  }

  void _selectArea(SuggestedAreaContent area) {
    final query = '${area.title}، القاهرة';
    _searchController.text = query;
    setState(() {
      _form = _form.copyWith(query: query, selectedArea: area.title);
    });
  }

  void _selectRecent(RecentSearchContent search) {
    _searchController.text = search.title;
    setState(() {
      _form = _form.copyWith(query: search.title, clearSelectedArea: true);
    });
    _submitSearch();
  }

  void _submitSearch([String? submittedQuery]) {
    final query = (submittedQuery ?? _searchController.text).trim();
    if (query.isEmpty && !_form.canSearch) {
      return;
    }

    setState(() {
      _form = _form.copyWith(query: query).withRecentSearch(query);
    });

    FocusScope.of(context).unfocus();
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TenantSearchResultsScreen(
          initialQuery: query,
          initialFilters: _form.resultFilters,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(
                  'ابحث عن سكن',
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.right,
                ),
                14.szH,
                TenantSearchField(
                  controller: _searchController,
                  onChanged: _updateQuery,
                  onSubmitted: (value) => _submitSearch(value),
                  onSearchTap: () => _submitSearch(),
                ),
                14.szH,
                SearchCategoryChips(
                  categories: TenantSearchContent.categoriesFor(
                    _form.selectedCategory,
                  ),
                  onCategorySelected: _selectCategory,
                ),
                18.szH,
                const SearchSectionTitle('مناطق مقترحة'),
                10.szH,
                SuggestedAreasGrid(
                  areas: TenantSearchContent.suggestedAreas,
                  selectedArea: _form.selectedArea,
                  onAreaSelected: _selectArea,
                ),
                18.szH,
                const SearchSectionTitle('بحثت عنها مؤخراً'),
                6.szH,
                for (final search in _form.recentSearches)
                  RecentSearchRow(
                    search: search,
                    onTap: () => _selectRecent(search),
                  ),
                24.szH,
              ],
            ),
          ),
        ),
        bottomNavigationBar: SafeArea(
          top: false,
          child: HomeBottomNav(
            items: [
              const HomeBottomNavItemData(
                icon: Icons.home_outlined,
                label: 'الرئيسية',
              ),
              HomeBottomNavItemData(
                icon: Icons.favorite_border_rounded,
                label: 'المحفوظات',
                onTap: () => Go.to(const FavoritesScreen()),
              ),
              const HomeBottomNavItemData(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'الشات',
              ),
              HomeBottomNavItemData(
                icon: Icons.notifications_none_rounded,
                label: 'الإشعارات',
              ),
              HomeBottomNavItemData(
                icon: Icons.person_outline_rounded,
                label: 'الحساب',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
