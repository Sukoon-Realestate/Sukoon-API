import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import '../../data/models/rent_overview.dart';
import '../cubits/rent_overview_cubit.dart';
import 'rent_overview_card.dart';
import 'rent_overview_empty_state.dart';

class RentOverviewSection extends StatelessWidget {
  const RentOverviewSection({
    super.key,
    required this.cubit,
    required this.request,
    required this.onRefresh,
  });
  final RentOverviewCubit cubit;
  final Future<void> request;
  final Future<void> Function() onRefresh;
  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      AppText(LocaleKeys.journeyYourRent, fontWeight: FontWeight.bold),
      8.szH,
      PremiumRemoteView<RentOverviewCubit, RentOverview>(
        cubit: cubit,
        request: request,
        initialData: const RentOverview.initial(),
        onRetry: onRefresh,
        builder: (overview) => overview.invoice == null
            ? const RentOverviewEmptyState()
            : RentOverviewCard(
                invoice: overview.invoice!,
                isCached: cubit.isCached,
                onReturned: onRefresh,
              ),
      ),
    ],
  );
}
