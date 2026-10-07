import 'package:flutter/material.dart';
import 'package:pagify/pagify.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/digital_leases_data.dart';
import '../../data/models/digital_lease.dart';
import '../screens/lease_draft_screen.dart';
import 'digital_leases_empty_state.dart';
import 'digital_lease_card.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';

class DigitalLeasesList extends StatefulWidget {
  const DigitalLeasesList({super.key, required this.workspace, this.property});
  final AppWorkspace workspace;
  final OwnerPropertyContent? property;
  @override
  State<DigitalLeasesList> createState() => _DigitalLeasesListState();
}

class _DigitalLeasesListState extends State<DigitalLeasesList> {
  final PagifyController<DigitalLease> _controller = PagifyController();
  @override
  Widget build(BuildContext context) => AppPagify<DigitalLease>(
    pagifyController: _controller,
    enablePullRefresh: true,
    header: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (widget.property != null)
            AppText(widget.property!.title, fontWeight: FontWeight.bold),
          AppText(LocaleKeys.paidLeasesExplanation),
          if (widget.workspace.isOwner)
            FilledButton.icon(
              onPressed: () async {
                final lease = await Go.to<DigitalLease>(
                  LeaseDraftScreen(property: widget.property),
                );
                if (lease != null && mounted) _controller.refresh();
              },
              icon: const Icon(Icons.add),
              label: AppText(LocaleKeys.paidCreateLease),
            ),
        ],
      ),
    ),
    cacheKey: DigitalLeasesData.cacheKey(
      widget.workspace,
      propertyId: widget.property?.id ?? '',
    ),
    cacheToJson: (lease) => lease.toJson(),
    cacheFromJson: DigitalLease.fromJson,
    asyncCall: (_, page) => DigitalLeasesData.getPage(
      page: page,
      workspace: widget.workspace,
      propertyId: widget.property?.id ?? '',
    ),
    emptyListView: const DigitalLeasesEmptyState(),
    itemBuilder: (_, __, ___, lease) => DigitalLeaseCard(
      key: ValueKey(lease.id),
      lease: lease,
      workspace: widget.workspace,
      onReturned: _controller.refresh,
    ),
  );
}
