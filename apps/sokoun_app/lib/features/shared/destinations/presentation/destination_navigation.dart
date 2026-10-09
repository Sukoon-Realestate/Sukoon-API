import 'dart:async';
import 'package:flutter/widgets.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_listings_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/property_details_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitations_screen.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../notifications/data/enums/notification_role.dart';
import '../../notifications/data/models/app_notification_content.dart';
import '../../notifications/presentation/screens/notification_detail_screen.dart';
import '../../notifications/presentation/screens/notifications_screen.dart';
import '../data/models/app_destination.dart';
import 'visible_destination_registry.dart';

abstract final class DestinationNavigation {
  static bool _ready = false;
  static ({
    AppDestination target,
    AppNotificationContent? notification,
    String? account,
  })?
  _pending;
  static String? _dispatching;
  static final Map<String, DateTime> _deliveries = {};
  static bool _registered = false;
  static void initialize() {
    if (_registered) return;
    _registered = true;
    AccountSession.registerCleanup((_) async {
      clearSession();
    });
  }

  static void clearSession() {
    _pending = null;
    _deliveries.clear();
    _dispatching = null;
    WorkspaceNavigation.clearPending();
  }

  static void reset() {
    _ready = false;
    clearSession();
  }

  static void ready() {
    initialize();
    _ready = true;
    final pending = _pending;
    _pending = null;
    if (pending != null &&
        (pending.account == null || pending.account == AccountSession.userId)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        unawaited(open(pending.target, notification: pending.notification));
      });
    }
  }

  static Future<void> open(
    AppDestination target, {
    AppNotificationContent? notification,
  }) async {
    initialize();
    if (!_ready) {
      _pending = (
        target: target,
        notification: notification,
        account: AccountSession.userId,
      );
      return;
    }
    final String identity = target.identity;
    if (_alreadyOpen(target) || _dispatching == identity) return;
    final DateTime now = DateTime.now();
    _deliveries.removeWhere(
      (_, time) => now.difference(time) > const Duration(seconds: 2),
    );
    final String delivery = '${notification?.id ?? ''}|$identity';
    if (_deliveries.containsKey(delivery)) return;
    if (_deliveries.length >= 100) _deliveries.clear();
    _deliveries[delivery] = now;
    _dispatching = identity;
    final String? account = AccountSession.userId;
    void detail() {
      if (account != null && account != AccountSession.userId) return;
      unawaited(_show(target, notification));
    }

    try {
      if (!target.requiresAccount && !WorkspaceNavigation.isAuthenticated) {
        detail();
      } else {
        await WorkspaceNavigation.open(
          workspace: target.workspace,
          tab: target.tab,
          detail: detail,
        );
      }
    } finally {
      if (_dispatching == identity) _dispatching = null;
    }
  }

  static bool _alreadyOpen(AppDestination target) {
    final Widget? page = AppNavigationObserver.currentPage;
    final visible = VisibleDestinationRegistry.read(
      AppNavigationObserver.currentPageRoute,
    );
    return switch (target.kind) {
      DestinationKind.property =>
        page is PropertyDetailsScreen &&
            page.propertyId == target.id &&
            (target.offerId == null ||
                (visible == null ? page.offerId : visible.offerId) ==
                    target.offerId),
      DestinationKind.tenantVisit =>
        page is VisitDetailsScreen &&
            page.visit.id == target.id &&
            (!target.openReview || page.openReview),
      DestinationKind.tenantVisits => page is TenantVisitsScreen,
      DestinationKind.ownerRequest =>
        page is OwnerRequestDetailsScreen && page.requestId == target.id,
      DestinationKind.ownerProperties => page is OwnerPropertiesScreen,
      DestinationKind.ownerListings => page is OwnerListingsScreen,
      DestinationKind.propertyAnalytics =>
        page is OwnerPropertyAnalyticsScreen && page.property.id == target.id,
      DestinationKind.chat =>
        page is ChatScreen && page.conversation.id == target.id,
      DestinationKind.profileVerification =>
        page is ProfileVerificationScreen &&
            (target.workspace == null || page.workspace == target.workspace),
      DestinationKind.profileSettings =>
        page is ProfileSettingsScreen &&
            (target.workspace == null || page.workspace == target.workspace),
      DestinationKind.searchAlert =>
        page is PremiumAlertDetailScreen && page.alertId == target.id,
      DestinationKind.tenancyInvitation =>
        page is TenancyInvitationDetailScreen &&
            page.invitationId == target.id &&
            (target.workspace == null || page.workspace == target.workspace),
      DestinationKind.tenancyInvitations =>
        page is TenancyInvitationsScreen &&
            page.propertyId.isEmpty &&
            (target.workspace == null || page.workspace == target.workspace),
      DestinationKind.notificationDetail =>
        page is NotificationDetailScreen && page.notification.id == target.id,
      DestinationKind.notifications => page is NotificationsScreen,
      DestinationKind.externalPromotion => false,
    };
  }

  static Future<void> _show(
    AppDestination target,
    AppNotificationContent? notification,
  ) async {
    final AppWorkspace workspace =
        target.workspace ?? WorkspaceCubit.instance.state;
    final NotificationRole role = workspace.isOwner
        ? NotificationRole.owner
        : NotificationRole.tenant;
    switch (target.kind) {
      case DestinationKind.property:
        await Go.to<void>(
          PropertyDetailsScreen(propertyId: target.id, offerId: target.offerId),
        );
      case DestinationKind.tenantVisit:
        await Go.to<void>(
          VisitDetailsScreen(
            visit: const TenantVisitContent.initial().copyWith(
              id: target.id,
              propertyTitle: notification?.title ?? '',
              rentalSelection: notification?.payload.rentalSelection,
            ),
            openReview: target.openReview,
          ),
        );
      case DestinationKind.tenantVisits:
        await Go.to<void>(const TenantVisitsScreen());
      case DestinationKind.ownerRequest:
        await Go.to<void>(OwnerRequestDetailsScreen(requestId: target.id));
      case DestinationKind.ownerProperties:
        await Go.to<void>(const OwnerPropertiesScreen());
      case DestinationKind.ownerListings:
        await Go.to<void>(const OwnerListingsScreen());
      case DestinationKind.propertyAnalytics:
        await Go.to<void>(
          OwnerPropertyAnalyticsScreen(
            property: OwnerPropertyContent.initial().copyWith(
              id: target.id,
              title: notification?.title ?? '',
            ),
          ),
        );
      case DestinationKind.chat:
        await Go.to<void>(
          ChatScreen(
            conversation: const ConversationContent.initial().copyWith(
              id: target.id,
            ),
          ),
        );
      case DestinationKind.profileVerification:
        await Go.to<void>(ProfileVerificationScreen(workspace: workspace));
      case DestinationKind.profileSettings:
        await Go.to<void>(ProfileSettingsScreen(workspace: workspace));
      case DestinationKind.searchAlert:
        await Go.to<void>(PremiumAlertDetailScreen(alertId: target.id));
      case DestinationKind.tenancyInvitation:
        await Go.to<void>(
          TenancyInvitationDetailScreen(
            invitationId: target.id,
            workspace: workspace,
          ),
        );
      case DestinationKind.tenancyInvitations:
        await Go.to<void>(TenancyInvitationsScreen(workspace: workspace));
      case DestinationKind.notificationDetail:
        if (notification != null) {
          await Go.to<void>(
            NotificationDetailScreen(role: role, notification: notification),
          );
        }
      case DestinationKind.notifications:
        await Go.to<void>(const NotificationsScreen());
      case DestinationKind.externalPromotion:
        if (target.url != null) {
          await launchUrl(target.url!, mode: LaunchMode.inAppBrowserView);
        }
    }
  }
}
