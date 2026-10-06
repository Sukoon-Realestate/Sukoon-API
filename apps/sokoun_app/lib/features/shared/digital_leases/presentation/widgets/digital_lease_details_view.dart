import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_revision_body.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/digital_lease.dart';
import '../cubits/lease_action_cubit.dart';

class DigitalLeaseDetailsView extends StatefulWidget {
  const DigitalLeaseDetailsView({
    super.key,
    required this.lease,
    required this.isFresh,
    required this.onRefresh,
  });
  final DigitalLease lease;
  final bool isFresh;
  final Future<void> Function() onRefresh;
  @override
  State<DigitalLeaseDetailsView> createState() =>
      _DigitalLeaseDetailsViewState();
}

class _DigitalLeaseDetailsViewState extends State<DigitalLeaseDetailsView>
    with WidgetsBindingObserver {
  late final LeaseActionCubit _cubit;
  String? _signingKey;
  @override
  void initState() {
    super.initState();
    _cubit = LeaseActionCubit();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cubit.close();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) widget.onRefresh();
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: BlocBuilder<LeaseActionCubit, AsyncState<PremiumActionReceipt>>(
      bloc: _cubit,
      builder: (context, state) {
        final lease = widget.lease;
        final canChange =
            widget.isFresh &&
            !state.isLoading &&
            lease.id.isNotEmpty &&
            lease.revision > 0;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(lease.propertyTitle, fontWeight: FontWeight.bold),
            PremiumStatusBadge(status: lease.status),
            AppText(lease.ownerName),
            AppText(lease.tenantName),
            AppText(lease.rent.display),
            if (lease.startDate != null && lease.endDate != null)
              AppText(
                '${lease.startDate!.toIso8601String().substring(0, 10)} – ${lease.endDate!.toIso8601String().substring(0, 10)}',
              ),
            16.szH,
            AppText(LocaleKeys.paidLeasesExplanation),
            if (PremiumHostedData.httpsUri(lease.documentUrl) != null)
              OutlinedButton(
                onPressed: () async {
                  if (!await PremiumHostedData.open(lease.documentUrl)) {
                    PremiumFeedback.linkFailed();
                  }
                },
                child: AppText(LocaleKeys.paidLeaseDocument),
              ),
            16.szH,
            if (lease.canSign &&
                lease.status.isSignable &&
                PremiumHostedData.httpsUri(lease.documentUrl) != null)
              FilledButton(
                onPressed: !canChange
                    ? null
                    : () async {
                        _signingKey ??= const Uuid().v4();
                        final receipt = await _cubit.signing(
                          lease.id,
                          PremiumRevisionBody(
                            revision: lease.revision,
                            requestKey: _signingKey!,
                          ),
                        );
                        if (receipt != null &&
                            mounted &&
                            !await PremiumHostedData.open(
                              receipt.hostedUrl,
                              expiresAt: receipt.expiresAt,
                            )) {
                          PremiumFeedback.linkFailed();
                        }
                      },
                child: AppText(LocaleKeys.paidLeaseSign),
              ),
            AppText(LocaleKeys.paidLeaseRefreshNotice),
            TextButton.icon(
              onPressed: widget.onRefresh,
              icon: const Icon(Icons.refresh),
              label: AppText(LocaleKeys.paidRefresh),
            ),
            if (lease.canCancel && lease.status.isDraft)
              TextButton(
                onPressed: !canChange
                    ? null
                    : () async {
                        if (!await PremiumConfirmSheet.show(
                              context,
                              title: LocaleKeys.paidLeaseConfirmCancel,
                              details: AppText(lease.propertyTitle),
                              actionLabel: LocaleKeys.paidLeaseCancel,
                            ) ||
                            !mounted) {
                          return;
                        }
                        final receipt = await _cubit.cancel(
                          lease.id,
                          PremiumRevisionBody(
                            revision: lease.revision,
                            requestKey: const Uuid().v4(),
                          ),
                        );
                        if (receipt != null && mounted) {
                          PremiumFeedback.saved(receipt);
                          await widget.onRefresh();
                        }
                      },
                child: AppText(LocaleKeys.paidLeaseCancel),
              ),
          ],
        );
      },
    ),
  );
}
