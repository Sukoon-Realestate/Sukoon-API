import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../data/models/property_review_summary.dart';
import '../cubits/property_review_summary_cubit.dart';

class PropertyRatingSummary extends StatefulWidget {
  const PropertyRatingSummary({super.key, required this.propertyId});

  final String propertyId;

  @override
  State<PropertyRatingSummary> createState() => _PropertyRatingSummaryState();
}

class _PropertyRatingSummaryState extends State<PropertyRatingSummary> {
  late PropertyReviewSummaryCubit _cubit;

  void _initialize() {
    _cubit = PropertyReviewSummaryCubit();
    _cubit.load(propertyId: widget.propertyId);
  }

  @override
  void initState() {
    super.initState();
    _initialize();
  }

  @override
  void didUpdateWidget(covariant PropertyRatingSummary oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.propertyId != widget.propertyId) {
      // A rating belongs to one property; replace the owner on identity change.
      _cubit.close();
      _initialize();
    }
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      BlocProvider<PropertyReviewSummaryCubit>.value(
        value: _cubit,
        child:
            BlocSelector<
              PropertyReviewSummaryCubit,
              AsyncState<PropertyReviewSummary>,
              bool
            >(
              selector: (state) => state.isError,
              builder: (context, hasError) => hasError
                  ? const SizedBox.shrink()
                  : StatusBuilder<
                      PropertyReviewSummaryCubit,
                      PropertyReviewSummary
                    >.withShimmer(
                      initialDataForShimmer:
                          const PropertyReviewSummary.initial(),
                      onRetry: () => _cubit.load(propertyId: widget.propertyId),
                      shimmerBuilder: (_) =>
                          SizedBox(width: 64.w, height: 16.h),
                      builder: _buildSummary,
                    ),
            ),
      );

  Widget _buildSummary(PropertyReviewSummary summary) {
    if (summary.averageRating == null || summary.totalReviews == null) {
      return const SizedBox.shrink();
    }
    return Row(
      mainAxisSize: MainAxisSize.min,
      spacing: 4.w,
      children: [
        Icon(Icons.star_rounded, color: AppColors.amber, size: 16.r),
        AppText(
          summary.averageRating!.toStringAsFixed(1),
          style: AppTextStyles.extraBold13.copyWith(
            color: AppColors.sokoonNavy,
            fontSize: 13.sp,
          ),
        ),
        AppText(
          '(${summary.totalReviews})',
          style: AppTextStyles.medium12.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
          ),
        ),
      ],
    );
  }
}
