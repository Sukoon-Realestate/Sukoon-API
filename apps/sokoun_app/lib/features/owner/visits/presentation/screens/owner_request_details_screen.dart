part of '../../imports.dart';

class OwnerRequestDetailsScreen extends StatefulWidget {
  const OwnerRequestDetailsScreen({super.key, required this.requestId});

  final String requestId;

  @override
  State<OwnerRequestDetailsScreen> createState() =>
      _OwnerRequestDetailsScreenState();
}

class _OwnerRequestDetailsScreenState extends State<OwnerRequestDetailsScreen> {
  late final OwnerRequestDetailsCubit _requestDetailsCubit;
  late final OwnerVisitStatusCubit _visitStatusCubit;
  late final Future<void> _requestDetailsRequest;
  OwnerVisitUpdateStatus? _pendingStatus;

  @override
  void initState() {
    super.initState();
    _requestDetailsCubit = OwnerRequestDetailsCubit();
    _visitStatusCubit = OwnerVisitStatusCubit();
    _requestDetailsRequest = _requestDetailsCubit.getRequestDetails(
      widget.requestId,
    );
  }

  @override
  void dispose() {
    _requestDetailsCubit.close();
    _visitStatusCubit.close();
    super.dispose();
  }

  Future<void> _acceptRequest(
    BuildContext context,
    OwnerVisitRequestDetailsContent request,
  ) async {
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) =>
          OwnerAcceptRequestSheet(request: request.toRequestContent()),
    );

    if (confirmed == true && context.mounted) {
      await _updateVisitStatus(
        status: OwnerVisitUpdateStatus.confirmed,
        resolution: OwnerRequestResolution.accepted,
      );
    }
  }

  Future<void> _rejectRequest(
    BuildContext context,
    OwnerVisitRequestDetailsContent request,
  ) async {
    final OwnerRejectionReason? reason =
        await showModalBottomSheet<OwnerRejectionReason>(
          context: context,
          isScrollControlled: true,
          useSafeArea: true,
          backgroundColor: AppColors.transparent,
          barrierColor: AppColors.blackAlpha45,
          builder: (context) => const OwnerRejectRequestSheet(),
        );

    if (reason != null && context.mounted) {
      await _updateVisitStatus(
        status: OwnerVisitUpdateStatus.rejected,
        resolution: OwnerRequestResolution.rejected,
      );
    }
  }

  Future<void> _updateVisitStatus({
    required OwnerVisitUpdateStatus status,
    required OwnerRequestResolution resolution,
  }) async {
    if (_visitStatusCubit.isLoading) return;
    setState(() => _pendingStatus = status);
    void onSuccess() {
      if (mounted) Go.back(resolution);
    }

    if (status == OwnerVisitUpdateStatus.confirmed) {
      await _visitStatusCubit.acceptVisitRequest(
        requestId: widget.requestId,
        onSuccess: onSuccess,
      );
      return;
    }
    await _visitStatusCubit.rejectVisitRequest(
      requestId: widget.requestId,
      onSuccess: onSuccess,
    );
  }

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<OwnerRequestDetailsCubit>.value(
          value: _requestDetailsCubit,
        ),
        BlocProvider<OwnerVisitStatusCubit>.value(value: _visitStatusCubit),
      ],
      child: BlocBuilder<OwnerVisitStatusCubit, AsyncState<bool>>(
        builder: (context, state) {
          final bool isUpdating = state.isLoading;
          return PopScope(
            canPop: !isUpdating,
            child: Directionality(
              textDirection: TextDirection.rtl,
              child: Scaffold(
                backgroundColor: AppColors.scaffoldBackground,
                body: SafeArea(
                  child: Column(
                    children: [
                      VisitHeader(
                        title: LocaleKeys.ownerRequestDetailsTitle,
                        backKey: const ValueKey('owner-request-details-back'),
                        isBackEnabled: !isUpdating,
                      ),
                      Expanded(
                        child:
                            StatusBuilder<
                              OwnerRequestDetailsCubit,
                              OwnerVisitRequestDetailsContent
                            >.withShimmer(
                              initialDataForShimmer:
                                  const OwnerVisitRequestDetailsContent.initial(),
                              requestToTryAgainWhenError:
                                  _requestDetailsRequest,
                              errorType: ErrorType.defaultView,
                              builder: (request) => OwnerRequestDetailsContent(
                                request: request,
                                isAccepting:
                                    isUpdating &&
                                    _pendingStatus ==
                                        OwnerVisitUpdateStatus.confirmed,
                                isRejecting:
                                    isUpdating &&
                                    _pendingStatus ==
                                        OwnerVisitUpdateStatus.rejected,
                                onAcceptPressed: () =>
                                    _acceptRequest(context, request),
                                onRejectPressed: () =>
                                    _rejectRequest(context, request),
                              ),
                            ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
