import 'package:flutter/material.dart';
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

abstract final class NotificationNavigation {
  static Future<void> open({
    required AppNotificationContent notification,
    required NotificationRole role,
  }) async {
    final String actionType = notification.primaryActionType;
    final String targetId = notification.primaryTargetId;

    if (actionType == 'dismiss') {
      Go.back();
      return;
    }

    if (notification.kind == AppNotificationKind.visitRequest &&
        targetId.isNotEmpty) {
      await Go.to<void>(OwnerRequestDetailsScreen(requestId: targetId));
      return;
    }

    if (notification.kind == AppNotificationKind.visitAccepted ||
        actionType == 'view_visit') {
      await Go.to<void>(
        VisitDetailsScreen(
          visit: TenantVisitContent(
            id: targetId,
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
      await Go.to<void>(
        ChatThreadScreen(
          conversation: ConversationContent(
            id: chatId,
            name: notification.payload.senderName.isNotEmpty
                ? notification.payload.senderName
                : notification.title,
            property: notification.detailLocation,
            lastMessage: notification.description,
            time: notification.time,
            unreadCount: 1,
            isVerified: true,
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
      await showModalBottomSheet<bool>(
        context: Go.context,
        useSafeArea: true,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (_) => VisitRatingSheet(propertyTitle: notification.title),
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
      await Go.to<void>(
        OwnerPropertyAnalyticsScreen(
          property: property,
          analytics: OwnerPropertyAnalyticsContent.initial().copyWith(
            views: notification.payload.viewsCount,
          ),
        ),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.dailyBump) {
      await Go.to<void>(const OwnerListingsScreen());
      return;
    }

    if (notification.kind == AppNotificationKind.accountVerification ||
        notification.kind == AppNotificationKind.securityAlert) {
      await Go.to<void>(
        role.isOwner ? const OwnerMoreScreen() : const TenantProfileScreen(),
      );
      return;
    }

    if (notification.kind == AppNotificationKind.promotion &&
        notification.payload.promoUrl.isNotEmpty) {
      final Uri? uri = Uri.tryParse(notification.payload.promoUrl);
      if (uri != null) {
        await launchUrl(uri, mode: LaunchMode.inAppBrowserView);
      }
      return;
    }

    final String propertyId = notification.payload.propertyId.isNotEmpty
        ? notification.payload.propertyId
        : targetId;
    if (propertyId.isNotEmpty) {
      await Go.to<void>(PropertyDetailsScreen(propertyId: propertyId));
      return;
    }

    if (role.isOwner) {
      await Go.to<void>(const OwnerListingsScreen());
    }
  }
}
