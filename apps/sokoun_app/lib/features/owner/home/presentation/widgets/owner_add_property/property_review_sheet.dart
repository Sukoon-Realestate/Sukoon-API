import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_selection_panel.dart';
import 'package:flutter/material.dart';
import 'listing_quality_card.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/finance/presentation/egyptian_pound_text.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

import '../../../data/enums/property_review_action.dart';
import '../../../data/models/owner_add_property_content.dart';
import 'property_review_section.dart';
import 'rental_media_review_summary.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';

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
                style: AppTextStyles.bold.copyWith(fontSize: 22),
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
                style: AppTextStyles.regular14.copyWith(
                  fontSize: 14,
                  color: context.appColor(AppColors.sokoonGray),
                  height: 1.45,
                ),
              ),
              const SizedBox(height: 16),
              if (form.submissionInventory case final inventory?) ...[
                for (final offer in inventory.offers)
                  RentalSelectionPanel(
                    inventory: inventory,
                    selection: RentalSelection.fromOffer(
                      propertyId: '',
                      inventory: inventory,
                      offer: offer,
                    ),
                  ),
                if (inventory.hasLocalOnlyDetails)
                  AppText(LocaleKeys.rentalDraftDetailsHelp),
              ],
              if (form.rentalInventory == null) ListingQualityCard(form: form),
              SokounReveal(
                child: PropertyReviewSection(
                  title: form.rentalInventory == null
                      ? LocaleKeys.ownerPropertyReviewBasics
                      : form.isPartialOffering
                      ? LocaleKeys.rentalPropertyContext
                      : LocaleKeys.rentalPropertyDetails,
                  lines: [
                    form.title,
                    form.propertyType,
                    '${form.locationSummary}، ${form.street}',
                    if (form.location case final location?)
                      location.coordinates,
                    if (form.bedrooms.isNotEmpty)
                      '${LocaleKeys.rentalPropertyRooms}: ${form.bedrooms}',
                    if (form.bathrooms.isNotEmpty)
                      '${LocaleKeys.rentalParentPropertyBathrooms}: ${form.bathrooms}',
                    if (form.space.isNotEmpty)
                      '${LocaleKeys.rentalParentPropertyArea}: ${form.space}',
                    if (form.areaDescription.trim().isNotEmpty)
                      '${LocaleKeys.ownerAddPropertyAreaDescription}: ${form.areaDescription}',
                    if (form.floor.trim().isNotEmpty)
                      '${LocaleKeys.ownerAddPropertyFloor}: ${form.floor}',
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
                    for (final (index, photo) in form.photoDrafts.indexed)
                      if (photo.name.trim().isNotEmpty ||
                          photo.description.trim().isNotEmpty)
                        '${LocaleKeys.ownerAddPropertyPhotoNumber.replaceAll('{number}', '${index + 1}')}: ${[photo.name.trim(), photo.description.trim()].where((value) => value.isNotEmpty).join(' — ')}',
                    '${LocaleKeys.ownerPropertyReviewVideo}: ${form.hasVideo ? LocaleKeys.ownerPropertyVideoSelected : LocaleKeys.ownerPropertyVideoRequired}',
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.photos),
                ),
              ),
              RentalMediaReviewSummary(form: form),
              if (form.submissionInventory != null) ...[
                AppText(LocaleKeys.rentalOfferingMode),
                AppText(
                  form.isPartialOffering
                      ? LocaleKeys.rentalPartialMode
                      : LocaleKeys.rentalEntireProperty,
                ),
                AppText(LocaleKeys.rentalSharedSpaces),
                AppText(
                  [
                    ...form.amenityLabels,
                    ...form.submissionInventory!.draftDetails.facilities,
                  ].join(' · '),
                ),
                if (form.submissionInventory!.draftDetails.rules.isNotEmpty)
                  AppText(
                    form.submissionInventory!.draftDetails.rules.join('\n'),
                  ),
              ],
              if (form.rentalInventory == null)
                SokounReveal(
                  delay: const Duration(milliseconds: 120),
                  child: PropertyReviewSection(
                    title: LocaleKeys.ownerAddPropertyPricingTitle,
                    lines: [
                      '${LocaleKeys.ownerAddPropertyPrice}: ${EgyptianPoundText.format(form.monthlyPrice)}',
                      '${LocaleKeys.ownerAddPropertyPricePeriod}: ${form.rentalUnitLabel}',
                      '${LocaleKeys.ownerAddPropertySuitableFor}: ${form.suitableForLabel}',
                      '${LocaleKeys.ownerAddPropertyMinimumRentalMonths}: ${form.rentalDuration}',
                      form.amenityLabels.join(' · '),
                      form.description,
                    ],
                    onEdit: () => Go.back(PropertyReviewAction.pricing),
                  ),
                ),
              SokounReveal(
                delay: const Duration(milliseconds: 160),
                child: PropertyReviewSection(
                  title: LocaleKeys.ownerAddPropertyAdditionalDetails,
                  lines: [
                    if (form.country.isNotEmpty)
                      '${LocaleKeys.ownerAddPropertyCountry}: ${form.country}',
                    if (form.neighborhood.isNotEmpty)
                      '${LocaleKeys.ownerAddPropertyNeighborhood}: ${form.neighborhood}',
                    if (form.buildingYear.isNotEmpty)
                      '${LocaleKeys.tenantPropertyDetailsBuildingYear}: ${form.buildingYear}',
                    if (!form.isPartialOffering && form.deposit.isNotEmpty)
                      '${LocaleKeys.ownerAddPropertyDeposit}: ${PropertyDetailsModel.depositLabelFor(form.deposit)}',
                    if (!form.isPartialOffering && form.smokingAllowed != null)
                      form.smokingAllowed == true
                          ? LocaleKeys.tenantPropertyDetailsSmokingAllowed
                          : LocaleKeys.tenantPropertyDetailsSmokingNotAllowed,
                    form.hasOwnershipProof
                        ? LocaleKeys.ownerPropertyReviewProof
                        : LocaleKeys.ownerPropertyReviewNoProof,
                  ],
                  onEdit: () => Go.back(PropertyReviewAction.pricing),
                ),
              ),
            ],
          ),
        ),
      ),
      SokounActionFooter(
        child: DefaultButton(
          title: !form.canSaveToServer()
              ? LocaleKeys.rentalSaveLocalDraft
              : isEditing
              ? LocaleKeys.ownerPropertiesSaveChanges
              : LocaleKeys.ownerAddPropertySubmitReview,
          onTap: () => Go.back(PropertyReviewAction.submit),
          textStyle: AppTextStyles.medium13.copyWith(
            fontSize: FontSize.s13,
            height: 1.45,
          ),
        ),
      ),
    ],
  );
}
