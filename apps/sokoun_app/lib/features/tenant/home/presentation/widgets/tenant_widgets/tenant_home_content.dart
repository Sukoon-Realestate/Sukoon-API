import 'package:flutter/cupertino.dart' show CupertinoActivityIndicator;
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
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
    required this.scrollController,
    required this.isLoadingMore,
    super.key,
  });

  final List<HomePropertyModel> properties;
  final bool showVisitBanner;
  final ScrollController scrollController;
  final bool isLoadingMore;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      controller: scrollController,
      physics: const AlwaysScrollableScrollPhysics(),
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
          HomeSectionHeader(),
          10.szH,
          SuggestedPropertiesSection(properties: properties),
          if (isLoadingMore) ...[16.szH, const CupertinoActivityIndicator()],
          24.szH,
        ],
      ),
    );
  }
}
