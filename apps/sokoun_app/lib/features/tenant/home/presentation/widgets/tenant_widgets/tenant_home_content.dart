import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';

import 'home_search_box.dart';
import 'home_section_header.dart';
import 'suggested_properties_section.dart';
import 'tenant_header.dart';
import 'tenant_visit_banner.dart';

class TenantHomeContent extends StatelessWidget {
  const TenantHomeContent({
    required this.properties,
    required this.showVisitBanner,
    required this.onNotificationsPressed,
    required this.onSearchPressed,
    required this.onVisitPressed,
    required this.onPropertyPressed,
    super.key,
  });

  final List<HomePropertyModel> properties;
  final bool showVisitBanner;
  final VoidCallback onNotificationsPressed;
  final VoidCallback onSearchPressed;
  final VoidCallback onVisitPressed;
  final ValueChanged<String> onPropertyPressed;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TenantHeader(onNotificationsPressed: onNotificationsPressed),
          18.szH,
          HomeSearchBox(onPressed: onSearchPressed),
          16.szH,
          TenantVisitBanner(
            onPressed: onVisitPressed,
          ).showIf(condition: () => showVisitBanner),
          18.szH,
          HomeSectionHeader(
            title: LocaleKeys.tenantHomeSuggestedForYou,
            actionTitle: LocaleKeys.tenantHomeViewAll,
            onActionTap: onSearchPressed,
          ),
          10.szH,
          SuggestedPropertiesSection(
            properties: properties,
            onPropertyPressed: onPropertyPressed,
          ),
          24.szH,
        ],
      ),
    );
  }
}
