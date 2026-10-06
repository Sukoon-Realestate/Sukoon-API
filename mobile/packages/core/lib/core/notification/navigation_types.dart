part of 'notification_service.dart';

/// The notification kinds supported by the mobile notification contract.
enum NotificationType {
  visitRequest(
    'visit_request',
    navigation: VisitNavigation(),
    category: 'حجز زيارة',
    iconType: NotificationIconType.calendar,
    actionType: NotificationActionType.viewVisit,
  ),
  visitAccepted(
    'visit_accepted',
    navigation: VisitNavigation(),
    category: 'حجز زيارة',
    iconType: NotificationIconType.checkCircle,
    actionType: NotificationActionType.viewVisit,
  ),
  visitRejected(
    'visit_rejected',
    navigation: PropertyNavigation(),
    category: 'حجز زيارة',
    iconType: NotificationIconType.cancel,
    actionType: NotificationActionType.viewProperty,
  ),
  visitReview(
    'visit_review',
    navigation: VisitReviewNavigation(),
    category: 'تقييم الزيارة',
    iconType: NotificationIconType.star,
    actionType: NotificationActionType.reviewVisit,
  ),
  newMessage(
    'new_message',
    navigation: ChatNavigation(),
    category: 'الرسائل',
    iconType: NotificationIconType.chat,
    actionType: NotificationActionType.openChat,
  ),
  propertyVerified(
    'property_verified',
    navigation: OwnerPropertyNavigation(),
    category: 'توثيق العقار',
    iconType: NotificationIconType.verified,
    actionType: NotificationActionType.viewProperty,
  ),
  propertyViews(
    'property_views',
    navigation: PropertyStatsNavigation(),
    category: 'أداء العقار',
    iconType: NotificationIconType.eye,
    actionType: NotificationActionType.viewPropertyStats,
  ),
  dailyBump(
    'daily_bump',
    navigation: MyPropertiesNavigation(),
    category: 'تحديث العقارات',
    iconType: NotificationIconType.warning,
    actionType: NotificationActionType.bumpProperties,
  ),
  newProperty(
    'new_property',
    navigation: PropertyNavigation(),
    category: 'العقارات',
    iconType: NotificationIconType.bell,
    actionType: NotificationActionType.viewProperty,
  ),
  propertyUpdate(
    'property_update',
    navigation: PropertyNavigation(),
    category: 'العقارات',
    iconType: NotificationIconType.refresh,
    actionType: NotificationActionType.viewProperty,
  ),
  accountVerification(
    'account_verification',
    navigation: AccountVerificationNavigation(),
    category: 'الحساب',
    iconType: NotificationIconType.warning,
    actionType: NotificationActionType.verifyAccount,
  ),
  securityAlert(
    'security_alert',
    navigation: SecurityNavigation(),
    category: 'الأمان',
    iconType: NotificationIconType.shield,
    actionType: NotificationActionType.reviewSecurity,
  ),
  promotion(
    'promotion',
    navigation: PromotionNavigation(),
    category: 'العروض',
    iconType: NotificationIconType.star,
    actionType: NotificationActionType.openPromotion,
  ),
  general(
    'general',
    navigation: NotificationsNavigation(),
    category: 'عام',
    iconType: NotificationIconType.bell,
    actionType: NotificationActionType.openGeneral,
  ),
  unknown(
    'unknown',
    navigation: NoNavigation(),
    category: '',
    iconType: NotificationIconType.unknown,
    actionType: NotificationActionType.unknown,
  );

  const NotificationType(
    this.type, {
    required this.navigation,
    required this.category,
    required this.iconType,
    required this.actionType,
  });

  /// The value used in the `notification_type` payload field.
  final String type;
  final NotificationNavigation navigation;
  final String category;
  final NotificationIconType iconType;
  final NotificationActionType actionType;

  /// Backwards-compatible alias for [type].
  String get id => type;

  static NotificationType fromValue(Object? value) {
    final String normalized = _normalizeNotificationValue(value);
    return switch (normalized) {
      'visit_request' => NotificationType.visitRequest,
      'visit_accepted' => NotificationType.visitAccepted,
      'visit_rejected' => NotificationType.visitRejected,
      'visit_review' => NotificationType.visitReview,
      'new_message' => NotificationType.newMessage,
      'property_verified' => NotificationType.propertyVerified,
      'property_views' => NotificationType.propertyViews,
      'daily_bump' => NotificationType.dailyBump,
      'new_property' => NotificationType.newProperty,
      'property_update' => NotificationType.propertyUpdate,
      'account_verification' => NotificationType.accountVerification,
      'security_alert' => NotificationType.securityAlert,
      'promotion' => NotificationType.promotion,
      'general' => NotificationType.general,
      _ => NotificationType.unknown,
    };
  }
}

enum NotificationActionType {
  viewVisit('view_visit'),
  viewProperty('view_property'),
  reviewVisit('review_visit'),
  openChat('open_chat'),
  viewPropertyStats('view_property_stats'),
  bumpProperties('bump_properties'),
  verifyAccount('verify_account'),
  reviewSecurity('review_security'),
  openPromotion('open_promotion'),
  openGeneral('open_general'),
  unknown('unknown');

  const NotificationActionType(this.id);

  /// The value used in the `action_type` payload field.
  final String id;

  static NotificationActionType fromValue(Object? value) {
    final String normalized = _normalizeNotificationValue(value);
    return NotificationActionType.values.firstWhere(
      (NotificationActionType action) => action.id == normalized,
      orElse: () => NotificationActionType.unknown,
    );
  }
}

enum NotificationIconType {
  calendar('calendar'),
  checkCircle('check_circle'),
  cancel('cancel'),
  star('star'),
  chat('chat'),
  verified('verified'),
  eye('eye'),
  warning('warning'),
  bell('bell'),
  refresh('refresh'),
  shield('shield'),
  unknown('unknown');

  const NotificationIconType(this.id);

  /// The value used in the `icon_type` payload field.
  final String id;

  static NotificationIconType fromValue(Object? value) {
    final String normalized = _normalizeNotificationValue(value);
    return NotificationIconType.values.firstWhere(
      (NotificationIconType icon) => icon.id == normalized,
      orElse: () => NotificationIconType.unknown,
    );
  }
}

String _normalizeNotificationValue(Object? value) =>
    value?.toString().trim().toLowerCase() ?? '';
