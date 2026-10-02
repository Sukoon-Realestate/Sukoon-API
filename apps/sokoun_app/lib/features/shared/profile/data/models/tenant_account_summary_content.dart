import 'package:equatable/equatable.dart';
import '../profile_json.dart';

class TenantAccountSummaryContent extends Equatable {
  const TenantAccountSummaryContent({
    required this.user,
    required this.identityVerification,
    required this.stats,
    required this.shortcuts,
  });

  const TenantAccountSummaryContent.initial()
    : user = const TenantAccountSummaryUserContent.initial(),
      identityVerification = const TenantIdentityVerificationContent.initial(),
      stats = const TenantAccountSummaryStatsContent.initial(),
      shortcuts = const TenantAccountSummaryShortcutsContent.initial();

  factory TenantAccountSummaryContent.fromJson(Map<String, dynamic> json) {
    return TenantAccountSummaryContent(
      user: TenantAccountSummaryUserContent.fromJson(
        profileJsonMap(json['user']),
      ),
      identityVerification: TenantIdentityVerificationContent.fromJson(
        profileJsonMap(json['identity_verification']),
      ),
      stats: TenantAccountSummaryStatsContent.fromJson(
        profileJsonMap(json['stats']),
      ),
      shortcuts: TenantAccountSummaryShortcutsContent.fromJson(
        profileJsonMap(json['shortcuts']),
      ),
    );
  }

  static const String cacheKey = 'tenant_account_summary';

  final TenantAccountSummaryUserContent user;
  final TenantIdentityVerificationContent identityVerification;
  final TenantAccountSummaryStatsContent stats;
  final TenantAccountSummaryShortcutsContent shortcuts;

  Map<String, dynamic> toJson() => {
    'user': user.toJson(),
    'identity_verification': identityVerification.toJson(),
    'stats': stats.toJson(),
    'shortcuts': shortcuts.toJson(),
  };

  TenantAccountSummaryContent copyWith({
    TenantAccountSummaryUserContent? user,
    TenantIdentityVerificationContent? identityVerification,
    TenantAccountSummaryStatsContent? stats,
    TenantAccountSummaryShortcutsContent? shortcuts,
  }) {
    return TenantAccountSummaryContent(
      user: user ?? this.user,
      identityVerification: identityVerification ?? this.identityVerification,
      stats: stats ?? this.stats,
      shortcuts: shortcuts ?? this.shortcuts,
    );
  }

  @override
  List<Object?> get props => [user, identityVerification, stats, shortcuts];
}

class TenantAccountSummaryUserContent extends Equatable {
  const TenantAccountSummaryUserContent({
    required this.id,
    required this.fullName,
    required this.avatar,
    required this.initial,
    required this.roleLabel,
    required this.memberSinceLabel,
    required this.profileCompletionPercentage,
    required this.profileCompletionLabel,
  });

  const TenantAccountSummaryUserContent.initial()
    : id = '',
      fullName = '',
      avatar = null,
      initial = '',
      roleLabel = '',
      memberSinceLabel = '',
      profileCompletionPercentage = 0,
      profileCompletionLabel = '';

  factory TenantAccountSummaryUserContent.fromJson(Map<String, dynamic> json) {
    return TenantAccountSummaryUserContent(
      id: profileString(json['id']),
      fullName: profileString(json['full_name'] ?? json['name']),
      avatar: profileNullableString(json['avatar']),
      initial: profileString(json['initial']),
      roleLabel: profileString(json['role_label']),
      memberSinceLabel: profileString(json['member_since_label']),
      profileCompletionPercentage: profileInt(
        json['profile_completion_percentage'],
      ),
      profileCompletionLabel: profileString(json['profile_completion_label']),
    );
  }

  final String id;
  final String fullName;
  final String? avatar;
  final String initial;
  final String roleLabel;
  final String memberSinceLabel;
  final int profileCompletionPercentage;
  final String profileCompletionLabel;

