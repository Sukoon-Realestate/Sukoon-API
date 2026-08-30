import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/tenant/home/data/tenant_search_data.dart';

class TenantRecentSearchesCubit extends Cubit<List<RecentSearchContent>> {
  TenantRecentSearchesCubit() : super(const []);

  void loadRecentSearches() {
    emit(TenantSearchData.getRecentSearches());
  }

  Future<void> addRecentSearch(String title) async {
    final String normalizedTitle = title.trim();
    if (normalizedTitle.isEmpty) return;

    final List<RecentSearchContent> updatedSearches = [
      RecentSearchContent(title: normalizedTitle),
      for (final search in state)
        if (search.title != normalizedTitle) search,
    ].take(TenantSearchData.maxRecentSearches).toList(growable: false);
    await TenantSearchData.saveRecentSearches(updatedSearches);
    if (isClosed) return;
    emit(updatedSearches);
  }
}
