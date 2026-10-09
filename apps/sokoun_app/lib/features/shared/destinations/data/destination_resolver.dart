import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import '../../notifications/data/enums/app_notification_kind.dart';
import '../../notifications/data/models/app_notification_content.dart';
import 'models/app_destination.dart';

abstract final class DestinationResolver {
  static const Set<String> propertyHosts = {'sokoun.app', 'www.sokoun.app'};
  static bool validId(String value) =>
      RegExp(r'^[a-zA-Z0-9_-]{1,128}$').hasMatch(value) &&
      !const {'0', 'null', 'undefined'}.contains(value.toLowerCase());
  static AppDestination? propertyLink(Uri uri) {
    if (uri.hasScheme &&
        (uri.scheme != 'https' ||
            !propertyHosts.contains(uri.host.toLowerCase()) ||
            uri.userInfo.isNotEmpty ||
            (uri.hasPort && uri.port != 443))) {
      return null;
    }
    if (!uri.hasScheme && uri.hasAuthority) return null;
    final List<String> parts = uri.pathSegments;
    if ((parts.length != 2 && parts.length != 4) ||
        parts.first != 'properties' ||
        !validId(parts[1])) {
      return null;
    }
    if (parts.length == 4 && (parts[2] != 'offers' || !validId(parts[3]))) {
      return null;
    }
    final List<String> offers = uri.queryParametersAll['offer_id'] ?? const [];
    if (offers.length > 1 || (offers.isNotEmpty && !validId(offers.single))) {
      return null;
    }
    if (parts.length == 4 && offers.isNotEmpty && parts[3] != offers.single) {
      return null;
    }
    return AppDestination(
      kind: DestinationKind.property,
      id: parts[1],
      offerId: parts.length == 4 ? parts[3] : offers.firstOrNull,
      workspace: AppWorkspace.tenant,
      tab: WorkspaceTab.home,
    );
  }

  static AppDestination notification(AppNotificationContent notification) {
    final payload = notification.payload;
    final String action = notification.primaryActionType;
    final String target = notification.primaryTargetId;
    if (action == 'open_search_alert') {
      return validId(target)
          ? AppDestination(
              kind: DestinationKind.searchAlert,
              id: target,
              workspace: AppWorkspace.tenant,
              tab: WorkspaceTab.home,
            )
          : const AppDestination(kind: DestinationKind.notifications);
    }
    if (action == 'open_tenancy_invitation') {
      final workspace =
          payload.workspace == 'owner' ||
              notification.kind == AppNotificationKind.tenancyInvitationResponse
          ? AppWorkspace.owner
          : AppWorkspace.tenant;
      return AppDestination(
        kind: validId(target)
            ? DestinationKind.tenancyInvitation
            : DestinationKind.tenancyInvitations,
        id: validId(target) ? target : '',
        workspace: workspace,
        tab: WorkspaceTab.profile,
      );
    }
    if (notification.kind == AppNotificationKind.newMessage ||
        action == 'open_chat') {
      final String id = payload.chatId.isNotEmpty ? payload.chatId : target;
      return validId(id)
          ? AppDestination(
              kind: DestinationKind.chat,
              id: id,
              tab: WorkspaceTab.messages,
            )
          : const AppDestination(
              kind: DestinationKind.notifications,
              tab: WorkspaceTab.messages,
            );
    }
    if (notification.kind == AppNotificationKind.visitRequest) {
      return validId(target)
          ? AppDestination(
              kind: DestinationKind.ownerRequest,
              id: target,
              workspace: AppWorkspace.owner,
              tab: WorkspaceTab.requests,
            )
          : const AppDestination(
              kind: DestinationKind.notifications,
              workspace: AppWorkspace.owner,
              tab: WorkspaceTab.requests,
            );
    }
    if (notification.kind == AppNotificationKind.visitReview ||
        notification.kind == AppNotificationKind.visitAccepted ||
        notification.kind == AppNotificationKind.visitRejected) {
      // Review/rejection IDs must come from a typed visit field, never a property fallback.
      final String id = payload.visitId.isNotEmpty
          ? payload.visitId
          : notification.kind == AppNotificationKind.visitAccepted
          ? target
          : '';
      if (validId(id)) {
        return AppDestination(
          kind: DestinationKind.tenantVisit,
          id: id,
          workspace: AppWorkspace.tenant,
          tab: WorkspaceTab.visits,
          openReview: notification.kind == AppNotificationKind.visitReview,
        );
      }
      if (notification.kind != AppNotificationKind.visitRejected ||
          !validId(payload.propertyId)) {
        return const AppDestination(
          kind: DestinationKind.tenantVisits,
          workspace: AppWorkspace.tenant,
          tab: WorkspaceTab.visits,
        );
      }
    }
    if (notification.kind == AppNotificationKind.propertyViews) {
      return validId(payload.propertyId)
          ? AppDestination(
              kind: DestinationKind.propertyAnalytics,
              id: payload.propertyId,
              workspace: AppWorkspace.owner,
              tab: WorkspaceTab.properties,
            )
          : const AppDestination(
              kind: DestinationKind.ownerProperties,
              workspace: AppWorkspace.owner,
              tab: WorkspaceTab.properties,
            );
    }
    if (notification.kind == AppNotificationKind.dailyBump) {
      return const AppDestination(
        kind: DestinationKind.ownerListings,
        workspace: AppWorkspace.owner,
        tab: WorkspaceTab.properties,
      );
    }
    if (notification.kind == AppNotificationKind.propertyVerified) {
      return const AppDestination(
        kind: DestinationKind.ownerProperties,
        workspace: AppWorkspace.owner,
        tab: WorkspaceTab.properties,
      );
    }
    if (notification.kind == AppNotificationKind.accountVerification) {
      return const AppDestination(
        kind: DestinationKind.profileVerification,
        tab: WorkspaceTab.profile,
      );
    }
    if (notification.kind == AppNotificationKind.securityAlert) {
      return const AppDestination(
        kind: DestinationKind.profileSettings,
        tab: WorkspaceTab.profile,
      );
    }
    if (notification.kind == AppNotificationKind.promotion) {
      final Uri? uri = Uri.tryParse(payload.promoUrl);
      if (uri != null &&
          uri.scheme == 'https' &&
          uri.host.isNotEmpty &&
          uri.userInfo.isEmpty) {
        return AppDestination(
          kind: DestinationKind.externalPromotion,
          url: uri,
        );
      }
    }
    if (notification.kind == AppNotificationKind.newProperty ||
        notification.kind == AppNotificationKind.propertyUpdate ||
        notification.kind == AppNotificationKind.visitRejected) {
      final String id = payload.propertyId.isNotEmpty
          ? payload.propertyId
          : notification.kind == AppNotificationKind.visitRejected
          ? ''
          : target;
      if (validId(id) &&
          (payload.offerId.isEmpty || validId(payload.offerId))) {
        return AppDestination(
          kind: DestinationKind.property,
          id: id,
          offerId: payload.offerId.isEmpty ? null : payload.offerId,
          workspace: AppWorkspace.tenant,
          tab: WorkspaceTab.home,
        );
      }
    }
    return AppDestination(
      kind: validId(notification.id)
          ? DestinationKind.notificationDetail
          : DestinationKind.notifications,
      id: validId(notification.id) ? notification.id : '',
    );
  }
}
