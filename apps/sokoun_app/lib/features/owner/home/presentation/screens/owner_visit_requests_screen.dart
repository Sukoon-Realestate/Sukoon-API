import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/owner/visits/presentation/cubits/received_visits_cubit.dart';

import '../widgets/owner_visit_requests/imports.dart';

class OwnerVisitRequestsScreen extends StatefulWidget {
  const OwnerVisitRequestsScreen({
    super.key,
    this.initialRequests,
    this.showBackButton = true,
  });

  final List<OwnerVisitRequestContent>? initialRequests;
  final bool showBackButton;

  @override
  State<OwnerVisitRequestsScreen> createState() =>
      _OwnerVisitRequestsScreenState();
}

class _OwnerVisitRequestsScreenState extends State<OwnerVisitRequestsScreen> {
  ReceivedVisitsCubit? _receivedVisitsCubit;
  Future<void>? _receivedVisitsRequest;
  late List<OwnerVisitRequestContent> _fixtureRequests;
  OwnerVisitRequestFilter _selectedFilter = OwnerVisitRequestFilter.all;

  List<OwnerVisitRequestContent> _visibleRequests(
    List<OwnerVisitRequestContent> requests,
  ) {
    return requests
        .where((request) => _selectedFilter.accepts(request.status))
        .toList(growable: false);
  }

  @override
  void initState() {
    super.initState();
    final List<OwnerVisitRequestContent>? initialRequests =
        widget.initialRequests;
    if (initialRequests == null) {
      final ReceivedVisitsCubit cubit = ReceivedVisitsCubit();
      _receivedVisitsCubit = cubit;
      _receivedVisitsRequest = cubit.getReceivedVisits();
    } else {
      _fixtureRequests = List<OwnerVisitRequestContent>.of(initialRequests);
    }
  }

  @override
  void dispose() {
    _receivedVisitsCubit?.close();
    super.dispose();
  }

  void _selectFilter(OwnerVisitRequestFilter filter) {
    setState(() => _selectedFilter = filter);
  }

  Future<void> _openDetails(OwnerVisitRequestContent request) async {
    final OwnerRequestResolution? resolution =
        await Go.to<OwnerRequestResolution>(
          OwnerRequestDetailsScreen(request: request),
        );
    if (resolution != null && mounted) {
      _resolveRequest(request: request, resolution: resolution);
    }
  }

  Future<void> _acceptRequest(OwnerVisitRequestContent request) async {
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) => OwnerAcceptRequestSheet(request: request),
    );
    if (confirmed == true && mounted) {
      _resolveRequest(
        request: request,
        resolution: OwnerRequestResolution.accepted,
      );
    }
  }

  Future<void> _rejectRequest(OwnerVisitRequestContent request) async {
    final OwnerRejectionReason? reason =
        await showModalBottomSheet<OwnerRejectionReason>(
          context: context,
          isScrollControlled: true,
          useSafeArea: true,
          backgroundColor: AppColors.transparent,
          barrierColor: AppColors.blackAlpha45,
          builder: (context) => const OwnerRejectRequestSheet(),
        );
    if (reason != null && mounted) {
      _resolveRequest(
        request: request,
        resolution: OwnerRequestResolution.rejected,
      );
    }
  }

  void _resolveRequest({
    required OwnerVisitRequestContent request,
    required OwnerRequestResolution resolution,
  }) {
    final OwnerVisitRequestContent updatedRequest = request.copyWith(
      status: resolution.isAccepted
          ? OwnerVisitRequestStatus.accepted
          : OwnerVisitRequestStatus.rejected,
    );
    final ReceivedVisitsCubit? cubit = _receivedVisitsCubit;
    if (cubit == null) {
      setState(() {
        _fixtureRequests = _fixtureRequests
            .map((item) => item.id == request.id ? updatedRequest : item)
            .toList(growable: false);
      });
    } else {
      cubit.replaceRequest(updatedRequest);
    }
    _showMessage(
      resolution.isAccepted
          ? LocaleKeys.ownerVisitAcceptedMessage
          : LocaleKeys.ownerVisitRejectedMessage,
    );
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: AppText(message)));
  }

  @override
  Widget build(BuildContext context) {
    final ReceivedVisitsCubit? cubit = _receivedVisitsCubit;
    if (cubit == null) {
      return _buildScreen(_fixtureRequests);
    }
    return BlocProvider.value(
      value: cubit,
      child:
          StatusBuilder<
            ReceivedVisitsCubit,
            List<OwnerVisitRequestContent>
          >.withShimmer(
            initialDataForShimmer: List<OwnerVisitRequestContent>.filled(
              3,
              OwnerVisitRequestContent.initial(),
            ),
            requestToTryAgainWhenError: _receivedVisitsRequest!,
            errorType: ErrorType.defaultView,
            emptyView: _buildScreen(const []),
            builder: _buildScreen,
          ),
    );
  }

  Widget _buildScreen(List<OwnerVisitRequestContent> requests) {
    final List<OwnerVisitRequestContent> visibleRequests = _visibleRequests(
      requests,
    );

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: OwnerVisitRequestsContent(
            requests: requests,
            visibleRequests: visibleRequests,
            selectedFilter: _selectedFilter,
            showBackButton: widget.showBackButton,
            onFilterSelected: _selectFilter,
            onRequestPressed: _openDetails,
            onAcceptPressed: _acceptRequest,
            onRejectPressed: _rejectRequest,
          ),
        ),
      ),
    );
  }
}
