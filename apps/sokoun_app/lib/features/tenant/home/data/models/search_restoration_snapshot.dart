import 'property_search_model.dart';

class SearchRestorationSnapshot {
  const SearchRestorationSnapshot({
    required this.filters,
    this.loadedPages = 1,
    this.anchorId = '',
    this.offset = 0,
  });
  final PropertySearchFilters filters;
  final int loadedPages;
  final String anchorId;
  final double offset;
  factory SearchRestorationSnapshot.fromJson(Map<String, dynamic> json) =>
      SearchRestorationSnapshot(
        filters: PropertySearchFilters.fromJson(
          Map<String, dynamic>.from(json['filters'] as Map? ?? const {}),
        ),
        loadedPages: ((json['loaded_pages'] as num?)?.toInt() ?? 1).clamp(
          1,
          20,
        ),
        anchorId: json['anchor_id'] as String? ?? '',
        offset: ((json['offset'] as num?)?.toDouble() ?? 0).clamp(0, 100000),
      );
  Map<String, dynamic> toJson() => {
    'filters': filters.copyWith(page: 1).toJson(),
    'loaded_pages': loadedPages.clamp(1, 20),
    'anchor_id': anchorId,
    'offset': offset.isFinite ? offset.clamp(0, 100000) : 0,
  };
}
