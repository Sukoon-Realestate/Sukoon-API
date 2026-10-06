import 'package:flutter/material.dart';

typedef PullRefreshIndicatorBuilder =
    Widget Function(BuildContext context, RefreshIndicatorStatus? status);

/// Optional app-owned presentation for the shared pull-to-refresh gesture.
///
/// The builder is placed above the scroll view, at its top edge. It should hide
/// for null, canceled and done statuses, and exclude hidden content from semantics.
@immutable
class PullRefresherTheme extends ThemeExtension<PullRefresherTheme> {
  const PullRefresherTheme({required this.indicatorBuilder});

  final PullRefreshIndicatorBuilder indicatorBuilder;

  @override
  PullRefresherTheme copyWith({
    PullRefreshIndicatorBuilder? indicatorBuilder,
  }) => PullRefresherTheme(
    indicatorBuilder: indicatorBuilder ?? this.indicatorBuilder,
  );

  @override
  PullRefresherTheme lerp(covariant PullRefresherTheme? other, double t) =>
      other != null && t >= .5 ? other : this;
}