  Map<String, dynamic> toJson() => {
    'id': id,
    'full_name': fullName,
    'avatar': avatar,
    'initial': initial,
    'role_label': roleLabel,
    'member_since_label': memberSinceLabel,
    'profile_completion_percentage': profileCompletionPercentage,
    'profile_completion_label': profileCompletionLabel,
  };

  TenantAccountSummaryUserContent copyWith({
    String? id,
    String? fullName,
    String? avatar,
    bool clearAvatar = false,
    String? initial,
    String? roleLabel,
    String? memberSinceLabel,
    int? profileCompletionPercentage,
    String? profileCompletionLabel,
  }) {
    return TenantAccountSummaryUserContent(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      avatar: clearAvatar ? null : avatar ?? this.avatar,
      initial: initial ?? this.initial,
      roleLabel: roleLabel ?? this.roleLabel,
      memberSinceLabel: memberSinceLabel ?? this.memberSinceLabel,
      profileCompletionPercentage:
          profileCompletionPercentage ?? this.profileCompletionPercentage,
      profileCompletionLabel:
          profileCompletionLabel ?? this.profileCompletionLabel,
    );
  }

  @override
  List<Object?> get props => [
    id,
    fullName,
    avatar,
    initial,
    roleLabel,
    memberSinceLabel,
    profileCompletionPercentage,
    profileCompletionLabel,
  ];
}

class TenantIdentityVerificationContent extends Equatable {
  const TenantIdentityVerificationContent({
    required this.isVerified,
    required this.title,
    required this.subtitle,
    required this.statusLabel,
  });

  const TenantIdentityVerificationContent.initial()
    : isVerified = false,
      title = '',
      subtitle = '',
      statusLabel = '';

  factory TenantIdentityVerificationContent.fromJson(
    Map<String, dynamic> json,
  ) {
    return TenantIdentityVerificationContent(
      isVerified: json['is_verified'] == true,
      title: profileString(json['title']),
      subtitle: profileString(json['subtitle']),
      statusLabel: profileString(json['status_label']),
    );
  }

  final bool isVerified;
  final String title;
  final String subtitle;
  final String statusLabel;

  Map<String, dynamic> toJson() => {
    'is_verified': isVerified,
    'title': title,
    'subtitle': subtitle,
    'status_label': statusLabel,
  };

  TenantIdentityVerificationContent copyWith({
    bool? isVerified,
    String? title,
    String? subtitle,
    String? statusLabel,
  }) {
    return TenantIdentityVerificationContent(
      isVerified: isVerified ?? this.isVerified,
      title: title ?? this.title,
      subtitle: subtitle ?? this.subtitle,
      statusLabel: statusLabel ?? this.statusLabel,
    );
  }

  @override
  List<Object?> get props => [isVerified, title, subtitle, statusLabel];
}

class TenantAccountSummaryStatsContent extends Equatable {
  const TenantAccountSummaryStatsContent({
    required this.savedPropertiesCount,
    required this.completedVisitsCount,
    required this.activeChatsCount,
  });

  const TenantAccountSummaryStatsContent.initial()
    : savedPropertiesCount = 0,
      completedVisitsCount = 0,
      activeChatsCount = 0;

  factory TenantAccountSummaryStatsContent.fromJson(Map<String, dynamic> json) {
    return TenantAccountSummaryStatsContent(
      savedPropertiesCount: profileInt(json['saved_properties_count']),
      completedVisitsCount: profileInt(json['completed_visits_count']),
      activeChatsCount: profileInt(json['active_chats_count']),
    );
  }

  final int savedPropertiesCount;
  final int completedVisitsCount;
  final int activeChatsCount;

  Map<String, dynamic> toJson() => {
    'saved_properties_count': savedPropertiesCount,
    'completed_visits_count': completedVisitsCount,
    'active_chats_count': activeChatsCount,
  };

