import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_request_content.dart';

import '../widgets/owner_requests/imports.dart';

class OwnerRequestsScreen extends StatelessWidget {
  const OwnerRequestsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AppText(
                  'طلبات الزيارة',
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w900,
                  textAlign: TextAlign.right,
                ),
                14.szH,
                const OwnerRequestTabs(tabs: OwnerRequestsContent.tabs),
                14.szH,
                for (final request in OwnerRequestsContent.requests) ...[
                  OwnerRequestCard(request: request),
                  12.szH,
                ],
                12.szH,
              ],
            ),
          ),
        ),
      ),
    );
  }
}
