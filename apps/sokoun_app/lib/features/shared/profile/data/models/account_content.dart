import 'package:equatable/equatable.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import '../profile_json.dart';
import 'profile_account_details_content.dart';

class AccountContent extends Equatable {
  const AccountContent({
    required this.user,
    required this.stats,
    required this.menuItems,
    required this.accountDetails,
  });

  const AccountContent.initial()
    : user = const AccountUserContent.initial(),
      stats = const AccountStatsContent.initial(),
      menuItems = const AccountMenuItemsContent.initial(),
      accountDetails = const ProfileAccountDetailsContent.initial();

  factory AccountContent.fromJson(Map<String, dynamic> json) {
    final UserModel identity = UserModel.fromJson(json);
    return AccountContent(
      user: AccountUserContent.fromJson({
        ...profileJsonMap(json['user'] ?? json),
        'is_verified': identity.isVerified,
      }),
      stats: AccountStatsContent.fromJson(profileJsonMap(json['stats'])),
      menuItems: AccountMenuItemsContent.fromJson(
        profileJsonMap(json['menu_items']),
      ),
      accountDetails: ProfileAccountDetailsContent.fromJson({
        'name': identity.name,
        'email': identity.email,
        'phone_number': identity.phone,
        ...profileJsonMap(json['account_details']),
      }),
    );
  }

  static const String cacheKey = 'tenant_profile';

  final AccountUserContent user;
  final AccountStatsContent stats;
  final AccountMenuItemsContent menuItems;
  final ProfileAccountDetailsContent accountDetails;

  UserModel get identity => UserModel.fromJson(toJson());

  Map<String, dynamic> toJson() => {
    'user': user.toJson(),
    'stats': stats.toJson(),
    'menu_items': menuItems.toJson(),
    'account_details': accountDetails.toJson(),
  };

  AccountContent copyWith({
    AccountUserContent? user,
    AccountStatsContent? stats,
    AccountMenuItemsContent? menuItems,
    ProfileAccountDetailsContent? accountDetails,
  }) {
    return AccountContent(
      user: user ?? this.user,
      stats: stats ?? this.stats,
      menuItems: menuItems ?? this.menuItems,
      accountDetails: accountDetails ?? this.accountDetails,
    );
  }

  @override
  List<Object?> get props => [user, stats, menuItems, accountDetails];
}

class AccountUserContent extends Equatable {
  const AccountUserContent({
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

  const AccountUserContent.initial()
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

  factory AccountUserContent.fromJson(Map<String, dynamic> json) {
    return AccountUserContent(
      id: profileString(json['id']),
      fullName: profileString(json['full_name'] ?? json['name']),
      firstName: profileString(json['first_name']),
      lastName: profileString(json['last_name']),
      avatar: profileNullableString(json['avatar']),
      isVerified: json['is_verified'] ?? false,
      verificationBadge: profileString(json['verification_badge']),
      roleLabel: profileString(json['role_label']),
      memberSinceLabel: profileString(json['member_since_label']),
      memberSinceYear: profileInt(json['member_since_year']),
      memberSinceMonth: profileString(json['member_since_month']),
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

  AccountUserContent copyWith({
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
    return AccountUserContent(
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

class AccountStatsContent extends Equatable {
  const AccountStatsContent({
    required this.savedCount,
    required this.visitsCount,
    required this.reviewsCount,
  });

  const AccountStatsContent.initial()
    : savedCount = 0,
      visitsCount = 0,
      reviewsCount = 0;

  factory AccountStatsContent.fromJson(Map<String, dynamic> json) {
    return AccountStatsContent(
      savedCount: profileInt(json['saved_count']),
      visitsCount: profileInt(json['visits_count']),
      reviewsCount: profileInt(json['reviews_count']),
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

  AccountStatsContent copyWith({
    int? savedCount,
    int? visitsCount,
    int? reviewsCount,
  }) {
    return AccountStatsContent(
      savedCount: savedCount ?? this.savedCount,
      visitsCount: visitsCount ?? this.visitsCount,
      reviewsCount: reviewsCount ?? this.reviewsCount,
    );
  }

  @override
  List<Object?> get props => [savedCount, visitsCount, reviewsCount];
}

class AccountMenuItemsContent extends Equatable {
  const AccountMenuItemsContent({
    required this.visitRequests,
    required this.contracts,
    required this.reviews,
    required this.verification,
  });

  const AccountMenuItemsContent.initial()
    : visitRequests = const AccountMenuItemContent.initial(),
      contracts = const AccountMenuItemContent.initial(),
      reviews = const AccountMenuItemContent.initial(),
      verification = const AccountMenuItemContent.initial();

  factory AccountMenuItemsContent.fromJson(Map<String, dynamic> json) {
    return AccountMenuItemsContent(
      visitRequests: AccountMenuItemContent.fromJson(
        profileJsonMap(json['visit_requests']),
      ),
      contracts: AccountMenuItemContent.fromJson(
        profileJsonMap(json['contracts']),
      ),
      reviews: AccountMenuItemContent.fromJson(profileJsonMap(json['reviews'])),
      verification: AccountMenuItemContent.fromJson(
        profileJsonMap(json['verification']),
      ),
    );
  }

  final AccountMenuItemContent visitRequests;
  final AccountMenuItemContent contracts;
  final AccountMenuItemContent reviews;
  final AccountMenuItemContent verification;

  Map<String, dynamic> toJson() => {
    'visit_requests': visitRequests.toJson(),
    'contracts': contracts.toJson(),
    'reviews': reviews.toJson(),
    'verification': verification.toJson(),
  };

  AccountMenuItemsContent copyWith({
    AccountMenuItemContent? visitRequests,
    AccountMenuItemContent? contracts,
    AccountMenuItemContent? reviews,
    AccountMenuItemContent? verification,
  }) {
    return AccountMenuItemsContent(
      visitRequests: visitRequests ?? this.visitRequests,
      contracts: contracts ?? this.contracts,
      reviews: reviews ?? this.reviews,
      verification: verification ?? this.verification,
    );
  }

  @override
  List<Object?> get props => [visitRequests, contracts, reviews, verification];
}

class AccountMenuItemContent extends Equatable {
  const AccountMenuItemContent({
    required this.title,
    required this.count,
    required this.subtitle,
    required this.isVerified,
  });

  const AccountMenuItemContent.initial()
    : title = '',
      count = 0,
      subtitle = '',
      isVerified = false;

  factory AccountMenuItemContent.fromJson(Map<String, dynamic> json) {
    return AccountMenuItemContent(
      title: profileString(json['title']),
      count: profileInt(json['count']),
      subtitle: profileString(json['subtitle']),
      isVerified: json['is_verified'] ?? false,
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

  AccountMenuItemContent copyWith({
    String? title,
    int? count,
    String? subtitle,
    bool? isVerified,
  }) {
    return AccountMenuItemContent(
      title: title ?? this.title,
      count: count ?? this.count,
      subtitle: subtitle ?? this.subtitle,
      isVerified: isVerified ?? this.isVerified,
    );
  }

  @override
  List<Object?> get props => [title, count, subtitle, isVerified];
}
