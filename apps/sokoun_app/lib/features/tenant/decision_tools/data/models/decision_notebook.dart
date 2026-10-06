import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class PropertyDecision extends Equatable {
  const PropertyDecision({
    required this.propertyId,
    required this.title,
    this.list = '',
    this.note = '',
    this.checkedItems = const {},
  });
  const PropertyDecision.initial()
    : propertyId = '',
      title = '',
      list = '',
      note = '',
      checkedItems = const {};
  factory PropertyDecision.fromJson(Map<String, dynamic> json) =>
      PropertyDecision(
        propertyId: json['property_id'] as String? ?? '',
        title: json['title'] as String? ?? '',
        list: json['list'] as String? ?? '',
        note: json['note'] as String? ?? '',
        checkedItems: (json['checked_items'] as List? ?? const [])
            .whereType<String>()
            .toSet(),
      );
  final String propertyId;
  final String title;
  final String list;
  final String note;
  final Set<String> checkedItems;
  PropertyDecision copyWith({
    String? propertyId,
    String? title,
    String? list,
    String? note,
    Set<String>? checkedItems,
  }) => PropertyDecision(
    propertyId: propertyId ?? this.propertyId,
    title: title ?? this.title,
    list: list ?? this.list,
    note: note ?? this.note,
    checkedItems: checkedItems ?? this.checkedItems,
  );
  Map<String, dynamic> toJson() => {
    'property_id': propertyId,
    'title': title,
    'list': list,
    'note': note,
    'checked_items': checkedItems.toList(),
  };
  @override
  List<Object?> get props => [propertyId, title, list, note, checkedItems];
}

class SavedPropertySearch extends Equatable {
  const SavedPropertySearch({
    required this.id,
    required this.name,
    required this.filters,
  });
  const SavedPropertySearch.initial()
    : id = '',
      name = '',
      filters = const PropertySearchFilters.initial();
  factory SavedPropertySearch.fromJson(Map<String, dynamic> json) =>
      SavedPropertySearch(
        id: json['id'] as String? ?? '',
        name: json['name'] as String? ?? '',
        filters: PropertySearchFilters.fromJson(
          Map<String, dynamic>.from(json['filters'] as Map? ?? const {}),
        ),
      );
  final String id;
  final String name;
  final PropertySearchFilters filters;
  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'filters': filters.toJson(),
  };
  SavedPropertySearch copyWith({
    String? id,
    String? name,
    PropertySearchFilters? filters,
  }) => SavedPropertySearch(
    id: id ?? this.id,
    name: name ?? this.name,
    filters: filters ?? this.filters,
  );
  @override
  List<Object?> get props => [id, name, filters];
}

class DecisionNotebook extends Equatable {
  const DecisionNotebook({
    this.properties = const [],
    this.comparisonIds = const [],
    this.searches = const [],
  });
  const DecisionNotebook.initial()
    : properties = const [],
      comparisonIds = const [],
      searches = const [];
  factory DecisionNotebook.fromJson(
    Map<String, dynamic> json,
  ) => DecisionNotebook(
    properties: (json['properties'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) =>
              PropertyDecision.fromJson(Map<String, dynamic>.from(value)),
        )
        .where((property) => property.propertyId.isNotEmpty)
        .toList(growable: false),
    comparisonIds: (json['comparison_ids'] as List? ?? const [])
        .whereType<String>()
        .where((id) => id.isNotEmpty)
        .toSet()
        .take(3)
        .toList(growable: false),
    searches: (json['searches'] as List? ?? const [])
        .whereType<Map>()
        .map(
          (value) =>
              SavedPropertySearch.fromJson(Map<String, dynamic>.from(value)),
        )
        .where((search) => search.id.isNotEmpty)
        .toList(growable: false),
  );
  final List<PropertyDecision> properties;
  final List<String> comparisonIds;
  final List<SavedPropertySearch> searches;
  PropertyDecision decisionFor(String propertyId, String title) =>
      properties.firstWhere(
        (entry) => entry.propertyId == propertyId,
        orElse: () => PropertyDecision(propertyId: propertyId, title: title),
      );
  DecisionNotebook copyWith({
    List<PropertyDecision>? properties,
    List<String>? comparisonIds,
    List<SavedPropertySearch>? searches,
  }) => DecisionNotebook(
    properties: properties ?? this.properties,
    comparisonIds: comparisonIds ?? this.comparisonIds,
    searches: searches ?? this.searches,
  );
  Map<String, dynamic> toJson() => {
    'properties': properties.map((entry) => entry.toJson()).toList(),
    'comparison_ids': comparisonIds,
    'searches': searches.map((entry) => entry.toJson()).toList(),
  };
  @override
  List<Object?> get props => [properties, comparisonIds, searches];
}
