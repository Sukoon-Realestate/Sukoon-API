import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_result_content.dart';

import '../widgets/tenant_search_results/imports.dart';

class TenantSearchResultsScreen extends StatelessWidget {
  const TenantSearchResultsScreen({super.key});

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
              const ResultsSearchHeader(),
              const ActiveFiltersBar(
                filters: TenantSearchResultContent.activeFilters,
              ),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 18.w, vertical: 10.h),
                child: AppText(
                  '${TenantSearchResultContent.results.length} نتيجة',
                  color: AppColors.sokoonGray,
                  fontSize: 13.sp,
                  fontWeight: FontWeight.w600,
                  textAlign: TextAlign.right,
                ),
              ),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.fromLTRB(16.w, 0, 16.w, 18.h),
                  itemBuilder: (context, index) {
                    return SearchResultCard(
                      item: TenantSearchResultContent.results[index],
                    );
                  },
                  separatorBuilder: (context, index) => 14.szH,
                  itemCount: TenantSearchResultContent.results.length,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
