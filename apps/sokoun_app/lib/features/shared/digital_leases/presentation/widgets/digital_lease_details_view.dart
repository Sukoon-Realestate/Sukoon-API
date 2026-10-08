import 'lease_details_summary.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
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
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/digital_lease.dart';
import '../cubits/lease_action_cubit.dart';
import 'lease_rent_entry.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_status.dart';

class DigitalLeaseDetailsView extends StatefulWidget {
  const DigitalLeaseDetailsView({
    super.key,
    required this.lease,
    required this.isFresh,
    required this.onRefresh,
    required this.workspace,
    this.capabilities = FeatureServiceCapabilities.configured,
  });
  final DigitalLease lease;
  final FeatureServiceCapabilities capabilities;
  final AppWorkspace workspace;
  final bool isFresh;
  final Future<void> Function() onRefresh;
  @override
  State<DigitalLeaseDetailsView> createState() =>
      _DigitalLeaseDetailsViewState();
}

class _DigitalLeaseDetailsViewState extends State<DigitalLeaseDetailsView>
    with WidgetsBindingObserver {
  late final LeaseActionCubit _cubit;
  String? _signingKey, _cancelKey;
  @override
  void initState() {
    super.initState();
    _cubit = LeaseActionCubit(capabilities: widget.capabilities);
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didUpdateWidget(covariant DigitalLeaseDetailsView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.lease.id != widget.lease.id ||
        oldWidget.lease.revision != widget.lease.revision) {
      _signingKey = null;
      _cancelKey = null;
    }
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
            LeaseDetailsSummary(lease: lease),
            16.szH,
            AppText(LocaleKeys.paidLeasesExplanation),
            if (lease.id.isNotEmpty &&
                (lease.status == PremiumStatus.signed || lease.status.isActive))
              LeaseRentEntry(
                leaseId: lease.id,
                propertyTitle: lease.propertyTitle,
                workspace: widget.workspace,
              ),
            if (widget.capabilities.signedDocuments &&
                PremiumHostedData.httpsUri(lease.documentUrl) != null)
              OutlinedButton(
                onPressed: () async {
                  if (!await PremiumHostedData.open(lease.documentUrl)) {
                    PremiumFeedback.linkFailed();
                  }
                },
                child: AppText(LocaleKeys.paidLeaseDocument),
              ),
            16.szH,
            if (widget.capabilities.leaseSigning &&
                lease.canSign &&
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
            if (!widget.capabilities.leaseSigning && lease.status.isSignable)
              AppText(LocaleKeys.featureSigningUnavailable),
            if (widget.capabilities.leaseSigning)
              AppText(LocaleKeys.paidLeaseRefreshNotice),
            if (state.isError && state.msg?.isNotEmpty == true)
              AppText(state.msg!, color: Theme.of(context).colorScheme.error),
            TextButton.icon(
              onPressed: widget.onRefresh,
              icon: const Icon(Icons.refresh),
              label: AppText(LocaleKeys.paidRefresh),
            ),
            if (widget.workspace.isOwner &&
                lease.canCancel &&
                lease.status.isDraft)
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
                            requestKey: _cancelKey ??= const Uuid().v4(),
                          ),
                        );
                        if (!mounted) return;
                        if (receipt != null) PremiumFeedback.saved(receipt);
                        await widget.onRefresh();
                      },
                child: AppText(LocaleKeys.paidLeaseCancel),
              ),
          ],
        );
      },
    ),
  );
}
