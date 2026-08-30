import 'package:equatable/equatable.dart';

import 'property_details_model.dart';

class PropertySearchFilterEntry extends Equatable {
  final String id;
  final String value;

  const PropertySearchFilterEntry({required this.id, required this.value});

  const PropertySearchFilterEntry.initial() : id = '', value = '';

  factory PropertySearchFilterEntry.fromJson(Map<String, dynamic> json) {
    return PropertySearchFilterEntry(
      id: json['id'] as String? ?? '',
      value: json['value'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {'id': id, 'value': value};

  PropertySearchFilterEntry copyWith({String? id, String? value}) {
    return PropertySearchFilterEntry(
      id: id ?? this.id,
      value: value ?? this.value,
    );
  }

  @override
  List<Object?> get props => [id, value];
}

class PropertySearchFilters extends Equatable {
  final String search;
  final String city;
  final String district;
  final String ordering;
  final int page;
  final int pageSize;
  final String priceMin;
  final String priceMax;
  final String propertyType;
  final String pricePeriod;
  final String suitableFor;
  final String isFurnished;
  final String isVerified;
  final String smokingAllowed;
  final String bedrooms;
  final String bathrooms;
  final Set<String> amenities;

  const PropertySearchFilters({
    required this.search,
    required this.city,
    required this.district,
    required this.ordering,
    required this.page,
    required this.pageSize,
    required this.priceMin,
    required this.priceMax,
    required this.propertyType,
    required this.pricePeriod,
    required this.suitableFor,
    required this.isFurnished,
    required this.isVerified,
    required this.smokingAllowed,
    required this.bedrooms,
    required this.bathrooms,
    required this.amenities,
  });

  const PropertySearchFilters.initial({
    this.search = '',
    this.city = '',
    this.district = '',
    this.ordering = '-created_at',
    this.page = 1,
    this.pageSize = 10,
    this.priceMin = '',
    this.priceMax = '',
    this.propertyType = '',
    this.pricePeriod = '',
    this.suitableFor = '',
    this.isFurnished = '',
    this.isVerified = '',
    this.smokingAllowed = '',
    this.bedrooms = '',
    this.bathrooms = '',
    this.amenities = const {},
  });

  factory PropertySearchFilters.fromJson(Map<String, dynamic> json) {
    return PropertySearchFilters(
      search: json['search'] as String? ?? '',
      city: json['city'] as String? ?? '',
      district: json['district'] as String? ?? '',
      ordering: json['ordering'] as String? ?? '-created_at',
      page: (json['page'] as num?)?.toInt() ?? 1,
      pageSize: (json['page_size'] as num?)?.toInt() ?? 10,
      priceMin: json['price_min'] as String? ?? '',
      priceMax: json['price_max'] as String? ?? '',
      propertyType: json['property_type'] as String? ?? '',
      pricePeriod: json['price_period'] as String? ?? '',
      suitableFor: json['suitable_for'] as String? ?? '',
      isFurnished: json['is_furnished'] as String? ?? '',
      isVerified: json['is_verified'] as String? ?? '',
      smokingAllowed: json['smoking_allowed'] as String? ?? '',
      bedrooms: json['bedrooms'] as String? ?? '',
      bathrooms: json['bathrooms'] as String? ?? '',
      amenities: (json['amenities'] as List? ?? const [])
          .map((item) => item.toString())
          .toSet(),
    );
  }

  String get combinedSearch => [
    search.trim(),
    city.trim(),
    district.trim(),
  ].where((value) => value.isNotEmpty).toSet().join(' ');

  int get activeCount => activeFilters.length;

  String get cacheKey {
    final Map<String, dynamic> cacheDimensions = toQueryParameters()
      ..remove('page');
    final List<String> keys = cacheDimensions.keys.toList()..sort();
    final String identity = keys
        .map(
          (key) =>
              '${Uri.encodeQueryComponent(key)}=${Uri.encodeQueryComponent(cacheDimensions[key].toString())}',
        )
        .join('&');
    return 'property_search_$identity';
  }

  List<PropertySearchFilterEntry> get activeFilters => [
    if (city.trim().isNotEmpty)
      PropertySearchFilterEntry(id: 'city', value: city.trim()),
    if (district.trim().isNotEmpty)
      PropertySearchFilterEntry(id: 'district', value: district.trim()),
    if (priceMin.trim().isNotEmpty)
      PropertySearchFilterEntry(id: 'price_min', value: priceMin.trim()),
    if (priceMax.trim().isNotEmpty)
      PropertySearchFilterEntry(id: 'price_max', value: priceMax.trim()),
    if (propertyType.isNotEmpty)
      PropertySearchFilterEntry(id: 'property_type', value: propertyType),
    if (pricePeriod.isNotEmpty)
      PropertySearchFilterEntry(id: 'price_period', value: pricePeriod),
    if (suitableFor.isNotEmpty)
      PropertySearchFilterEntry(id: 'suitable_for', value: suitableFor),
    if (isFurnished.isNotEmpty)
      PropertySearchFilterEntry(id: 'is_furnished', value: isFurnished),
    if (isVerified.isNotEmpty)
      PropertySearchFilterEntry(id: 'is_verified', value: isVerified),
    if (smokingAllowed.isNotEmpty)
      PropertySearchFilterEntry(id: 'smoking_allowed', value: smokingAllowed),
    if (bedrooms.isNotEmpty)
      PropertySearchFilterEntry(id: 'bedrooms', value: bedrooms),
    if (bathrooms.isNotEmpty)
      PropertySearchFilterEntry(id: 'bathrooms', value: bathrooms),
    for (final String amenity in amenities)
      PropertySearchFilterEntry(id: amenity, value: 'true'),
    if (ordering != '-created_at')
      PropertySearchFilterEntry(id: 'ordering', value: ordering),
  ];

  Map<String, dynamic> toQueryParameters() {
    final Map<String, dynamic> queryParameters = {
      'ordering': ordering,
      'page': page,
      'page_size': pageSize,
    };
    final String query = combinedSearch;
    if (query.isNotEmpty) queryParameters['search'] = query;
    if (priceMin.isNotEmpty) queryParameters['price_min'] = priceMin;
    if (priceMax.isNotEmpty) queryParameters['price_max'] = priceMax;
    if (propertyType.isNotEmpty) {
      queryParameters['property_type'] = propertyType;
    }
    if (pricePeriod.isNotEmpty) queryParameters['price_period'] = pricePeriod;
    if (suitableFor.isNotEmpty) queryParameters['suitable_for'] = suitableFor;
    if (isFurnished.isNotEmpty) {
      queryParameters['is_furnished'] = isFurnished;
    }
    if (isVerified.isNotEmpty) queryParameters['is_verified'] = isVerified;
    if (smokingAllowed.isNotEmpty) {
      queryParameters['smoking_allowed'] = smokingAllowed;
    }
    if (bedrooms.isNotEmpty) queryParameters['bedrooms'] = bedrooms;
    if (bathrooms.isNotEmpty) queryParameters['bathrooms'] = bathrooms;
    for (final String amenity in amenities) {
      queryParameters[amenity] = 'true';
    }
    return queryParameters;
  }

  Map<String, dynamic> toJson() => {
    'search': search,
    'city': city,
    'district': district,
    'ordering': ordering,
    'page': page,
    'page_size': pageSize,
    'price_min': priceMin,
    'price_max': priceMax,
    'property_type': propertyType,
    'price_period': pricePeriod,
    'suitable_for': suitableFor,
    'is_furnished': isFurnished,
    'is_verified': isVerified,
    'smoking_allowed': smokingAllowed,
    'bedrooms': bedrooms,
    'bathrooms': bathrooms,
    'amenities': amenities.toList(growable: false)..sort(),
  };

  PropertySearchFilters removeFilter(String id) {
    final Set<String> updatedAmenities = Set<String>.from(amenities)
      ..remove(id);
    return copyWith(
      city: id == 'city' ? '' : city,
      district: id == 'district' ? '' : district,
      priceMin: id == 'price_min' ? '' : priceMin,
      priceMax: id == 'price_max' ? '' : priceMax,
      propertyType: id == 'property_type' ? '' : propertyType,
      pricePeriod: id == 'price_period' ? '' : pricePeriod,
      suitableFor: id == 'suitable_for' ? '' : suitableFor,
      isFurnished: id == 'is_furnished' ? '' : isFurnished,
      isVerified: id == 'is_verified' ? '' : isVerified,
      smokingAllowed: id == 'smoking_allowed' ? '' : smokingAllowed,
      bedrooms: id == 'bedrooms' ? '' : bedrooms,
      bathrooms: id == 'bathrooms' ? '' : bathrooms,
      amenities: updatedAmenities,
      ordering: id == 'ordering' ? '-created_at' : ordering,
      page: 1,
    );
  }

  PropertySearchFilters clearFilters() =>
      PropertySearchFilters.initial(search: search, pageSize: pageSize);

  PropertySearchFilters copyWith({
    String? search,
    String? city,
    String? district,
    String? ordering,
    int? page,
    int? pageSize,
    String? priceMin,
    String? priceMax,
    String? propertyType,
    String? pricePeriod,
    String? suitableFor,
    String? isFurnished,
    String? isVerified,
    String? smokingAllowed,
    String? bedrooms,
    String? bathrooms,
    Set<String>? amenities,
  }) => PropertySearchFilters(
    search: search ?? this.search,
    city: city ?? this.city,
    district: district ?? this.district,
    ordering: ordering ?? this.ordering,
    page: page ?? this.page,
    pageSize: pageSize ?? this.pageSize,
    priceMin: priceMin ?? this.priceMin,
    priceMax: priceMax ?? this.priceMax,
    propertyType: propertyType ?? this.propertyType,
    pricePeriod: pricePeriod ?? this.pricePeriod,
    suitableFor: suitableFor ?? this.suitableFor,
    isFurnished: isFurnished ?? this.isFurnished,
    isVerified: isVerified ?? this.isVerified,
    smokingAllowed: smokingAllowed ?? this.smokingAllowed,
    bedrooms: bedrooms ?? this.bedrooms,
    bathrooms: bathrooms ?? this.bathrooms,
    amenities: amenities ?? this.amenities,
  );

  @override
  List<Object?> get props => [
    search,
    city,
    district,
    ordering,
    page,
    pageSize,
    priceMin,
    priceMax,
    propertyType,
    pricePeriod,
    suitableFor,
    isFurnished,
    isVerified,
    smokingAllowed,
    bedrooms,
    bathrooms,
    amenities,
  ];
}

class PropertySearchResponseModel extends Equatable {
  final int count;
  final String? next;
  final String? previous;
  final List<PropertyDetailsModel> results;

  const PropertySearchResponseModel({
    required this.count,
    required this.next,
    required this.previous,
    required this.results,
  });

  const PropertySearchResponseModel.initial()
    : count = 0,
      next = null,
      previous = null,
      results = const [];

  factory PropertySearchResponseModel.fromJson(Map<String, dynamic> json) =>
      PropertySearchResponseModel(
        count: (json['count'] as num?)?.toInt() ?? 0,
        next: json['next'] as String?,
        previous: json['previous'] as String?,
        results:
            (json['results'] as List?)
                ?.whereType<Map<String, dynamic>>()
                .map(PropertyDetailsModel.fromJson)
                .toList(growable: false) ??
            const [],
      );

  Map<String, dynamic> toJson() => {
    'count': count,
    'next': next,
    'previous': previous,
    'results': results.map((item) => item.toJson()).toList(growable: false),
  };

  PropertySearchResponseModel copyWith({
    int? count,
    String? next,
    String? previous,
    List<PropertyDetailsModel>? results,
  }) => PropertySearchResponseModel(
    count: count ?? this.count,
    next: next ?? this.next,
    previous: previous ?? this.previous,
    results: results ?? this.results,
  );

  @override
  List<Object?> get props => [count, next, previous, results];
}
