import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

import '../../../data/enums/property_review_action.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'property_review_section.dart';

class PropertyReviewSheet extends StatelessWidget {
  const PropertyReviewSheet({
    super.key,
    required this.form,
    required this.isEditing,
  });

  final OwnerAddPropertyFormState form;
  final bool isEditing;

  @override
  Widget build(BuildContext context) => Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsetsDirectional.fromSTEB(20, 0, 8, 8),
        child: Row(
          children: [
            Expanded(
              child: AppText(
                LocaleKeys.ownerPropertyReviewTitle,
                fontSize: 22,
                fontWeight: FontWeight.w700,
              ),
            ),
            IconButton(
              tooltip: MaterialLocalizations.of(context).closeButtonTooltip,
              onPressed: Go.back,
              icon: const Icon(Icons.close_rounded),
            ),
          ],
        ),
      ),
      Flexible(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                LocaleKeys.ownerPropertyReviewHint,
                fontSize: 14,
                color: AppColors.sokoonGray,
              ),
              const SizedBox(height: 16),
              SokounReveal(
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerPropertyReviewBasics,
                  lines: [
                    form.title,
                    form.propertyType,
                    '${form.locationSummary}، ${form.street}',
                    '${LocaleKeys.ownerAddPropertyBedrooms}: ${form.bedrooms} · ${LocaleKeys.ownerAddPropertyBathrooms}: ${form.bathrooms}',
                    '${LocaleKeys.ownerAddPropertySpace}: ${form.space}',
                    '${LocaleKeys.ownerAddPropertyFloor}: ${form.floor} · ${LocaleKeys.ownerAddPropertyBuildingYear}: ${form.buildingYear}',
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.basics),
                ),
              ),
              SokounReveal(
                delay: const Duration(milliseconds: 40),
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerAddPropertyPhotosSummary,
                  lines: [
                    '${LocaleKeys.ownerAddPropertyCount}: ${form.photoCount}',
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.photos),
                ),
              ),
              SokounReveal(
                delay: const Duration(milliseconds: 80),
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerAddPropertyVideoSummary,
                  lines: [
                    form.video?.formattedDuration ??
                        LocaleKeys.ownerAddPropertyVideoSkipped,
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.video),
                ),
              ),
              SokounReveal(
                delay: const Duration(milliseconds: 120),
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerAddPropertyPricingTitle,
                  lines: [
                    '${LocaleKeys.ownerAddPropertyPrice}: ${form.monthlyPrice} ${LocaleKeys.ownerAddPropertyCurrency}',
                    '${LocaleKeys.ownerAddPropertyDeposit}: ${form.deposit}',
                    '${LocaleKeys.ownerAddPropertyRentalPeriod}: ${form.rentalDuration} ${form.rentalUnit}',
                    form.amenities.join(' · '),
                    form.description,
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.pricing),
                ),
              ),
              SokounReveal(
                delay: const Duration(milliseconds: 160),
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerPropertyReviewAdditional,
                  lines: [
                    '${LocaleKeys.ownerAddPropertySmokingQuestion}: ${form.smokingPolicy}',
                    '${LocaleKeys.ownerAddPropertySuitableFor}: ${form.suitableFor}',
                    '${LocaleKeys.ownerAddPropertyProofSummary}: ${form.proofFileName}',
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.details),
                ),
              ),
            ],
          ),
        ),
      ),
      SokounActionFooter(
        child: DefaultButton(
          title: isEditing
              ? LocaleKeys.ownerPropertiesSaveChanges
              : LocaleKeys.ownerAddPropertySubmitReview,
          onTap: () => Go.back(PropertyReviewAction.submit),
        ),
      ),
    ],
  );
}
