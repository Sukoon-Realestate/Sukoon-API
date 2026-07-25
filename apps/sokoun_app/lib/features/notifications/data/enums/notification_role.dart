enum NotificationRole { tenant, owner }

extension NotificationRoleX on NotificationRole {
  bool get isTenant => this == NotificationRole.tenant;
  bool get isOwner => this == NotificationRole.owner;
}
