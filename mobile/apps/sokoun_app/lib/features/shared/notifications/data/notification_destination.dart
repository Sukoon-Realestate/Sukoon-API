import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';

import 'enums/app_notification_kind.dart';
import 'models/app_notification_content.dart';

class NotificationDestination {
  const NotificationDestination({this.workspace, this.tab});

  final AppWorkspace? workspace;
  final WorkspaceTab? tab;

  factory NotificationDestination.resolve(AppNotificationContent notification) {
    return switch (notification.kind) {
      AppNotificationKind.visitRequest => const NotificationDestination(
        workspace: AppWorkspace.owner,
        tab: WorkspaceTab.requests,
      ),
      AppNotificationKind.propertyVerified ||
      AppNotificationKind.propertyViews ||
      AppNotificationKind.dailyBump => const NotificationDestination(
        workspace: AppWorkspace.owner,
        tab: WorkspaceTab.properties,
      ),
      AppNotificationKind.visitAccepted ||
      AppNotificationKind.visitReview => const NotificationDestination(
        workspace: AppWorkspace.tenant,
        tab: WorkspaceTab.visits,
      ),
      AppNotificationKind.visitRejected ||
      AppNotificationKind.newProperty ||
      AppNotificationKind.propertyUpdate => const NotificationDestination(
        workspace: AppWorkspace.tenant,
        tab: WorkspaceTab.home,
      ),
      AppNotificationKind.newMessage => const NotificationDestination(
        tab: WorkspaceTab.messages,
      ),
      AppNotificationKind.accountVerification ||
      AppNotificationKind.securityAlert => const NotificationDestination(
        tab: WorkspaceTab.profile,
      ),
      _ =>
        notification.primaryActionType == 'open_chat'
            ? const NotificationDestination(tab: WorkspaceTab.messages)
            : const NotificationDestination(),
    };
  }
}
