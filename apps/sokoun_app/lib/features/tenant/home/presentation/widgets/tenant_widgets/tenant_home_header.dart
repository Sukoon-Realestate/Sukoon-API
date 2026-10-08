import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';

import 'home_search_box.dart';
import 'home_section_header.dart';
import 'tenant_home_app_bar_title.dart';
import 'tenant_visit_banner.dart';
import 'tenant_search_tools.dart';
import 'package:sokoun_app/features/shared/profile/presentation/widgets/contracts/contracts_entry.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';

class TenantHomeHeader extends StatelessWidget {
  const TenantHomeHeader({
    super.key,
    required this.banner,
    this.rentOverview,
    this.rentalSections,
  });

  final HomeVisitBannerModel? banner;
  final Widget? rentOverview;
  final Widget? rentalSections;

  @override
  Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.only(top: 12.h, bottom: 8.h),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const TenantHomeAppBarTitle(),
        20.szH,
        const HomeSearchBox(),
        const TenantSearchTools(),
        if (rentOverview != null) ...[
          12.szH,
          rentOverview!,
          const ContractsEntry(workspace: AppWorkspace.tenant),
        ],
        if (banner != null && !banner!.isEmpty) ...[
          16.szH,
          TenantVisitBanner(banner: banner!),
        ],
        12.szH,
        if (rentalSections != null) rentalSections!,
        const HomeSectionHeader(),
      ],
    ),
  );
}
