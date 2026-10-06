import 'package:equatable/equatable.dart';

class MyReview extends Equatable {
  const MyReview({
    required this.id,
    required this.propertyId,
    required this.propertyTitle,
    required this.propertyImage,
    required this.visitId,
    required this.rating,
    required this.comment,
    required this.createdAt,
  });
  const MyReview.initial()
    : id = '',
      propertyId = '',
      propertyTitle = '',
      propertyImage = '',
      visitId = '',
      rating = 0,
      comment = '',
      createdAt = '';

  factory MyReview.fromJson(Map<String, dynamic> json) => MyReview(
    id: json['id']?.toString() ?? '',
    propertyId: json['property_id']?.toString() ?? '',
    propertyTitle: json['property_title']?.toString() ?? '',
    propertyImage: json['property_image']?.toString() ?? '',
    visitId: json['visit_id']?.toString() ?? '',
    rating: (json['rating'] as num?)?.toDouble() ?? 0,
    comment: json['comment']?.toString() ?? '',
    createdAt: json['created_at']?.toString() ?? '',
  );
  final String id;
  final String propertyId;
  final String propertyTitle;
  final String propertyImage;
  final String visitId;
  final double rating;
  final String comment;
  final String createdAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'property_id': propertyId,
    'property_title': propertyTitle,
    'property_image': propertyImage,
    'visit_id': visitId,
    'rating': rating,
    'comment': comment,
    'created_at': createdAt,
  };
  MyReview copyWith({
    String? id,
    String? propertyId,
    String? propertyTitle,
    String? propertyImage,
    String? visitId,
    double? rating,
    String? comment,
    String? createdAt,
  }) => MyReview(
    id: id ?? this.id,
    propertyId: propertyId ?? this.propertyId,
    propertyTitle: propertyTitle ?? this.propertyTitle,
    propertyImage: propertyImage ?? this.propertyImage,
    visitId: visitId ?? this.visitId,
    rating: rating ?? this.rating,
    comment: comment ?? this.comment,
    createdAt: createdAt ?? this.createdAt,
  );
  @override
  List<Object?> get props => [
    id,
    propertyId,
    propertyTitle,
    propertyImage,
    visitId,
    rating,
    comment,
    createdAt,
  ];
}
