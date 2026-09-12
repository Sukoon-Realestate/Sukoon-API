part of '../../imports.dart';

class TenantProfileContent extends Equatable {
  const TenantProfileContent({
    required this.user,
    required this.stats,
    required this.menuItems,
    required this.accountDetails,
  });

  const TenantProfileContent.initial()
    : user = const TenantProfileUserContent.initial(),
      stats = const TenantProfileStatsContent.initial(),
      menuItems = const TenantProfileMenuItemsContent.initial(),
      accountDetails = const ProfileAccountDetailsContent.initial();

  factory TenantProfileContent.fromJson(Map<String, dynamic> json) {
    return TenantProfileContent(
      user: TenantProfileUserContent.fromJson(_profileJsonMap(json['user'])),
      stats: TenantProfileStatsContent.fromJson(_profileJsonMap(json['stats'])),
      menuItems: TenantProfileMenuItemsContent.fromJson(
        _profileJsonMap(json['menu_items']),
      ),
      accountDetails: ProfileAccountDetailsContent.fromJson(
        _profileJsonMap(json['account_details']),
      ),
    );
  }

  static const String cacheKey = 'tenant_profile';

  final TenantProfileUserContent user;
  final TenantProfileStatsContent stats;
  final TenantProfileMenuItemsContent menuItems;
  final ProfileAccountDetailsContent accountDetails;

  Map<String, dynamic> toJson() => {
    'user': user.toJson(),
    'stats': stats.toJson(),
    'menu_items': menuItems.toJson(),
    'account_details': accountDetails.toJson(),
  };

  TenantProfileContent copyWith({
    TenantProfileUserContent? user,
    TenantProfileStatsContent? stats,
    TenantProfileMenuItemsContent? menuItems,
    ProfileAccountDetailsContent? accountDetails,
  }) {
    return TenantProfileContent(
      user: user ?? this.user,
      stats: stats ?? this.stats,
      menuItems: menuItems ?? this.menuItems,
      accountDetails: accountDetails ?? this.accountDetails,
    );
  }

  @override
  List<Object?> get props => [user, stats, menuItems, accountDetails];
}

class TenantProfileUserContent extends Equatable {
  const TenantProfileUserContent({
    required this.id,
    required this.fullName,
    required this.firstName,
    required this.lastName,
    required this.avatar,
    required this.isVerified,
    required this.verificationBadge,
    required this.roleLabel,
    required this.memberSinceLabel,
    required this.memberSinceYear,
    required this.memberSinceMonth,
  });

  const TenantProfileUserContent.initial()
    : id = '',
      fullName = '',
      firstName = '',
      lastName = '',
      avatar = null,
      isVerified = false,
      verificationBadge = '',
      roleLabel = '',
      memberSinceLabel = '',
      memberSinceYear = 0,
      memberSinceMonth = '';

  factory TenantProfileUserContent.fromJson(Map<String, dynamic> json) {
    return TenantProfileUserContent(
      id: _profileString(json['id']),
      fullName: _profileString(json['full_name'] ?? json['name']),
      firstName: _profileString(json['first_name']),
      lastName: _profileString(json['last_name']),
      avatar: _profileNullableString(json['avatar']),
      isVerified: json['is_verified'] == true,
      verificationBadge: _profileString(json['verification_badge']),
      roleLabel: _profileString(json['role_label']),
      memberSinceLabel: _profileString(json['member_since_label']),
      memberSinceYear: _profileInt(json['member_since_year']),
      memberSinceMonth: _profileString(json['member_since_month']),
    );
  }

  final String id;
  final String fullName;
  final String firstName;
  final String lastName;
  final String? avatar;
  final bool isVerified;
  final String verificationBadge;
  final String roleLabel;
  final String memberSinceLabel;
  final int memberSinceYear;
  final String memberSinceMonth;

  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': fullName,
    'first_name': firstName,
    'last_name': lastName,
    'avatar': avatar,
    'is_verified': isVerified,
    'verification_badge': verificationBadge,
    'role_label': roleLabel,
    'member_since_label': memberSinceLabel,
    'member_since_year': memberSinceYear,
    'member_since_month': memberSinceMonth,
  };

  TenantProfileUserContent copyWith({
    String? id,
    String? fullName,
    String? firstName,
    String? lastName,
    String? avatar,
    bool clearAvatar = false,
    bool? isVerified,
    String? verificationBadge,
    String? roleLabel,
    String? memberSinceLabel,
    int? memberSinceYear,
    String? memberSinceMonth,
  }) {
    return TenantProfileUserContent(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      isVerified: isVerified ?? this.isVerified,
      verificationBadge: verificationBadge ?? this.verificationBadge,
      roleLabel: roleLabel ?? this.roleLabel,
      memberSinceLabel: memberSinceLabel ?? this.memberSinceLabel,
      memberSinceYear: memberSinceYear ?? this.memberSinceYear,
      memberSinceMonth: memberSinceMonth ?? this.memberSinceMonth,
    );
  }

  @override
  List<Object?> get props => [
    id,
    fullName,
    firstName,
    lastName,
    avatar,
    isVerified,
    verificationBadge,
    roleLabel,
    memberSinceLabel,
    memberSinceYear,
    memberSinceMonth,
  ];
}

