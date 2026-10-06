import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../widgets/property_reviews_list.dart';

class PropertyReviewsScreen extends StatelessWidget {
  const PropertyReviewsScreen({super.key, required this.propertyId});
  final String propertyId;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.propertyReviewsTitle,
    body: SafeArea(child: PropertyReviewsList(propertyId: propertyId)),
  );
}
