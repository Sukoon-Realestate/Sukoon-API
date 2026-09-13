import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';

import 'models/app_notification_content.dart';
import 'models/notifications_response.dart';

abstract final class NotificationsData {
  static const int pageSize = 20;
  static const String cacheKey = 'notifications';

  static Future<bool> hasAuthenticatedSession() =>
      injector<NetworkService>().hasSessionCookies();

  static Future<(List<AppNotificationContent>, PaginationData)>
  getNotificationsPage({
    required int page,
    bool unreadOnly = false,
    void Function(int count)? onUnreadCount,
  }) async {
    final NotificationsResponse response = await getNotifications(
      page: page,
      unreadOnly: unreadOnly,
    );
    onUnreadCount?.call(response.unreadCount);
    return (
      response.results,
      PaginationData(
        perPage: response.perPage < 1 ? pageSize : response.perPage,
        totalPages: response.totalPages < 1 ? 1 : response.totalPages,
      ),
    );
  }

  static Future<NotificationsResponse> getNotifications({
    required int page,
    bool unreadOnly = false,
  }) async {
    final response = await injector<NetworkService>().callApi(
      NetworkRequest(
        method: RequestMethod.get,
        path: ApiConstants.notifications,
        queryParameters: {
          'page': page,
          'page_size': pageSize,
          if (unreadOnly) 'unread': true,
        },
      ),
      mapper: (json) => NotificationsResponse.fromJson(
        json is Map<String, dynamic> ? json : const {},
      ),
    );

    return response.data;
  }
}
