import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:url_launcher/url_launcher.dart';

import '../data/enums/app_notification_kind.dart';
import '../data/enums/notification_role.dart';
import '../data/models/app_notification_content.dart';
import '../data/notification_destination.dart';
import 'screens/notification_detail_screen.dart';
import 'screens/notifications_screen.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';

abstract final class NotificationNavigation {
  static Future<void> open({
    required AppNotificationContent notification,
    NotificationRole? role,
  }) async {
    if (notification.primaryActionType == 'dismiss') {
      Go.back();
      return;
    }
    final NotificationDestination target = NotificationDestination.resolve(
      notification,
    );
    await WorkspaceNavigation.open(
      workspace: target.workspace,
      tab: target.tab,
      detail: () => _openNotification(
        notification: notification,
        role: WorkspaceCubit.instance.state.isOwner
            ? NotificationRole.owner
            : NotificationRole.tenant,
      ),
    );
  }

  static Future<void> _openNotification({
    required AppNotificationContent notification,
    required NotificationRole role,
  }) async {
    final String actionType = notification.primaryActionType;
    final String targetId = notification.primaryTargetId;

    if (actionType == 'dismiss') {
      Go.back();
      return;
    }

    if (actionType == 'open_search_alert' && targetId.isNotEmpty) {
      await Go.to<void>(PremiumAlertDetailScreen(alertId: targetId));
      return;
    }

    if (notification.kind == AppNotificationKind.visitRequest &&
        targetId.isNotEmpty) {
      await Go.to<void>(OwnerRequestDetailsScreen(requestId: targetId));
      return;
    }

    if (notification.kind == AppNotificationKind.visitAccepted &&
        targetId.isNotEmpty) {
      await Go.to<void>(
        VisitDetailsScreen(
          visit: TenantVisitContent(
            id: targetId,
            rentalSelection: notification.payload.rentalSelection,
            propertyTitle: notification.detailLocation.isNotEmpty
                ? notification.detailLocation
                : notification.title,
            day: notification.payload.appointmentDate.isNotEmpty
                ? notification.payload.appointmentDate
                : notification.payload.visitDate.isNotEmpty
                ? notification.payload.visitDate
                : notification.detailDate,
            time: notification.payload.appointmentTime.isNotEmpty
                ? notification.payload.appointmentTime
                : notification.payload.visitTime,
            status: TenantVisitStatus.accepted,
            statusText: '',
          ),
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.newMessage ||
        actionType == 'open_chat') {
      final String chatId = notification.payload.chatId.isNotEmpty
          ? notification.payload.chatId
          : targetId;
      if (chatId.isEmpty) {
        await Go.to<void>(const NotificationsScreen());
        return;
      }
      await Go.to<void>(
        ChatScreen(
          rentalContext: notification.payload.rentalSelection,
          conversation: ConversationContent(
            id: chatId,
            name: notification.payload.senderName.isNotEmpty
                ? notification.payload.senderName
                : notification.title,
            property: notification.detailLocation,
            lastMessage: notification.description,
            time: notification.time,
            unreadCount: 1,
            // Notifications do not carry a verified-participant contract.
            isVerified: false,
            isOnline: false,
            otherParticipant: ChatParticipantContent(
              id: notification.payload.senderId,
              firstName: '',
              lastName: '',
              fullName: notification.payload.senderName,
              email: '',
              avatarUrl: '',
              isOnline: false,
            ),
          ),
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.visitReview) {
      final visitId = notification.payload.visitId;
      if (visitId.isEmpty) {
        await Go.to<void>(const TenantVisitsScreen());
        return;
      }
      await Go.to<void>(
        VisitDetailsScreen(
          visit: const TenantVisitContent.initial().copyWith(
            id: visitId,
            rentalSelection: notification.payload.rentalSelection,
            propertyTitle: notification.title,
          ),
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.propertyViews) {
      final property = OwnerPropertyContent.initial().copyWith(
        id: notification.payload.propertyId,
        title: notification.title,
        location: notification.detailLocation,
        views: notification.payload.viewsCount,
      );
      await Go.to<void>(OwnerPropertyAnalyticsScreen(property: property));
      return;
    }

    if (notification.kind == AppNotificationKind.dailyBump) {
      await Go.to<void>(const OwnerListingsScreen());
      return;
    }

    if (notification.kind == AppNotificationKind.propertyVerified) {
      await Go.to<void>(const OwnerPropertiesScreen());
      return;
    }

    if (notification.kind == AppNotificationKind.accountVerification) {
      await Go.to<void>(
        ProfileVerificationScreen(
          workspace: role.isOwner ? AppWorkspace.owner : AppWorkspace.tenant,
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.securityAlert) {
      await Go.to<void>(
        ProfileSettingsScreen(
          workspace: role.isOwner ? AppWorkspace.owner : AppWorkspace.tenant,
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.promotion &&
        notification.payload.promoUrl.isNotEmpty) {
      final Uri? uri = Uri.tryParse(notification.payload.promoUrl);
      if (uri != null && uri.scheme == 'https' && uri.host.isNotEmpty) {
        await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
      }
      return;
    }

    final String propertyId = notification.payload.propertyId.isNotEmpty
        ? notification.payload.propertyId
        : targetId;
    if (propertyId.isNotEmpty &&
        (notification.kind == AppNotificationKind.newProperty ||
            notification.kind == AppNotificationKind.propertyUpdate ||
            notification.kind == AppNotificationKind.visitRejected)) {
      await Go.to<void>(
        PropertyDetailsScreen(
          propertyId: propertyId,
          offerId: notification.payload.offerId.isEmpty
              ? null
              : notification.payload.offerId,
        ),
      );
      return;
    }

    if (notification.id.isNotEmpty) {
      await Go.to<void>(
        NotificationDetailScreen(role: role, notification: notification),
      );
    } else {
      await Go.to<void>(const NotificationsScreen());
    }
  }
}
