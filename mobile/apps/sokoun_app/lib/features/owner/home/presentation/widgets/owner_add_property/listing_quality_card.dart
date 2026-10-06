import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../../data/enums/listing_quality_check.dart';
import '../../../data/listing_quality_data.dart';
import '../../../data/models/owner_add_property_content.dart';

class ListingQualityCard extends StatelessWidget {
  const ListingQualityCard({super.key, required this.form});
  final OwnerAddPropertyFormState form;
  @override
  Widget build(BuildContext context) {
    final checks = ListingQualityData.evaluate(form);
    final labels = {
      ListingQualityCheck.photos: LocaleKeys.freeQualityPhotos,
      ListingQualityCheck.location: LocaleKeys.freeQualityLocation,
      ListingQualityCheck.description: LocaleKeys.freeQualityDescription,
      ListingQualityCheck.deposit: LocaleKeys.freeQualityDeposit,
      ListingQualityCheck.captions: LocaleKeys.freeQualityCaptions,
      ListingQualityCheck.video: LocaleKeys.freeQualityVideo,
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(
              '${LocaleKeys.freeListingQuality} (${checks.values.where((value) => value).length}/${checks.length})',
              fontWeight: FontWeight.bold,
            ),
            const SizedBox(height: 8),
            AppText(LocaleKeys.freeQualityExplanation),
            const SizedBox(height: 8),
            for (final check in checks.entries)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 5),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      check.value
                          ? Icons.check_circle_outline
                          : Icons.info_outline,
                      color: context.appColor(
                        check.value
                            ? AppColors.sokoonTeal
                            : AppColors.sokoonMuted,
                      ),
                      size: 20,
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: AppText(labels[check.key]!)),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
