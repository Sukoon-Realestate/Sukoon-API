import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:pagify/pagify.dart';

import '../widgets/owner_visit_requests/imports.dart';

class OwnerVisitRequestsScreen extends StatefulWidget {
  const OwnerVisitRequestsScreen({
    super.key,
    this.initialRequests,
    this.showBackButton = true,
    this.useRequestEndpoint = true,
  });

  final List<OwnerVisitRequestContent>? initialRequests;
  final bool showBackButton;
  final bool useRequestEndpoint;

  @override
  State<OwnerVisitRequestsScreen> createState() =>
      _OwnerVisitRequestsScreenState();
}

class _OwnerVisitRequestsScreenState extends State<OwnerVisitRequestsScreen> {
  late final PagifyController<OwnerVisitRequestContent> _pagifyController;
  late final OwnerVisitStatusCubit _visitStatusCubit;
  late final ValueNotifier<
    ({OwnerVisitRequestFilter filter, List<OwnerVisitRequestContent>? requests})
  >
  _view;
  final ValueNotifier<({String? requestId, OwnerVisitUpdateStatus? status})>
  _progress = ValueNotifier((requestId: null, status: null));
  String? get _updatingRequestId => _progress.value.requestId;

  @override
  void initState() {
    super.initState();
    _visitStatusCubit = OwnerVisitStatusCubit();
    _pagifyController = PagifyController<OwnerVisitRequestContent>();
    final List<OwnerVisitRequestContent>? initialRequests =
        widget.initialRequests;
    _view = ValueNotifier((
      filter: OwnerVisitRequestFilter.all,
      requests: initialRequests == null
          ? null
          : List<OwnerVisitRequestContent>.of(initialRequests),
    ));
  }

  @override
  void dispose() {
    _pagifyController.dispose();
    _view.dispose();
    _visitStatusCubit.close();
    _progress.dispose();
    super.dispose();
  }

  void _selectFilter(OwnerVisitRequestFilter filter) {
    if (filter.isSame(_view.value.filter)) return;
    _view.value = (filter: filter, requests: _view.value.requests);
    if (_view.value.requests != null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted || !filter.isSame(_view.value.filter)) return;
      await _pagifyController.refresh();
    });
  }

  Future<void> _openDetails(OwnerVisitRequestContent request) async {
    final OwnerRequestResolution? resolution =
        await Go.to<OwnerRequestResolution>(
          OwnerRequestDetailsScreen(
            requestId: request.id,
            useVisitEndpoint: !widget.useRequestEndpoint,
          ),
        );
    if (resolution != null && mounted) {
      _resolveRequest(request: request, resolution: resolution);
    } else if (mounted && _view.value.requests == null) {
      await _pagifyController.refresh();
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
      await _updateRequestStatus(
        request: request,
        status: OwnerVisitUpdateStatus.confirmed,
        resolution: OwnerRequestResolution.accepted,
      );
    }
  }

  Future<void> _rejectRequest(OwnerVisitRequestContent request) async {
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) => const OwnerRejectRequestSheet(),
    );
    if (confirmed == true && mounted) {
      await _updateRequestStatus(
        request: request,
        status: OwnerVisitUpdateStatus.rejected,
        resolution: OwnerRequestResolution.rejected,
      );
    }
  }

  Future<void> _updateRequestStatus({
    required OwnerVisitRequestContent request,
    required OwnerVisitUpdateStatus status,
    required OwnerRequestResolution resolution,
  }) async {
    if (_updatingRequestId != null || _visitStatusCubit.isLoading) return;
    _progress.value = (requestId: request.id, status: status);

    bool succeeded = false;
    void onSuccess() => succeeded = true;
    if (status == OwnerVisitUpdateStatus.confirmed) {
      await _visitStatusCubit.acceptVisitRequest(
        requestId: request.id,
        onSuccess: onSuccess,
      );
    } else {
      await _visitStatusCubit.rejectVisitRequest(
        requestId: request.id,
        onSuccess: onSuccess,
      );
    }

    if (!mounted) return;
    _progress.value = (requestId: null, status: null);
    if (succeeded) {
      _resolveRequest(request: request, resolution: resolution);
      if (resolution.isAccepted) await _openDetails(request);
    }
  }

  void _resolveRequest({
    required OwnerVisitRequestContent request,
    required OwnerRequestResolution resolution,
  }) {
    final OwnerVisitRequestContent updatedRequest = request.copyWith(
      statusLabel: '',
      status: resolution.isAccepted
          ? OwnerVisitRequestStatus.accepted
          : OwnerVisitRequestStatus.rejected,
    );
    final List<OwnerVisitRequestContent>? fixtures = _view.value.requests;
    if (fixtures != null) {
      _view.value = (
        filter: _view.value.filter,
        requests: fixtures
            .map((item) => item.id == request.id ? updatedRequest : item)
            .toList(growable: false),
      );
    } else {
      final int index = _pagifyController.items.indexWhere(
        (item) => item.id == request.id,
      );
      if (index >= 0) _pagifyController.replaceWith(index, updatedRequest);
      _pagifyController.refresh();
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.ownerVisitsTitle,
      showBackButton: widget.showBackButton,
      actions: [
        IconButton(
          tooltip: LocaleKeys.ownerCalendarTitle,
          onPressed: () => Go.to(const OwnerRequestsCalendarScreen()),
          icon: const Icon(Icons.calendar_month_outlined),
        ),
      ],
      backgroundColor: context.appColor(
        AppColors.scaffoldBackground,
        surface: true,
      ),
      body: SafeArea(
        child:
            ValueListenableBuilder<
              ({
                OwnerVisitRequestFilter filter,
                List<OwnerVisitRequestContent>? requests,
              })
            >(
              valueListenable: _view,
              builder: (context, view, _) => OwnerVisitRequestsContent(
                initialRequests: view.requests,
                pagifyController: _pagifyController,
                useRequestEndpoint: widget.useRequestEndpoint,
                selectedFilter: view.filter,
                onFilterSelected: _selectFilter,
                onRequestPressed: _openDetails,
                onAcceptPressed: _acceptRequest,
                onRejectPressed: _rejectRequest,
                progress: _progress,
              ),
            ),
      ),
    );
  }
}
