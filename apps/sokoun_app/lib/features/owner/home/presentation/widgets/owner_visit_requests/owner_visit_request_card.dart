import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';

import 'owner_visit_request_action_row.dart';
import 'owner_visit_request_identity_row.dart';
import 'owner_visit_request_status_banner.dart';
import 'owner_visit_request_time_row.dart';

class OwnerVisitRequestCard extends StatelessWidget {
  const OwnerVisitRequestCard({
    super.key,
    required this.request,
    required this.onPressed,
    required this.onChatPressed,
    required this.onAcceptPressed,
    required this.onRejectPressed,
  });

  final OwnerVisitRequestContent request;
  final VoidCallback onPressed;
  final VoidCallback onChatPressed;
  final VoidCallback onAcceptPressed;
  final VoidCallback onRejectPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.transparent,
      child: InkWell(
        key: ValueKey('owner-request-card-${request.id}'),
        onTap: onPressed,
        borderRadius: BorderRadius.circular(16.r),
        child: Container(
          padding: EdgeInsets.symmetric(
            horizontal: AppPadding.pW14,
            vertical: AppPadding.pH14,
          ),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: AppColors.grayPale),
          ),
          child: Column(
            children: [
              OwnerVisitRequestIdentityRow(
                request: request,
                onChatPressed: onChatPressed,
              ),
              12.szH,
              OwnerVisitRequestTimeRow(
                dateLabel: request.dateLabel.isNotEmpty
                    ? request.dateLabel
                    : request.time,
              ),
              if (request.status.canDecide) ...[
                12.szH,
                OwnerVisitRequestActionRow(
                  onAcceptPressed: onAcceptPressed,
                  onRejectPressed: onRejectPressed,
                ),
              ],
              if (!request.status.canDecide) ...[
                12.szH,
                OwnerVisitRequestStatusBanner(status: request.status),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
