import 'package:melos_core/core/extensions/widget_extension.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
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
  // Filter and request mutations recompose the header, actions, and list.
  static List<OwnerVisitRequestContent> get _shimmerRequests => [
    OwnerVisitRequestContent(
      id: 'shimmer-request-1',
      initial: LocaleKeys.ownerVisitTenantMohamedInitial,
      name: LocaleKeys.ownerVisitTenantMohamed,
      property: LocaleKeys.ownerVisitPropertyNasrCity,
      dateLabel: LocaleKeys.ownerVisitDateSaturdayAtThree,
      detailDate: '',
      time: '',
      memberSince: '',
      tenantNote: '',
      phone: '',
      status: OwnerVisitRequestStatus.pending,
      isVerified: true,
    ),
    OwnerVisitRequestContent(
      id: 'shimmer-request-2',
      initial: LocaleKeys.ownerVisitTenantSaraInitial,
      name: LocaleKeys.ownerVisitTenantSara,
      property: LocaleKeys.ownerVisitPropertyJeddahStudio,
      dateLabel: LocaleKeys.ownerVisitDateSundayAtTwo,
      detailDate: '',
      time: '',
      memberSince: '',
      tenantNote: '',
      phone: '',
      status: OwnerVisitRequestStatus.pending,
      isVerified: false,
    ),
    OwnerVisitRequestContent(
      id: 'shimmer-request-3',
      initial: LocaleKeys.ownerVisitTenantKhaledInitial,
      name: LocaleKeys.ownerVisitTenantKhaled,
      property: LocaleKeys.ownerVisitPropertyDammamRoom,
      dateLabel: LocaleKeys.ownerVisitDateMondayAtEleven,
      detailDate: '',
      time: '',
      memberSince: '',
      tenantNote: '',
      phone: '',
      status: OwnerVisitRequestStatus.pending,
      isVerified: true,
    ),
  ];

  ReceivedVisitsCubit? _receivedVisitsCubit;
  late final OwnerVisitStatusCubit _visitStatusCubit;
  late List<OwnerVisitRequestContent> _fixtureRequests;
  OwnerVisitRequestFilter _selectedFilter = OwnerVisitRequestFilter.all;
  String? _updatingRequestId;
  OwnerVisitUpdateStatus? _pendingStatus;

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
    _visitStatusCubit = OwnerVisitStatusCubit();
    final List<OwnerVisitRequestContent>? initialRequests =
        widget.initialRequests;
    if (initialRequests == null) {
      final ReceivedVisitsCubit cubit = ReceivedVisitsCubit();
      _receivedVisitsCubit = cubit;
      cubit.getReceivedVisits();
    } else {
      _fixtureRequests = List<OwnerVisitRequestContent>.of(initialRequests);
    }
  }

  @override
  void dispose() {
    _receivedVisitsCubit?.close();
    _visitStatusCubit.close();
    super.dispose();
  }

  Future<void> _retryRequests() async {
    final ReceivedVisitsCubit? cubit = _receivedVisitsCubit;
    if (cubit == null) return;
    final Future<void> request = cubit.getReceivedVisits();
    await request;
  }

  void _selectFilter(OwnerVisitRequestFilter filter) {
    setState(() => _selectedFilter = filter);
  }

  Future<void> _openDetails(OwnerVisitRequestContent request) async {
    final OwnerRequestResolution? resolution =
        await Go.to<OwnerRequestResolution>(
          OwnerRequestDetailsScreen(requestId: request.id),
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
    setState(() {
      _updatingRequestId = request.id;
      _pendingStatus = status;
    });

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
    setState(() {
      _updatingRequestId = null;
      _pendingStatus = null;
    });
    if (succeeded) {
      _resolveRequest(request: request, resolution: resolution);
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
      ..showSnackBar(
        SnackBar(content: AppText(message, style: AppTextStyles.regular)),
      );
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
                initialDataForShimmer: _shimmerRequests,
                onRetry: _retryRequests,
                emptyView: _buildScreen(const []),
                builder: _buildScreen,
              )
              .withPullRefresher(
                onRefresh: () async {
                  if (_updatingRequestId != null) return;
                  await _retryRequests();
                },
              ),
    );
  }

  Widget _buildScreen(List<OwnerVisitRequestContent> requests) {
    final List<OwnerVisitRequestContent> visibleRequests = _visibleRequests(
      requests,
    );

    return AppScaffold(
      title: LocaleKeys.ownerVisitsTitle,
      showBackButton: widget.showBackButton,
      actions: [
        IconButton(
          tooltip: LocaleKeys.ownerCalendarTitle,
          onPressed: () => Go.to(
            OwnerRequestsCalendarScreen(
              ownerPropertyId:
                  requests
                      .where((request) => request.propertyId.trim().isNotEmpty)
                      .firstOrNull
                      ?.propertyId ??
                  '',
            ),
          ),
          icon: const Icon(Icons.calendar_month_outlined),
        ),
      ],
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: OwnerVisitRequestsContent(
          requests: requests,
          visibleRequests: visibleRequests,
          selectedFilter: _selectedFilter,
          onFilterSelected: _selectFilter,
          onRequestPressed: _openDetails,
          onAcceptPressed: _acceptRequest,
          onRejectPressed: _rejectRequest,
          updatingRequestId: _updatingRequestId,
          pendingStatus: _pendingStatus,
        ),
      ),
    );
  }
}
