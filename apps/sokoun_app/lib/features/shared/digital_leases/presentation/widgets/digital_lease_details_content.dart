import 'digital_leases_empty_state.dart';
import 'package:flutter/material.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import '../../data/models/digital_lease.dart';
import '../cubits/digital_lease_details_cubit.dart';
import 'digital_lease_details_view.dart';

class DigitalLeaseDetailsContent extends StatefulWidget {
  const DigitalLeaseDetailsContent({super.key, required this.leaseId});
  final String leaseId;
  @override
  State<DigitalLeaseDetailsContent> createState() =>
      _DigitalLeaseDetailsContentState();
}

class _DigitalLeaseDetailsContentState
    extends State<DigitalLeaseDetailsContent> {
  late final DigitalLeaseDetailsCubit _cubit;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _cubit = DigitalLeaseDetailsCubit();
    _request = _load();
  }

  Future<void> _load() => _cubit.load(widget.leaseId);
  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      PremiumRemoteView<DigitalLeaseDetailsCubit, DigitalLease>(
        cubit: _cubit,
        request: _request,
        initialData: const DigitalLease.initial(),
        onRetry: _load,
        builder: (lease) => lease.id.isEmpty
            ? const DigitalLeasesEmptyState()
            : DigitalLeaseDetailsView(
                lease: lease,
                isFresh: !_cubit.isCached,
                onRefresh: _load,
              ),
      );
}
