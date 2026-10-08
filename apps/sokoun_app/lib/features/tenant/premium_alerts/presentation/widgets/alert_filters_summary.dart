import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_filter/property_filter_label_resolver.dart';

class AlertFiltersSummary extends StatelessWidget {
  const AlertFiltersSummary({
    super.key,
    required this.filters,
    required this.options,
  });
  final PropertySearchFilters filters;
  final PropertyFilterOptionsModel options;
  @override
  Widget build(BuildContext context) {
    final labels = PropertyFilterLabelResolver(options);
    final entries = [
      if (filters.search.trim().isNotEmpty) filters.search.trim(),
      for (final entry in filters.activeFilters) labels.labelFor(entry),
      if (filters.ordering == '-created_at')
        labels.labelFor(
          const PropertySearchFilterEntry(id: 'ordering', value: '-created_at'),
        ),
    ];
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16.w),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 12.h,
          children: [
            AppText(
              LocaleKeys.featureAlertFilters,
              fontWeight: FontWeight.bold,
            ),
            if (entries.isEmpty) AppText(LocaleKeys.featureAlertAllProperties),
            for (final label in entries) AppText(label),
          ],
        ),
      ),
    );
  }
}
