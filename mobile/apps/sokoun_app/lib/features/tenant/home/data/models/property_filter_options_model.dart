import 'package:equatable/equatable.dart';

class TenantFilterOption extends Equatable {
  const TenantFilterOption({
    required this.value,
    required this.label,
    this.id = '',
    this.queryParameter = '',
  });

  const TenantFilterOption.initial()
    : id = '',
      value = '',
      label = '',
      queryParameter = '';

  factory TenantFilterOption.fromJson(Map<String, dynamic> json) {
    final String value = _stringValue(
      json['value'] ?? json['slug'] ?? json['code'],
    );

    return TenantFilterOption(
      id: _stringValue(json['id']),
      value: value,
      label: _stringValue(json['label'] ?? json['name'] ?? value),
      queryParameter: _stringValue(
        json['query_parameter'] ?? json['query_param'],
      ),
    );
  }

  final String id;
  final String value;
  final String label;
  final String queryParameter;

  String get selectionValue => queryParameter.isEmpty ? value : queryParameter;

  Map<String, dynamic> toJson() => {
    if (id.isNotEmpty) 'id': id,
    'value': value,
    'label': label,
    if (queryParameter.isNotEmpty) 'query_parameter': queryParameter,
  };

  TenantFilterOption copyWith({
    String? id,
    String? value,
    String? label,
    String? queryParameter,
  }) {
    return TenantFilterOption(
      id: id ?? this.id,
      value: value ?? this.value,
      label: label ?? this.label,
      queryParameter: queryParameter ?? this.queryParameter,
    );
  }

  @override
  List<Object?> get props => [id, value, label, queryParameter];

  static String _stringValue(dynamic value) => value?.toString() ?? '';
}

class PropertyFilterOptionsModel extends Equatable {
  const PropertyFilterOptionsModel({
    required this.propertyTypes,
    required this.ordering,
    required this.bedrooms,
    required this.bathrooms,
    required this.pricePeriods,
    required this.suitableFor,
    required this.booleanOptions,
    required this.amenities,
    required this.defaultOrdering,
  });

  const PropertyFilterOptionsModel.initial()
    : propertyTypes = const [],
      ordering = const [],
      bedrooms = const [],
      bathrooms = const [],
      pricePeriods = const [],
      suitableFor = const [],
      booleanOptions = const [],
      amenities = const [],
      defaultOrdering = '';

  factory PropertyFilterOptionsModel.fromJson(Map<String, dynamic> json) {
    final List<TenantFilterOption> sharedCounts = _optionList(json['counts']);
    final Map<String, dynamic> defaults = json['defaults'] is Map
        ? Map<String, dynamic>.from(json['defaults'] as Map)
        : const {};

    return PropertyFilterOptionsModel(
      propertyTypes: _optionList(json['property_types']),
      ordering: _optionList(json['ordering']),
      bedrooms: _optionList(json['bedrooms'], fallback: sharedCounts),
      bathrooms: _optionList(json['bathrooms'], fallback: sharedCounts),
      pricePeriods: _optionList(json['price_periods']),
      suitableFor: _optionList(json['suitable_for']),
      booleanOptions: _optionList(json['boolean_options']),
      amenities: _optionList(json['amenities']),
      defaultOrdering:
          defaults['ordering']?.toString() ??
          json['default_ordering']?.toString() ??
          '',
    );
  }

  final List<TenantFilterOption> propertyTypes;
  final List<TenantFilterOption> ordering;
  final List<TenantFilterOption> bedrooms;
  final List<TenantFilterOption> bathrooms;
  final List<TenantFilterOption> pricePeriods;
  final List<TenantFilterOption> suitableFor;
  final List<TenantFilterOption> booleanOptions;
  final List<TenantFilterOption> amenities;
  final String defaultOrdering;

  Map<String, dynamic> toJson() => {
    'property_types': propertyTypes
        .map((option) => option.toJson())
        .toList(growable: false),
    'ordering': ordering
        .map((option) => option.toJson())
        .toList(growable: false),
    'bedrooms': bedrooms
        .map((option) => option.toJson())
        .toList(growable: false),
    'bathrooms': bathrooms
        .map((option) => option.toJson())
        .toList(growable: false),
    'price_periods': pricePeriods
        .map((option) => option.toJson())
        .toList(growable: false),
    'suitable_for': suitableFor
        .map((option) => option.toJson())
        .toList(growable: false),
    'boolean_options': booleanOptions
        .map((option) => option.toJson())
        .toList(growable: false),
    'amenities': amenities
        .map((option) => option.toJson())
        .toList(growable: false),
    'defaults': {'ordering': defaultOrdering},
  };

  PropertyFilterOptionsModel copyWith({
    List<TenantFilterOption>? propertyTypes,
    List<TenantFilterOption>? ordering,
    List<TenantFilterOption>? bedrooms,
    List<TenantFilterOption>? bathrooms,
    List<TenantFilterOption>? pricePeriods,
    List<TenantFilterOption>? suitableFor,
    List<TenantFilterOption>? booleanOptions,
    List<TenantFilterOption>? amenities,
    String? defaultOrdering,
  }) {
    return PropertyFilterOptionsModel(
      propertyTypes: propertyTypes ?? this.propertyTypes,
      ordering: ordering ?? this.ordering,
      bedrooms: bedrooms ?? this.bedrooms,
      bathrooms: bathrooms ?? this.bathrooms,
      pricePeriods: pricePeriods ?? this.pricePeriods,
      suitableFor: suitableFor ?? this.suitableFor,
      booleanOptions: booleanOptions ?? this.booleanOptions,
      amenities: amenities ?? this.amenities,
      defaultOrdering: defaultOrdering ?? this.defaultOrdering,
    );
  }

  @override
  List<Object?> get props => [
    propertyTypes,
    ordering,
    bedrooms,
    bathrooms,
    pricePeriods,
    suitableFor,
    booleanOptions,
    amenities,
    defaultOrdering,
  ];

  static List<TenantFilterOption> _optionList(
    dynamic value, {
    List<TenantFilterOption> fallback = const [],
  }) {
    final dynamic items = value is Map ? value['results'] : value;
    if (items is! List) return fallback;

    return items
        .map((item) {
          if (item is Map) {
            return TenantFilterOption.fromJson(Map<String, dynamic>.from(item));
          }
          final String value = item?.toString() ?? '';
          return TenantFilterOption(value: value, label: value);
        })
        .where((option) => option.selectionValue.isNotEmpty)
        .toList(growable: false);
  }
}
