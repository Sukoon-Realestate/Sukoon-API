enum AppNotificationKind {
  visitRequest('visit_request'),
  visitAccepted('visit_accepted'),
  visitRejected('visit_rejected'),
  visitReview('visit_review'),
  newMessage('new_message'),
  propertyVerified('property_verified'),
  propertyViews('property_views'),
  dailyBump('daily_bump'),
  newProperty('new_property'),
  propertyUpdate('property_update'),
  accountVerification('account_verification'),
  securityAlert('security_alert'),
  promotion('promotion'),
  unknown('unknown');

  const AppNotificationKind(this.apiValue);

  final String apiValue;

  static AppNotificationKind fromApiValue(Object? value) {
    final String normalized = value?.toString().trim().toLowerCase() ?? '';
    return switch (normalized) {
      'visit_request' => AppNotificationKind.visitRequest,
      'visit_accepted' => AppNotificationKind.visitAccepted,
      'visit_rejected' => AppNotificationKind.visitRejected,
      'visit_review' || 'rate_visit' => AppNotificationKind.visitReview,
      'new_message' ||
      'owner_message' ||
      'tenant_message' => AppNotificationKind.newMessage,
      'property_verified' => AppNotificationKind.propertyVerified,
      'property_views' => AppNotificationKind.propertyViews,
      'daily_bump' || 'daily_visibility' => AppNotificationKind.dailyBump,
      'new_property' => AppNotificationKind.newProperty,
      'property_update' => AppNotificationKind.propertyUpdate,
      'account_verification' => AppNotificationKind.accountVerification,
      'security_alert' => AppNotificationKind.securityAlert,
      'promotion' => AppNotificationKind.promotion,
      _ => AppNotificationKind.unknown,
    };
  }
}
