import 'package:equatable/equatable.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import '../profile_json.dart';
import 'profile_account_details_content.dart';

class OwnerProfileContent extends Equatable {
  const OwnerProfileContent({
    required this.owner,
    required this.stats,
    required this.accountDetails,
    required this.privacyNotice,
    required this.recentReviews,
  });

  const OwnerProfileContent.initial()
    : owner = const OwnerProfileIdentityContent.initial(),
      stats = const OwnerProfileStatsContent.initial(),
      accountDetails = const ProfileAccountDetailsContent.initial(),
      privacyNotice = const OwnerProfilePrivacyNoticeContent.initial(),
      recentReviews = const [];

  factory OwnerProfileContent.fromJson(Map<String, dynamic> json) {
    return OwnerProfileContent(
      owner: OwnerProfileIdentityContent.fromJson(
        profileJsonMap(json['owner']),
      ),
      stats: OwnerProfileStatsContent.fromJson(profileJsonMap(json['stats'])),
      accountDetails: ProfileAccountDetailsContent.fromJson(
        profileJsonMap(json['account_details']),
      ),
      privacyNotice: OwnerProfilePrivacyNoticeContent.fromJson(
        profileJsonMap(json['privacy_notice']),
      ),
      recentReviews:
          (json['recent_reviews'] as List?)
              ?.map(
                (review) =>
                    OwnerProfileReviewContent.fromJson(profileJsonMap(review)),
              )
              .toList(growable: false) ??
          const [],
    );
  }

  static const String cacheKey = 'owner_profile';

  final OwnerProfileIdentityContent owner;
  final OwnerProfileStatsContent stats;
  final ProfileAccountDetailsContent accountDetails;
  final OwnerProfilePrivacyNoticeContent privacyNotice;
  final List<OwnerProfileReviewContent> recentReviews;

  Map<String, dynamic> toJson() => {
    'owner': owner.toJson(),
    'stats': stats.toJson(),
    'account_details': accountDetails.toJson(),
    'privacy_notice': privacyNotice.toJson(),
    'recent_reviews': recentReviews
        .map((review) => review.toJson())
        .toList(growable: false),
  };

  OwnerProfileContent copyWith({
    OwnerProfileIdentityContent? owner,
    OwnerProfileStatsContent? stats,
    ProfileAccountDetailsContent? accountDetails,
    OwnerProfilePrivacyNoticeContent? privacyNotice,
    List<OwnerProfileReviewContent>? recentReviews,
  }) {
    return OwnerProfileContent(
      owner: owner ?? this.owner,
      stats: stats ?? this.stats,
      accountDetails: accountDetails ?? this.accountDetails,
      privacyNotice: privacyNotice ?? this.privacyNotice,
      recentReviews: recentReviews ?? this.recentReviews,
    );
  }

  @override
  List<Object?> get props => [
    owner,
    stats,
    accountDetails,
    privacyNotice,
    recentReviews,
  ];
}

class OwnerProfileIdentityContent extends Equatable {
  const OwnerProfileIdentityContent({
    required this.id,
    required this.fullName,
    required this.avatar,
    required this.isVerified,
    required this.roleBadge,
    required this.averageRating,
    required this.reviewsCount,
    required this.ratingLabel,
    required this.memberSinceLabel,
  });

  const OwnerProfileIdentityContent.initial()
    : id = '',
      fullName = '',
      avatar = null,
      isVerified = false,
      roleBadge = '',
      averageRating = 0,
      reviewsCount = 0,
      ratingLabel = '',
      memberSinceLabel = '';

  factory OwnerProfileIdentityContent.fromJson(Map<String, dynamic> json) {
    return OwnerProfileIdentityContent(
      id: profileString(json['id']),
      fullName: profileString(json['full_name'] ?? json['name']),
      avatar: profileNullableString(json['avatar']),
      isVerified: json['is_verified'] ?? false,
      roleBadge: profileString(json['role_badge']),
      averageRating: profileDouble(json['average_rating']),
      reviewsCount: profileInt(json['reviews_count']),
      ratingLabel: profileString(json['rating_label']),
      memberSinceLabel: profileString(json['member_since_label']),
    );
  }

