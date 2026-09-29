import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';

import '../widgets/notifications_empty_state.dart';

class NotificationsEmptyScreen extends StatelessWidget {
  const NotificationsEmptyScreen({super.key, required this.role});

  final NotificationRole role;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.notificationsFlowTitle,
      showBackButton: true,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(child: NotificationsEmptyState(role: role)),
    );
  }
}
