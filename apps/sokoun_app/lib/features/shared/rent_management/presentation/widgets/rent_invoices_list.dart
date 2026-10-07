import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/models/rent_invoice.dart';
import '../../data/rent_management_data.dart';
import 'rent_invoice_card.dart';
import 'rent_invoices_empty_state.dart';

class RentInvoicesList extends StatefulWidget {
  const RentInvoicesList({
    super.key,
    required this.workspace,
    this.leaseId = '',
    this.propertyTitle = '',
  });
  final AppWorkspace workspace;
  final String leaseId;
  final String propertyTitle;
  @override
  State<RentInvoicesList> createState() => _RentInvoicesListState();
}

class _RentInvoicesListState extends State<RentInvoicesList> {
  final PagifyController<RentInvoice> _controller = PagifyController();
  @override
  Widget build(BuildContext context) => AppPagify<RentInvoice>(
    pagifyController: _controller,
    enablePullRefresh: true,
    header: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (widget.propertyTitle.isNotEmpty)
            AppText(widget.propertyTitle, fontWeight: FontWeight.bold),
          AppText(LocaleKeys.paidInvoicesExplanation),
        ],
      ),
    ),
    cacheKey: RentManagementData.cacheKey(
      widget.workspace,
      leaseId: widget.leaseId,
    ),
    cacheToJson: (invoice) => invoice.toJson(),
    cacheFromJson: RentInvoice.fromJson,
    asyncCall: (_, page) => RentManagementData.getPage(
      page: page,
      workspace: widget.workspace,
      leaseId: widget.leaseId,
    ),
    emptyListView: const RentInvoicesEmptyState(),
    itemBuilder: (_, __, ___, invoice) => RentInvoiceCard(
      key: ValueKey(invoice.id),
      invoice: invoice,
      workspace: widget.workspace,
      onReturned: _controller.refresh,
    ),
  );
}