class TenantProfileStatsContent extends Equatable {
  const TenantProfileStatsContent({
    required this.savedCount,
    required this.visitsCount,
    required this.reviewsCount,
  });

  const TenantProfileStatsContent.initial()
    : savedCount = 0,
      visitsCount = 0,
      reviewsCount = 0;

  factory TenantProfileStatsContent.fromJson(Map<String, dynamic> json) {
    return TenantProfileStatsContent(
      savedCount: _profileInt(json['saved_count']),
      visitsCount: _profileInt(json['visits_count']),
      reviewsCount: _profileInt(json['reviews_count']),
    );
  }

  final int savedCount;
  final int visitsCount;
  final int reviewsCount;

  Map<String, dynamic> toJson() => {
    'saved_count': savedCount,
    'visits_count': visitsCount,
    'reviews_count': reviewsCount,
  };

  TenantProfileStatsContent copyWith({
    int? savedCount,
    int? visitsCount,
    int? reviewsCount,
  }) {
    return TenantProfileStatsContent(
      savedCount: savedCount ?? this.savedCount,
      visitsCount: visitsCount ?? this.visitsCount,
      reviewsCount: reviewsCount ?? this.reviewsCount,
    );
  }

  @override
  List<Object?> get props => [savedCount, visitsCount, reviewsCount];
}

class TenantProfileMenuItemsContent extends Equatable {
  const TenantProfileMenuItemsContent({
    required this.visitRequests,
    required this.contracts,
    required this.reviews,
    required this.verification,
  });

  const TenantProfileMenuItemsContent.initial()
    : visitRequests = const TenantProfileMenuItemContent.initial(),
      contracts = const TenantProfileMenuItemContent.initial(),
      reviews = const TenantProfileMenuItemContent.initial(),
      verification = const TenantProfileMenuItemContent.initial();

  factory TenantProfileMenuItemsContent.fromJson(Map<String, dynamic> json) {
    return TenantProfileMenuItemsContent(
      visitRequests: TenantProfileMenuItemContent.fromJson(
        _profileJsonMap(json['visit_requests']),
      ),
      contracts: TenantProfileMenuItemContent.fromJson(
        _profileJsonMap(json['contracts']),
      ),
      reviews: TenantProfileMenuItemContent.fromJson(
        _profileJsonMap(json['reviews']),
      ),
      verification: TenantProfileMenuItemContent.fromJson(
        _profileJsonMap(json['verification']),
      ),
    );
  }

  final TenantProfileMenuItemContent visitRequests;
  final TenantProfileMenuItemContent contracts;
  final TenantProfileMenuItemContent reviews;
  final TenantProfileMenuItemContent verification;

  Map<String, dynamic> toJson() => {
    'visit_requests': visitRequests.toJson(),
    'contracts': contracts.toJson(),
    'reviews': reviews.toJson(),
    'verification': verification.toJson(),
  };

  TenantProfileMenuItemsContent copyWith({
    TenantProfileMenuItemContent? visitRequests,
    TenantProfileMenuItemContent? contracts,
    TenantProfileMenuItemContent? reviews,
    TenantProfileMenuItemContent? verification,
  }) {
    return TenantProfileMenuItemsContent(
      visitRequests: visitRequests ?? this.visitRequests,
      contracts: contracts ?? this.contracts,
      reviews: reviews ?? this.reviews,
      verification: verification ?? this.verification,
    );
  }

  @override
  List<Object?> get props => [visitRequests, contracts, reviews, verification];
}

class TenantProfileMenuItemContent extends Equatable {
  const TenantProfileMenuItemContent({
    required this.title,
    required this.count,
    required this.subtitle,
    required this.isVerified,
  });

  const TenantProfileMenuItemContent.initial()
    : title = '',
      count = 0,
      subtitle = '',
      isVerified = false;

  factory TenantProfileMenuItemContent.fromJson(Map<String, dynamic> json) {
    return TenantProfileMenuItemContent(
      title: _profileString(json['title']),
      count: _profileInt(json['count']),
      subtitle: _profileString(json['subtitle']),
      isVerified: json['is_verified'] == true,
    );
  }

  final String title;
  final int count;
  final String subtitle;
  final bool isVerified;

  Map<String, dynamic> toJson() => {
    'title': title,
    'count': count,
    'subtitle': subtitle,
    'is_verified': isVerified,
  };

  TenantProfileMenuItemContent copyWith({
    String? title,
    int? count,
    String? subtitle,
    bool? isVerified,
  }) {
    return TenantProfileMenuItemContent(
      title: title ?? this.title,
      count: count ?? this.count,
      subtitle: subtitle ?? this.subtitle,
      isVerified: isVerified ?? this.isVerified,
    );
  }

  @override
  List<Object?> get props => [title, count, subtitle, isVerified];
}
