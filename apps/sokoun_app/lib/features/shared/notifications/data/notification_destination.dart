import '../../destinations/data/destination_resolver.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';

import 'models/app_notification_content.dart';

class NotificationDestination {
  const NotificationDestination({this.workspace, this.tab});

  final AppWorkspace? workspace;
  final WorkspaceTab? tab;

  factory NotificationDestination.resolve(AppNotificationContent notification) {
    final target = DestinationResolver.notification(notification);
    return NotificationDestination(
      workspace: target.workspace,
      tab: target.tab,
    );
  }
}
