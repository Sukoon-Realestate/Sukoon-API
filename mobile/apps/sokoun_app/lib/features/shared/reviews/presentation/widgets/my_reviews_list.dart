import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/exeption_view.dart';
import 'package:pagify/pagify.dart';
import '../../data/my_reviews_data.dart';
import '../../data/models/my_review.dart';
import 'my_review_card.dart';
import 'my_reviews_empty_state.dart';

class MyReviewsList extends StatefulWidget {
  const MyReviewsList({super.key});
  @override
  State<MyReviewsList> createState() => _MyReviewsListState();
}

class _MyReviewsListState extends State<MyReviewsList> {
  final PagifyController<MyReview> _controller = PagifyController<MyReview>();
  // AppPagify owns disposal of its controller.
  @override
  Widget build(BuildContext context) => AppPagify<MyReview>(
    enablePullRefresh: true,
    pagifyController: _controller,
    shrinkWrap: false,
    asyncCall: (_, page) => MyReviewsData.getPage(page),
    cacheKey: MyReviewsData.cacheKey,
    cacheToJson: (review) => review.toJson(),
    cacheFromJson: MyReview.fromJson,
    emptyListView: const MyReviewsEmptyState(),
    errorBuilder: (error) =>
        ExceptionView(msg: error.msg, onRetry: () async => _controller.retry()),
    itemBuilder: (_, __, ___, review) =>
        MyReviewCard(key: ValueKey(review.id), review: review),
  );
}
