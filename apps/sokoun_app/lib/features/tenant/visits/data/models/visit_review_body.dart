part of '../../imports.dart';

class VisitReviewBody {
  const VisitReviewBody({
    required this.cleanliness,
    required this.accuracy,
    required this.ownerInteraction,
    required this.comment,
  });
  const VisitReviewBody.initial()
    : cleanliness = 0,
      accuracy = 0,
      ownerInteraction = 0,
      comment = '';
  final int cleanliness, accuracy, ownerInteraction;
  final String comment;
  bool get isValid =>
      [cleanliness, accuracy, ownerInteraction].every((v) => v >= 1 && v <= 5);
  Map<String, dynamic> toJson() => {
    'cleanliness_rating': cleanliness,
    'listing_accuracy_rating': accuracy,
    'owner_interaction_rating': ownerInteraction,
    'comment': comment.trim(),
  };
  VisitReviewBody copyWith({
    int? cleanliness,
    int? accuracy,
    int? ownerInteraction,
    String? comment,
  }) => VisitReviewBody(
    cleanliness: cleanliness ?? this.cleanliness,
    accuracy: accuracy ?? this.accuracy,
    ownerInteraction: ownerInteraction ?? this.ownerInteraction,
    comment: comment ?? this.comment,
  );
}
