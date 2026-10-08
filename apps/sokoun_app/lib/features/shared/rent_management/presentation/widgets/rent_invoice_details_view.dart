import 'rent_invoice_summary.dart';
import 'rent_invoice_lease_entry.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_feedback.dart';
import '../../data/models/rent_invoice.dart';
import '../../data/models/rent_checkout_body.dart';
import '../cubits/rent_checkout_cubit.dart';

class RentInvoiceDetailsView extends StatefulWidget {
  const RentInvoiceDetailsView({
    super.key,
    required this.invoice,
    required this.isFresh,
    required this.onRefresh,
    this.workspace = AppWorkspace.tenant,
    this.capabilities = FeatureServiceCapabilities.configured,
  });
  final RentInvoice invoice;
  final AppWorkspace workspace;
  final FeatureServiceCapabilities capabilities;
  final bool isFresh;
  final Future<void> Function() onRefresh;
  @override
  State<RentInvoiceDetailsView> createState() => _RentInvoiceDetailsViewState();
}

class _RentInvoiceDetailsViewState extends State<RentInvoiceDetailsView>
    with WidgetsBindingObserver {
  late final RentCheckoutCubit _cubit;
  String? _requestKey;
  @override
  void initState() {
    super.initState();
    _cubit = RentCheckoutCubit(capabilities: widget.capabilities);
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cubit.close();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant RentInvoiceDetailsView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.invoice.id != widget.invoice.id) _requestKey = null;
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) widget.onRefresh();
  }

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
    padding: const EdgeInsets.all(20),
    child: BlocBuilder<RentCheckoutCubit, AsyncState<PremiumActionReceipt>>(
      bloc: _cubit,
      builder: (context, state) {
        final invoice = widget.invoice;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            RentInvoiceSummary(invoice: invoice),
            16.szH,
            AppText(LocaleKeys.paidInvoicesExplanation),
            if (invoice.leaseId.isNotEmpty)
              RentInvoiceLeaseEntry(
                leaseId: invoice.leaseId,
                workspace: widget.workspace,
              ),
            if (widget.capabilities.rentCheckout &&
                !widget.workspace.isOwner &&
                invoice.canPay &&
                invoice.status.isPayable &&
                invoice.amount.isKnown &&
                invoice.amount.amountMinor! > 0)
              FilledButton(
                onPressed: !widget.isFresh || state.isLoading
                    ? null
                    : () async {
                        _requestKey ??= const Uuid().v4();
                        final receipt = await _cubit.checkout(
                          RentCheckoutBody(
                            invoiceId: invoice.id,
                            requestKey: _requestKey!,
                          ),
                        );
                        if (receipt == null || !context.mounted) return;
                        final confirmed = await PremiumConfirmSheet.show(
                          context,
                          title: LocaleKeys.paidConfirmRent,
                          details: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              AppText(invoice.propertyTitle),
                              AppText(invoice.reference),
                              AppText(
                                receipt.amount.display,
                                fontWeight: FontWeight.bold,
                              ),
                            ],
                          ),
                          actionLabel: LocaleKeys.paidPayRent,
                        );
                        if (confirmed &&
                            mounted &&
                            !await PremiumHostedData.open(
                              receipt.hostedUrl,
                              expiresAt: receipt.expiresAt,
                            )) {
                          PremiumFeedback.linkFailed();
                        }
                      },
                child: state.isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : AppText(LocaleKeys.paidPayRent),
              ),
            if (widget.capabilities.signedDocuments &&
                invoice.status.isPaid &&
                PremiumHostedData.httpsUri(invoice.receiptUrl) != null)
              OutlinedButton(
                onPressed: () async {
                  if (!await PremiumHostedData.open(invoice.receiptUrl)) {
                    PremiumFeedback.linkFailed();
                  }
                },
                child: AppText(LocaleKeys.paidViewReceipt),
              ),
            if (!widget.capabilities.rentCheckout &&
                !widget.workspace.isOwner &&
                invoice.status.isPayable)
              AppText(LocaleKeys.featureCheckoutUnavailable),
            if (state.isError && state.msg?.isNotEmpty == true)
              AppText(state.msg!, color: Theme.of(context).colorScheme.error),
            16.szH,
            OutlinedButton.icon(
              onPressed: widget.onRefresh,
              icon: const Icon(Icons.refresh),
              label: AppText(LocaleKeys.paidVerifyRent),
            ),
          ],
        );
      },
    ),
  );
}
