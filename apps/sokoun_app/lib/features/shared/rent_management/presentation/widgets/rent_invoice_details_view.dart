import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_status_badge.dart';
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
  });
  final RentInvoice invoice;
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
    _cubit = RentCheckoutCubit();
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
    child: BlocBuilder<RentCheckoutCubit, AsyncState<PremiumActionReceipt>>(
      bloc: _cubit,
      builder: (context, state) {
        final invoice = widget.invoice;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppText(invoice.propertyTitle, fontWeight: FontWeight.bold),
            16.szH,
            AppText('${LocaleKeys.paidRentReference} ${invoice.reference}'),
            PremiumStatusBadge(status: invoice.status),
            AppText(
              invoice.amount.display,
              fontWeight: FontWeight.bold,
              fontSize: 24,
            ),
            if (invoice.dueDate != null)
              AppText(
                '${LocaleKeys.paidDueDate} ${invoice.dueDate!.toIso8601String().substring(0, 10)}',
              ),
            16.szH,
            AppText(LocaleKeys.paidInvoicesExplanation),
            if (invoice.canPay &&
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
            if (invoice.status.isPaid &&
                PremiumHostedData.httpsUri(invoice.receiptUrl) != null)
              OutlinedButton(
                onPressed: () async {
                  if (!await PremiumHostedData.open(invoice.receiptUrl)) {
                    PremiumFeedback.linkFailed();
                  }
                },
                child: AppText(LocaleKeys.paidViewReceipt),
              ),
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