  final String id;
  final String fullName;
  final String? avatar;
  final bool isVerified;
  final String roleBadge;
  final double averageRating;
  final int reviewsCount;
  final String ratingLabel;
  final String memberSinceLabel;

  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': fullName,
    'avatar': avatar,
    'is_verified': isVerified,
    'role_badge': roleBadge,
    'average_rating': averageRating,
    'reviews_count': reviewsCount,
    'rating_label': ratingLabel,
    'member_since_label': memberSinceLabel,
  };

  OwnerProfileIdentityContent copyWith({
    String? id,
    String? fullName,
    String? avatar,
    bool clearAvatar = false,
    bool? isVerified,
    String? roleBadge,
    double? averageRating,
    int? reviewsCount,
    String? ratingLabel,
    String? memberSinceLabel,
  }) {
    return OwnerProfileIdentityContent(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      isVerified: isVerified ?? this.isVerified,
      roleBadge: roleBadge ?? this.roleBadge,
      averageRating: averageRating ?? this.averageRating,
      reviewsCount: reviewsCount ?? this.reviewsCount,
      ratingLabel: ratingLabel ?? this.ratingLabel,
      memberSinceLabel: memberSinceLabel ?? this.memberSinceLabel,
    );
  }

  @override
  List<Object?> get props => [
    id,
    fullName,
    avatar,
    isVerified,
    roleBadge,
    averageRating,
    reviewsCount,
    ratingLabel,
    memberSinceLabel,
  ];
}

class OwnerProfileStatsContent extends Equatable {
  const OwnerProfileStatsContent({
    required this.propertiesCount,
    required this.propertiesLabel,
    required this.reviewsCount,
    required this.reviewsLabel,
    required this.acceptanceRate,
    required this.acceptanceLabel,
    required this.formattedAcceptanceRate,
    this.hasAcceptanceRate = true,
  });

  const OwnerProfileStatsContent.initial()
    : propertiesCount = 0,
      propertiesLabel = '',
      reviewsCount = 0,
      reviewsLabel = '',
      acceptanceRate = 0,
      acceptanceLabel = '',
      formattedAcceptanceRate = '',
      hasAcceptanceRate = false;

  factory OwnerProfileStatsContent.fromJson(Map<String, dynamic> json) {
    final rate = double.tryParse(json['acceptance_rate']?.toString() ?? '');
    return OwnerProfileStatsContent(
      propertiesCount: profileInt(json['properties_count']),
      propertiesLabel: profileString(json['properties_label']),
      reviewsCount: profileInt(json['reviews_count']),
      reviewsLabel: profileString(json['reviews_label']),
      acceptanceRate: profileInt(json['acceptance_rate']),
      acceptanceLabel: profileString(json['acceptance_label']),
      formattedAcceptanceRate: profileString(json['formatted_acceptance_rate']),
      hasAcceptanceRate:
          (rate != null && rate.isFinite && rate >= 0 && rate <= 100) ||
          profileString(json['formatted_acceptance_rate']).isNotEmpty,
    );
  }

  final int propertiesCount;
  final String propertiesLabel;
  final int reviewsCount;
  final String reviewsLabel;
  final int acceptanceRate;
  final String acceptanceLabel;
  final String formattedAcceptanceRate;
  final bool hasAcceptanceRate;

  String get displayAcceptanceRate => formattedAcceptanceRate.isNotEmpty
      ? formattedAcceptanceRate
      : hasAcceptanceRate
      ? '$acceptanceRate%'
      : LocaleKeys.notSetYet;

  Map<String, dynamic> toJson() => {
    'properties_count': propertiesCount,
    'properties_label': propertiesLabel,
    'reviews_count': reviewsCount,
    'reviews_label': reviewsLabel,
    if (hasAcceptanceRate) 'acceptance_rate': acceptanceRate,
    'acceptance_label': acceptanceLabel,
    'formatted_acceptance_rate': formattedAcceptanceRate,
  };

