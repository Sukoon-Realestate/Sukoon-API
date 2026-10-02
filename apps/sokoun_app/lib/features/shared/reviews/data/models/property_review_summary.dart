import 'package:equatable/equatable.dart';

class PropertyReviewSummary extends Equatable {
  const PropertyReviewSummary({this.totalReviews, this.averageRating});

  const PropertyReviewSummary.initial()
    : totalReviews = null,
      averageRating = null;

  factory PropertyReviewSummary.fromJson(Map<String, dynamic> json) =>
      PropertyReviewSummary(
        totalReviews: int.tryParse('${json['total_reviews'] ?? ''}'),
        averageRating: double.tryParse('${json['average_rating'] ?? ''}'),
      );

  final int? totalReviews;
  final double? averageRating;

  Map<String, dynamic> toJson() => {
    'total_reviews': totalReviews,
    'average_rating': averageRating,
  };

  PropertyReviewSummary copyWith({int? totalReviews, double? averageRating}) =>
      PropertyReviewSummary(
        totalReviews: totalReviews ?? this.totalReviews,
        averageRating: averageRating ?? this.averageRating,
      );

  @override
  List<Object?> get props => [totalReviews, averageRating];
}