  TenantAccountSummaryStatsContent copyWith({
    int? savedPropertiesCount,
    int? completedVisitsCount,
    int? activeChatsCount,
  }) {
    return TenantAccountSummaryStatsContent(
      savedPropertiesCount: savedPropertiesCount ?? this.savedPropertiesCount,
      completedVisitsCount: completedVisitsCount ?? this.completedVisitsCount,
      activeChatsCount: activeChatsCount ?? this.activeChatsCount,
    );
  }

  @override
  List<Object?> get props => [
    savedPropertiesCount,
    completedVisitsCount,
    activeChatsCount,
  ];
}

class TenantAccountSummaryShortcutsContent extends Equatable {
  const TenantAccountSummaryShortcutsContent({
    required this.savedProperties,
    required this.visitsHistory,
    required this.identityVerification,
  });

  const TenantAccountSummaryShortcutsContent.initial()
    : savedProperties = const TenantAccountSummaryShortcutContent.initial(),
      visitsHistory = const TenantAccountSummaryShortcutContent.initial(),
      identityVerification =
          const TenantAccountSummaryShortcutContent.initial();

  factory TenantAccountSummaryShortcutsContent.fromJson(
    Map<String, dynamic> json,
  ) {
    return TenantAccountSummaryShortcutsContent(
      savedProperties: TenantAccountSummaryShortcutContent.fromJson(
        profileJsonMap(json['saved_properties']),
      ),
      visitsHistory: TenantAccountSummaryShortcutContent.fromJson(
        profileJsonMap(json['visits_history']),
      ),
      identityVerification: TenantAccountSummaryShortcutContent.fromJson(
        profileJsonMap(json['identity_verification']),
      ),
    );
  }

  final TenantAccountSummaryShortcutContent savedProperties;
  final TenantAccountSummaryShortcutContent visitsHistory;
  final TenantAccountSummaryShortcutContent identityVerification;

  Map<String, dynamic> toJson() => {
    'saved_properties': savedProperties.toJson(),
    'visits_history': visitsHistory.toJson(),
    'identity_verification': identityVerification.toJson(),
  };

  TenantAccountSummaryShortcutsContent copyWith({
    TenantAccountSummaryShortcutContent? savedProperties,
    TenantAccountSummaryShortcutContent? visitsHistory,
    TenantAccountSummaryShortcutContent? identityVerification,
  }) {
    return TenantAccountSummaryShortcutsContent(
      savedProperties: savedProperties ?? this.savedProperties,
      visitsHistory: visitsHistory ?? this.visitsHistory,
      identityVerification: identityVerification ?? this.identityVerification,
    );
  }

  @override
  List<Object?> get props => [
    savedProperties,
    visitsHistory,
    identityVerification,
  ];
}

class TenantAccountSummaryShortcutContent extends Equatable {
  const TenantAccountSummaryShortcutContent({
    required this.title,
    required this.count,
    required this.status,
    required this.label,
  });

  const TenantAccountSummaryShortcutContent.initial()
    : title = '',
      count = 0,
      status = '',
      label = '';

  factory TenantAccountSummaryShortcutContent.fromJson(
    Map<String, dynamic> json,
  ) {
    return TenantAccountSummaryShortcutContent(
      title: profileString(json['title']),
      count: profileInt(json['count']),
      status: profileString(json['status']),
      label: profileString(json['label']),
    );
  }

  final String title;
  final int count;
  final String status;
  final String label;

  Map<String, dynamic> toJson() => {
    'title': title,
    'count': count,
    'status': status,
    'label': label,
  };

  TenantAccountSummaryShortcutContent copyWith({
    String? title,
    int? count,
    String? status,
    String? label,
  }) {
    return TenantAccountSummaryShortcutContent(
      title: title ?? this.title,
      count: count ?? this.count,
      status: status ?? this.status,
      label: label ?? this.label,
    );
  }

  @override
  List<Object?> get props => [title, count, status, label];
}
