import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/contact/presentation/widgets/revealed_phone_card.dart';
import 'package:sokoun_app/features/shared/rental_offers/presentation/widgets/rental_offer_labels.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

import 'owner_visit_request_action_row.dart';
import 'owner_visit_request_identity_row.dart';
import 'owner_visit_request_status_banner.dart';
import 'owner_visit_request_time_row.dart';
import 'owner_visit_verification_warning.dart';

class OwnerVisitRequestCard extends StatelessWidget {
  const OwnerVisitRequestCard({
    super.key,
    required this.request,
    required this.onPressed,
    required this.onAcceptPressed,
    required this.onRejectPressed,
    this.isAccepting = false,
    this.isRejecting = false,
  });

  final OwnerVisitRequestContent request;
  final VoidCallback? onPressed;
  final VoidCallback? onAcceptPressed;
  final VoidCallback? onRejectPressed;
  final bool isAccepting;
  final bool isRejecting;

  @override
  Widget build(BuildContext context) {
    final String schedule = request.dateLabel.isNotEmpty
        ? request.dateLabel
        : request.time;
    final bool scheduleInSubtitle =
        schedule.isNotEmpty && request.subtitle.contains(schedule);
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: AppPadding.pW14,
            vertical: AppPadding.pH14,
          ),
          decoration: BoxDecoration(
            color: context.appColor(AppColors.white, surface: true),
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: context.appColor(AppColors.grayPale)),
          ),
          child: Column(
            spacing: 12.h,
            children: [
              OwnerVisitRequestIdentityRow(request: request),
              if (request.revealedPhone.isNotEmpty)
                RevealedPhoneCard(phoneNumber: request.revealedPhone)
              else if (request.isPhoneRevealed == true)
                OwnerRequestPrivacyBanner(
                  message: LocaleKeys.contactPhoneUnavailable,
                  icon: Icons.info_outline_rounded,
                ),
              if (request.rentalSelection != null)
                AppText(
                  RentalOfferLabels.accommodation(request.rentalSelection!),
                ),
              if (!request.isVerified &&
                  request.verificationWarning.trim().isNotEmpty)
                OwnerVisitVerificationWarning(
                  message: request.verificationWarning,
                ),
              if (!scheduleInSubtitle && schedule.isNotEmpty)
                OwnerVisitRequestTimeRow(dateLabel: schedule),
              if (request.canAccept || request.canReject)
                OwnerVisitRequestActionRow(
                  onAcceptPressed: request.canAccept ? onAcceptPressed : null,
                  onRejectPressed: request.canReject ? onRejectPressed : null,
                  isAccepting: isAccepting,
                  isRejecting: isRejecting,
                ),
              if (!request.status.canDecide ||
                  request.statusLabel.trim().isNotEmpty)
                OwnerVisitRequestStatusBanner(
                  status: request.status,
                  label: request.statusLabel,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
