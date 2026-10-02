part of '../../imports.dart';

class OwnerPropertyAnalyticsContent extends Equatable {
  const OwnerPropertyAnalyticsContent({
    this.hasDetails = true,
    required this.views,
    required this.visitRequests,
    required this.saves,
    required this.acceptanceRate,
    required this.viewHistory,
    required this.spaceInterest,
    required this.priceInterest,
    required this.locationInterest,
    required this.amenitiesInterest,
  });

  factory OwnerPropertyAnalyticsContent.initial() {
    return const OwnerPropertyAnalyticsContent(
      hasDetails: false,
      views: 0,
      visitRequests: 0,
      saves: 0,
      acceptanceRate: 0,
      viewHistory: [],
      spaceInterest: 0,
      priceInterest: 0,
      locationInterest: 0,
      amenitiesInterest: 0,
    );
  }

  factory OwnerPropertyAnalyticsContent.fromJson(Map<String, dynamic> json) {
    return OwnerPropertyAnalyticsContent(
      hasDetails:
          json['has_details'] as bool? ??
          const [
            'views',
            'visit_requests',
            'saves',
            'acceptance_rate',
            'view_history',
            'space_interest',
            'price_interest',
            'location_interest',
            'amenities_interest',
          ].every((key) => json[key] != null),
      views: json['views'] ?? 0,
      visitRequests: json['visit_requests'] ?? 0,
      saves: json['saves'] ?? 0,
      acceptanceRate: json['acceptance_rate'] ?? 0,
      viewHistory: List<int>.from(json['view_history'] ?? const <int>[]),
      spaceInterest: json['space_interest'] ?? 0,
      priceInterest: json['price_interest'] ?? 0,
      locationInterest: json['location_interest'] ?? 0,
      amenitiesInterest: json['amenities_interest'] ?? 0,
    );
  }

  final int views;
  final bool hasDetails;
  final int visitRequests;
  final int saves;
  final int acceptanceRate;
  final List<int> viewHistory;
  final int spaceInterest;
  final int priceInterest;
  final int locationInterest;
  final int amenitiesInterest;

  Map<String, dynamic> toJson() {
    return {
      'has_details': hasDetails,
      'views': views,
      'visit_requests': visitRequests,
      'saves': saves,
      'acceptance_rate': acceptanceRate,
      'view_history': viewHistory,
      'space_interest': spaceInterest,
      'price_interest': priceInterest,
      'location_interest': locationInterest,
      'amenities_interest': amenitiesInterest,
    };
  }

  OwnerPropertyAnalyticsContent copyWith({
    bool? hasDetails,
    int? views,
    int? visitRequests,
    int? saves,
    int? acceptanceRate,
    List<int>? viewHistory,
    int? spaceInterest,
    int? priceInterest,
    int? locationInterest,
    int? amenitiesInterest,
  }) {
    return OwnerPropertyAnalyticsContent(
      hasDetails: hasDetails ?? this.hasDetails,
      views: views ?? this.views,
      visitRequests: visitRequests ?? this.visitRequests,
      saves: saves ?? this.saves,
      acceptanceRate: acceptanceRate ?? this.acceptanceRate,
      viewHistory: viewHistory ?? this.viewHistory,
      spaceInterest: spaceInterest ?? this.spaceInterest,
      priceInterest: priceInterest ?? this.priceInterest,
      locationInterest: locationInterest ?? this.locationInterest,
      amenitiesInterest: amenitiesInterest ?? this.amenitiesInterest,
    );
  }

  @override
  List<Object?> get props => [
    hasDetails,
    views,
    visitRequests,
    saves,
    acceptanceRate,
    viewHistory,
    spaceInterest,
    priceInterest,
    locationInterest,
    amenitiesInterest,
  ];
}
