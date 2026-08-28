import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_thread_screen.dart';
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

  int _pendingCount(List<OwnerVisitRequestContent> requests) =>
      requests.where((request) => request.status.canDecide).length;

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

  int _countForFilter(
    List<OwnerVisitRequestContent> requests,
    OwnerVisitRequestFilter filter,
  ) {
    return requests.where((request) => filter.accepts(request.status)).length;
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

  void _openChat(OwnerVisitRequestContent request) {
    Go.to(
      ChatThreadScreen(
        conversation: ConversationContent(
          id: 101,
          name: request.name,
          property: request.property,
          lastMessage: request.tenantNote,
          time: request.time,
          unreadCount: 0,
          isVerified: request.isVerified,
          isOnline: true,
        ),
      ),
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              OwnerVisitRequestsTopBar(
                onBackPressed: widget.showBackButton ? () => Go.back() : null,
                onCalendarPressed: () =>
                    Go.to(const OwnerRequestsCalendarScreen()),
              ),
              Container(
                padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 14.h),
                decoration: const BoxDecoration(
                  color: AppColors.white,
                  border: Border(bottom: BorderSide(color: AppColors.grayPale)),
                ),
                child: Column(
                  children: [
                    OwnerVisitRequestSummaryGrid(
                      totalCount: requests.length,
                      pendingCount: _pendingCount(requests),
                    ),
                    12.szH,
                    OwnerVisitRequestFilters(
                      filters: OwnerVisitRequestFilter.values,
                      selectedFilter: _selectedFilter,
                      countForFilter: (filter) =>
                          _countForFilter(requests, filter),
                      onFilterSelected: _selectFilter,
                    ),
                  ],
                ),
              ),
              Expanded(
                child: visibleRequests.isEmpty
                    ? Center(
                        child: AppText(
                          LocaleKeys.ownerVisitsNoRequests,
                          color: AppColors.sokoonGray,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w700,
                        ),
                      )
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 20.h),
                        itemBuilder: (context, index) {
                          final OwnerVisitRequestContent request =
                              visibleRequests[index];
                          return OwnerVisitRequestCard(
                            request: request,
                            onPressed: () => _openDetails(request),
                            onChatPressed: () => _openChat(request),
                            onAcceptPressed: () => _acceptRequest(request),
                            onRejectPressed: () => _rejectRequest(request),
                          );
                        },
                        separatorBuilder: (context, index) => 12.szH,
                        itemCount: visibleRequests.length,
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
