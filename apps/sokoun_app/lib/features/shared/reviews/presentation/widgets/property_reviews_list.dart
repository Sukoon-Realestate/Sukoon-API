import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/pagify.dart';
import '../../data/property_reviews_data.dart';
import '../../data/models/property_review.dart';
import 'property_review_card.dart';
import 'property_reviews_empty_state.dart';

class PropertyReviewsList extends StatefulWidget {
  const PropertyReviewsList({super.key, required this.propertyId});
  final String propertyId;
  @override
  State<PropertyReviewsList> createState() => _PropertyReviewsListState();
}

class _PropertyReviewsListState extends State<PropertyReviewsList> {
  final PagifyController<PropertyReview> _controller =
      PagifyController<PropertyReview>();
  // AppPagify owns disposal of its controller.
  @override
  Widget build(BuildContext context) => AppPagify<PropertyReview>(
    enablePullRefresh: true,
    pagifyController: _controller,
    shrinkWrap: false,
    asyncCall: (_, page) =>
        PropertyReviewsData.getPage(propertyId: widget.propertyId, page: page),
    cacheKey: 'property_reviews_${widget.propertyId}',
    cachePolicy: ReadCachePolicy.privateMemory,
    cacheToJson: (review) => review.toJson(),
    cacheFromJson: PropertyReview.fromJson,
    emptyListView: const PropertyReviewsEmptyState(),
    errorBuilder: (error) =>
        ExceptionView(msg: error.msg, onRetry: () async => _controller.retry()),
    itemBuilder: (_, __, ___, review) =>
        PropertyReviewCard(key: ValueKey(review.id), review: review),
  );
}
