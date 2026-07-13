import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/home/data/models/owner_visit_request_content.dart';

import '../widgets/owner_visit_requests/imports.dart';

class OwnerVisitRequestsScreen extends StatelessWidget {
  const OwnerVisitRequestsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const OwnerVisitRequestsTopBar(),
              Container(
                padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 14.h),
                decoration: const BoxDecoration(
                  color: AppColors.white,
                  border: Border(bottom: BorderSide(color: AppColors.grayPale)),
                ),
                child: Column(
                  children: [
                    const OwnerVisitRequestSummaryGrid(
                      summaries: OwnerVisitRequestsContent.summaries,
                    ),
                    12.szH,
                    const OwnerVisitRequestFilters(
                      filters: OwnerVisitRequestsContent.filters,
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
                  itemBuilder: (context, index) {
                    return OwnerVisitRequestCard(
                      request: OwnerVisitRequestsContent.requests[index],
                    );
                  },
                  separatorBuilder: (context, index) => 12.szH,
                  itemCount: OwnerVisitRequestsContent.requests.length,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
