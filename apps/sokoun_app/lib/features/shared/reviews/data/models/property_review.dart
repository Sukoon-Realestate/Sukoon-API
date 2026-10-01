import 'package:equatable/equatable.dart';

class PropertyReview extends Equatable {
  const PropertyReview({
    required this.id,
    required this.name,
    required this.comment,
    required this.createdAt,
    this.rating,
    this.cleanliness,
    this.accuracy,
    this.ownerInteraction,
    this.isVerified = false,
  });
  const PropertyReview.initial()
    : id = '',
      name = '',
      comment = '',
      createdAt = '',
      rating = null,
      cleanliness = null,
      accuracy = null,
      ownerInteraction = null,
      isVerified = false;
  factory PropertyReview.fromJson(Map<String, dynamic> json) {
    final Map tenant = json['tenant'] is Map ? json['tenant'] as Map : const {};
    return PropertyReview(
      id: json['id']?.toString() ?? '',
      name: tenant['name']?.toString() ?? '',
      comment: json['comment']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      rating: _number(json['overall_rating']),
      cleanliness: _number(json['cleanliness_rating']),
      accuracy: _number(json['listing_accuracy_rating']),
      ownerInteraction: _number(json['owner_interaction_rating']),
      isVerified: tenant['is_verified'] == true,
    );
  }
  final String id, name, comment, createdAt;
  final double? rating, cleanliness, accuracy, ownerInteraction;
  final bool isVerified;
  static double? _number(Object? v) =>
      v is num ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  Map<String, dynamic> toJson() => {
    'id': id,
    'tenant': {'name': name, 'is_verified': isVerified},
    'comment': comment,
    'created_at': createdAt,
    'overall_rating': rating,
    'cleanliness_rating': cleanliness,
    'listing_accuracy_rating': accuracy,
    'owner_interaction_rating': ownerInteraction,
  };
  PropertyReview copyWith({
    String? id,
    String? name,
    String? comment,
    String? createdAt,
    double? rating,
    double? cleanliness,
    double? accuracy,
    double? ownerInteraction,
    bool? isVerified,
  }) => PropertyReview(
    id: id ?? this.id,
    name: name ?? this.name,
    comment: comment ?? this.comment,
    createdAt: createdAt ?? this.createdAt,
    rating: rating ?? this.rating,
    cleanliness: cleanliness ?? this.cleanliness,
    accuracy: accuracy ?? this.accuracy,
    ownerInteraction: ownerInteraction ?? this.ownerInteraction,
    isVerified: isVerified ?? this.isVerified,
  );
  @override
  List<Object?> get props => [
    id,
    name,
    comment,
    createdAt,
    rating,
    cleanliness,
    accuracy,
    ownerInteraction,
    isVerified,
  ];
}
