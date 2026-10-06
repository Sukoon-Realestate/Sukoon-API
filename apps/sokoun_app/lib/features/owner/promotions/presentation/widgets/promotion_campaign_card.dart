import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import '../../data/models/promotion_campaign.dart';

class PromotionCampaignCard extends StatelessWidget {
  const PromotionCampaignCard({super.key, required this.campaign});
  final PromotionCampaign campaign;
  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          AppText(campaign.propertyTitle, fontWeight: FontWeight.bold),
          8.szH,
          PremiumStatusBadge(status: campaign.status),
          if (campaign.startsAt != null)
            AppText(
              '${DateFormat.yMMMd().format(campaign.startsAt!.toLocal())} – ${campaign.endsAt == null ? '—' : DateFormat.yMMMd().format(campaign.endsAt!.toLocal())}',
            ),
          if (campaign.impressions != null)
            AppText('${LocaleKeys.paidImpressions} ${campaign.impressions}'),
        ],
      ),
    ),
  );
}
