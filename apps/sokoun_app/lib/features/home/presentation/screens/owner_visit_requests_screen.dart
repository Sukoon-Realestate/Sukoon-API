import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/chat/data/models/chat_content.dart';
import 'package:sokoun_app/features/chat/presentation/screens/chat_thread_screen.dart';
import 'package:sokoun_app/features/visits/imports.dart';

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
  late List<OwnerVisitRequestContent> _requests;
  OwnerVisitRequestFilter _selectedFilter = OwnerVisitRequestFilter.all;

  List<OwnerVisitRequestContent> get _visibleRequests {
    return _requests
        .where((request) => _selectedFilter.accepts(request.status))
        .toList(growable: false);
  }

  int get _pendingCount =>
      _requests.where((request) => request.status.canDecide).length;

  @override
  void initState() {
    super.initState();
    _requests = List<OwnerVisitRequestContent>.of(
      widget.initialRequests ?? OwnerVisitRequestsContent.requests,
    );
  }

  int _countForFilter(OwnerVisitRequestFilter filter) {
    return _requests.where((request) => filter.accepts(request.status)).length;
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
    final int index = _requests.indexWhere((item) => item.id == request.id);
    if (index < 0) {
      return;
    }

    setState(() {
      _requests[index] = request.copyWith(
        status: resolution.isAccepted
            ? OwnerVisitRequestStatus.accepted
            : OwnerVisitRequestStatus.rejected,
      );
    });
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
    final List<OwnerVisitRequestContent> visibleRequests = _visibleRequests;

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
                      totalCount: _requests.length,
                      pendingCount: _pendingCount,
                    ),
                    12.szH,
                    OwnerVisitRequestFilters(
                      filters: OwnerVisitRequestFilter.values,
                      selectedFilter: _selectedFilter,
                      countForFilter: _countForFilter,
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
