import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/shared/notifications/data/enums/notification_role.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/screens/notifications_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/shared_widgets/property_details_screen.dart';

import '../widgets/tenant_widgets/imports.dart';
import 'tenant_search_screen.dart';

class TenantHomeScreen extends StatelessWidget {
  const TenantHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: TenantHomeContent(
            onNotificationsPressed: () =>
                Go.to(const NotificationsScreen(role: NotificationRole.tenant)),
            onSearchPressed: () => Go.to(TenantSearchScreen()),
            onVisitPressed: () => Go.to(const TenantVisitsScreen()),
            onPropertyPressed: (propertyId) =>
                Go.to(PropertyDetailsScreen(propertyId: propertyId)),
          ),
        ),
      ),
    );
  }
}