  OwnerProfileStatsContent copyWith({
    int? propertiesCount,
    String? propertiesLabel,
    int? reviewsCount,
    String? reviewsLabel,
    int? acceptanceRate,
    String? acceptanceLabel,
    String? formattedAcceptanceRate,
    bool? hasAcceptanceRate,
  }) {
    return OwnerProfileStatsContent(
      propertiesCount: propertiesCount ?? this.propertiesCount,
      propertiesLabel: propertiesLabel ?? this.propertiesLabel,
      reviewsCount: reviewsCount ?? this.reviewsCount,
      reviewsLabel: reviewsLabel ?? this.reviewsLabel,
      acceptanceRate: acceptanceRate ?? this.acceptanceRate,
      acceptanceLabel: acceptanceLabel ?? this.acceptanceLabel,
      formattedAcceptanceRate:
          formattedAcceptanceRate ?? this.formattedAcceptanceRate,
      hasAcceptanceRate:
          hasAcceptanceRate ??
          (acceptanceRate != null || formattedAcceptanceRate?.isNotEmpty == true
              ? true
              : this.hasAcceptanceRate),
    );
  }

  @override
  List<Object?> get props => [
    propertiesCount,
    propertiesLabel,
    reviewsCount,
    reviewsLabel,
    acceptanceRate,
    acceptanceLabel,
    formattedAcceptanceRate,
    hasAcceptanceRate,
  ];
}

class OwnerProfilePrivacyNoticeContent extends Equatable {
  const OwnerProfilePrivacyNoticeContent({
    required this.icon,
    required this.text,
  });

  const OwnerProfilePrivacyNoticeContent.initial() : icon = '', text = '';

  factory OwnerProfilePrivacyNoticeContent.fromJson(Map<String, dynamic> json) {
    return OwnerProfilePrivacyNoticeContent(
      icon: profileString(json['icon']),
      text: profileString(json['text']),
    );
  }

  final String icon;
  final String text;

  Map<String, dynamic> toJson() => {'icon': icon, 'text': text};

  OwnerProfilePrivacyNoticeContent copyWith({String? icon, String? text}) {
    return OwnerProfilePrivacyNoticeContent(
      icon: icon ?? this.icon,
      text: text ?? this.text,
    );
  }

  @override
  List<Object?> get props => [icon, text];
}

class OwnerProfileReviewContent extends Equatable {
  const OwnerProfileReviewContent({
    required this.id,
    required this.reviewerName,
    required this.comment,
    required this.rating,
    required this.dateLabel,
  });

  const OwnerProfileReviewContent.initial()
    : id = '',
      reviewerName = '',
      comment = '',
      rating = 0,
      dateLabel = '';

  factory OwnerProfileReviewContent.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> reviewer = profileJsonMap(json['reviewer']);
    return OwnerProfileReviewContent(
      id: profileString(json['id']),
      reviewerName: profileString(
        json['reviewer_name'] ??
            json['tenant_name'] ??
            reviewer['name'] ??
            json['name'],
      ),
      comment: profileString(json['comment'] ?? json['text'] ?? json['review']),
      rating: profileDouble(json['rating']),
      dateLabel: profileString(json['date_label'] ?? json['created_at']),
    );
  }

  final String id;
  final String reviewerName;
  final String comment;
  final double rating;
  final String dateLabel;

  Map<String, dynamic> toJson() => {
    'id': id,
    'reviewer_name': reviewerName,
    'comment': comment,
    'rating': rating,
    'date_label': dateLabel,
  };

  OwnerProfileReviewContent copyWith({
    String? id,
    String? reviewerName,
    String? comment,
    double? rating,
    String? dateLabel,
  }) {
    return OwnerProfileReviewContent(
      id: id ?? this.id,
      reviewerName: reviewerName ?? this.reviewerName,
      comment: comment ?? this.comment,
      rating: rating ?? this.rating,
      dateLabel: dateLabel ?? this.dateLabel,
    );
  }

  @override
  List<Object?> get props => [id, reviewerName, comment, rating, dateLabel];
}
