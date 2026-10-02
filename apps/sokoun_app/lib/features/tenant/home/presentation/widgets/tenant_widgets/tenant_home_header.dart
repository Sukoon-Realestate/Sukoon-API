import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

import 'home_search_box.dart';
import 'home_section_header.dart';
import 'tenant_home_app_bar_title.dart';
import 'tenant_visit_banner.dart';

class TenantHomeHeader extends StatelessWidget {
  const TenantHomeHeader({super.key, required this.banner});

  final String? banner;

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.only(top: 12.h, bottom: 8.h),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const TenantHomeAppBarTitle(),
        20.szH,
        const HomeSearchBox(),
        if (banner?.trim().isNotEmpty == true) ...[
          16.szH,
          TenantVisitBanner(text: banner!.trim()),
        ],
        12.szH,
        const HomeSectionHeader(),
      ],
    ),
  );
}
