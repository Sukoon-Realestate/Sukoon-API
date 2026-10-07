import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:equatable/equatable.dart';

class PropertyReview extends Equatable {
  const PropertyReview({
    this.rentalSelection,
    required this.id,
    required this.name,
    required this.comment,
    required this.createdAt,
    this.rating,
    this.cleanliness,
    this.accuracy,
    this.ownerInteraction,
    this.isVerified = false,
    this.avatarUrl = '',
  });
  const PropertyReview.initial()
    : rentalSelection = null,
      id = '',
      name = '',
      comment = '',
      createdAt = '',
      rating = null,
      cleanliness = null,
      accuracy = null,
      ownerInteraction = null,
      isVerified = false,
      avatarUrl = '';
  factory PropertyReview.fromJson(Map<String, dynamic> json) {
    final Map tenant = json['tenant'] is Map ? json['tenant'] as Map : const {};
    return PropertyReview(
      rentalSelection: RentalSelection.fromRecord(json),
      id: json['id']?.toString() ?? '',
      name: tenant['name']?.toString() ?? '',
      comment: json['comment']?.toString() ?? '',
      createdAt: json['created_at']?.toString() ?? '',
      rating: _number(json['overall_rating']),
      cleanliness: _number(json['cleanliness_rating']),
      accuracy: _number(json['listing_accuracy_rating']),
      ownerInteraction: _number(json['owner_interaction_rating']),
      isVerified: tenant['is_verified'] ?? false,
      avatarUrl: tenant['avatar']?.toString() ?? '',
    );
  }
  final RentalSelection? rentalSelection;
  final String id, name, comment, createdAt;
  final double? rating, cleanliness, accuracy, ownerInteraction;
  final bool isVerified;
  final String avatarUrl;
  static double? _number(Object? v) =>
      v is num ? v.toDouble() : double.tryParse(v?.toString() ?? '');
  Map<String, dynamic> toJson() => {
    'id': id,
    if (rentalSelection != null) ...{
      'offer_id': rentalSelection!.offerId,
      'offer_snapshot': rentalSelection!.toJson(),
    },
    'tenant': {'name': name, 'is_verified': isVerified, 'avatar': avatarUrl},
    'comment': comment,
    'created_at': createdAt,
    'overall_rating': rating,
    'cleanliness_rating': cleanliness,
    'listing_accuracy_rating': accuracy,
    'owner_interaction_rating': ownerInteraction,
  };
  PropertyReview copyWith({
    RentalSelection? rentalSelection,
    String? id,
    String? name,
    String? comment,
    String? createdAt,
    double? rating,
    double? cleanliness,
    double? accuracy,
    double? ownerInteraction,
    bool? isVerified,
    String? avatarUrl,
  }) => PropertyReview(
    rentalSelection: rentalSelection ?? this.rentalSelection,
    id: id ?? this.id,
    name: name ?? this.name,
    comment: comment ?? this.comment,
    createdAt: createdAt ?? this.createdAt,
    rating: rating ?? this.rating,
    cleanliness: cleanliness ?? this.cleanliness,
    accuracy: accuracy ?? this.accuracy,
    ownerInteraction: ownerInteraction ?? this.ownerInteraction,
    isVerified: isVerified ?? this.isVerified,
    avatarUrl: avatarUrl ?? this.avatarUrl,
  );
  @override
  List<Object?> get props => [
    rentalSelection,
    id,
    name,
    comment,
    createdAt,
    rating,
    cleanliness,
    accuracy,
    ownerInteraction,
    isVerified,
    avatarUrl,
  ];
}
