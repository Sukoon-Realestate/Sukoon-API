import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/helpers/status_builder.dart';

import '../../data/models/property_review_summary.dart';
import '../cubits/property_review_summary_cubit.dart';
import 'property_rating_card.dart';

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
                  ? _buildSummary(const PropertyReviewSummary.initial())
                  : StatusBuilder<
                      PropertyReviewSummaryCubit,
                      PropertyReviewSummary
                    >.withShimmer(
                      initialDataForShimmer:
                          const PropertyReviewSummary.initial(),
                      onRetry: () => _cubit.load(propertyId: widget.propertyId),
                      shimmerBuilder: (_) => const PropertyRatingCard(
                        propertyId: '',
                        averageRating: null,
                        totalReviews: 0,
                      ),
                      builder: _buildSummary,
                    ),
            ),
      );

  Widget _buildSummary(PropertyReviewSummary summary) {
    final int? count = summary.totalReviews;
    final double? rating = summary.averageRating;
    return PropertyRatingCard(
      propertyId: widget.propertyId,
      averageRating:
          rating != null && rating.isFinite && rating >= 0 && rating <= 5
          ? rating
          : null,
      totalReviews: count != null && count >= 0 ? count : null,
    );
  }
}
