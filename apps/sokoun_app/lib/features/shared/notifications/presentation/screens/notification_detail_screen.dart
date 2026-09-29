import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';

import '../../data/enums/notification_role.dart';
import '../../data/models/app_notification_content.dart';
import '../cubits/notification_detail_cubit.dart';
import '../notification_navigation.dart';
import '../widgets/notification_details_content.dart';
import '../widgets/notification_page_header.dart';

class NotificationDetailScreen extends StatefulWidget {
  const NotificationDetailScreen({
    super.key,
    required this.role,
    required this.notification,
    this.fetchFromApi = true,
  });

  final NotificationRole role;
  final AppNotificationContent notification;
  final bool fetchFromApi;

  @override
  State<NotificationDetailScreen> createState() =>
      _NotificationDetailScreenState();
}

class _NotificationDetailScreenState extends State<NotificationDetailScreen> {
  late final NotificationDetailCubit _cubit;
  late final Future<void> _detailsRequest;

  @override
  void initState() {
    super.initState();
    _cubit = NotificationDetailCubit(initialNotification: widget.notification);
    _detailsRequest = _cubit.load(
      notificationId: widget.notification.id,
      fixture: widget.fetchFromApi ? null : widget.notification,
    );
  }

  @override
  void dispose() {
    unawaited(_cubit.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      showBackButton: false,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            NotificationPageHeader(title: LocaleKeys.notificationDetailsTitle),
            Expanded(
              child: BlocProvider<NotificationDetailCubit>.value(
                value: _cubit,
                child:
                    StatusBuilder<
                      NotificationDetailCubit,
                      AppNotificationContent
                    >.withShimmer(
                      initialDataForShimmer: widget.notification,
                      requestToTryAgainWhenError: _detailsRequest,
                      onRetry: () => _cubit.load(
                        notificationId: widget.notification.id,
                        fixture: widget.fetchFromApi
                            ? null
                            : widget.notification,
                      ),
                      errorType: ErrorType.defaultView,
                      builder: (notification) => NotificationDetailsContent(
                        notification: notification,
                        onPrimaryPressed: () => NotificationNavigation.open(
                          notification: notification,
                          role: widget.role,
                        ),
                        onDismissPressed: Go.back,
                      ),
                    ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
