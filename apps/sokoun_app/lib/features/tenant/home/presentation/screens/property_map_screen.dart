import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import '../../data/models/property_search_model.dart';
import '../widgets/property_map/property_map_results.dart';

class PropertyMapScreen extends StatelessWidget {
  const PropertyMapScreen({super.key, required this.filters});
  final PropertySearchFilters filters;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.freeMapResults,
    showBackButton: true,
    body: SafeArea(child: PropertyMapResults(filters: filters)),
  );
}
