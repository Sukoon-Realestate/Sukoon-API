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
    super.key,
  });

  final List<HomePropertyModel> properties;
  final bool showVisitBanner;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const TenantHeader(),
          18.szH,
          const HomeSearchBox(),
          16.szH,
          const TenantVisitBanner().showIf(condition: () => showVisitBanner),
          18.szH,
          HomeSectionHeader(
            title: LocaleKeys.tenantHomeSuggestedForYou,
            actionTitle: LocaleKeys.tenantHomeViewAll,
          ),
          10.szH,
          SuggestedPropertiesSection(properties: properties),
          24.szH,
        ],
      ),
    );
  }
}
