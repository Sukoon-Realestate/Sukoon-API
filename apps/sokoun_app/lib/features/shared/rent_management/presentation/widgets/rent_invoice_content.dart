import 'rent_invoices_empty_state.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import '../../data/models/rent_invoice.dart';
import '../cubits/rent_invoice_cubit.dart';
import 'rent_invoice_details_view.dart';

class RentInvoiceContent extends StatefulWidget {
  const RentInvoiceContent({super.key, required this.invoiceId});
  final String invoiceId;
  @override
  State<RentInvoiceContent> createState() => _RentInvoiceContentState();
}

class _RentInvoiceContentState extends State<RentInvoiceContent> {
  late final RentInvoiceCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = RentInvoiceCubit();
    _request = _load();
  }

  Future<void> _load() => _cubit.load(widget.invoiceId);
  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<RentInvoiceCubit, RentInvoice>(
        cubit: _cubit,
        request: _request,
        initialData: const RentInvoice.initial(),
        onRetry: _load,
        builder: (invoice) => invoice.id.isEmpty
            ? const RentInvoicesEmptyState()
            : RentInvoiceDetailsView(
                invoice: invoice,
                isFresh: !_cubit.isCached,
                onRefresh: _load,
              ),
      );
}
