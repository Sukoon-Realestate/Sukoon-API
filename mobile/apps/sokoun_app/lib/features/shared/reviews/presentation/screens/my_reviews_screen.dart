import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/my_reviews_list.dart';

class MyReviewsScreen extends StatelessWidget {
  const MyReviewsScreen({super.key});
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.profileMyReviews,
    body: const SafeArea(child: MyReviewsList()),
  );
}
