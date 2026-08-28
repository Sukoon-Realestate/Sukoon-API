import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';

class TenantPropertyMetricsGrid extends StatelessWidget {
  const TenantPropertyMetricsGrid({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (int index = 0; index < property.metrics.length; index++) ...[
          Expanded(child: _MetricCard(metric: property.metrics[index])),
          if (index < property.metrics.length - 1) 8.szW,
        ],
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.metric});

  final TenantPropertyMetricContent metric;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 11.h),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(14.r),
        border: Border.all(color: AppColors.grayPale),
      ),
      child: Column(
        children: [
          Icon(metric.icon, color: AppColors.sokoonTeal, size: 18.r),
          5.szH,
          AppText(
            metric.value,
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontWeight: FontWeight.w900,
          ),
          3.szH,
          AppText(
            metric.label,
            color: AppColors.sokoonGray,
            fontSize: 10.sp,
            fontWeight: FontWeight.w500,
          ),
        ],
      ),
    );
  }
}
