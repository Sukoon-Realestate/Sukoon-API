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
  final ValueNotifier<OwnerVisitUpdateStatus?> _pendingStatus =
      ValueNotifier<OwnerVisitUpdateStatus?>(null);

  @override
  void initState() {
    super.initState();
    _requestDetailsCubit = OwnerRequestDetailsCubit();
    _visitStatusCubit = OwnerVisitStatusCubit();
    _requestDetailsCubit.getRequestDetails(widget.requestId);
  }

  @override
  void dispose() {
    _requestDetailsCubit.close();
    _visitStatusCubit.close();
    _pendingStatus.dispose();
    super.dispose();
  }

  Future<void> _retryRequestDetails() async {
    final Future<void> request = _requestDetailsCubit.getRequestDetails(
      widget.requestId,
    );
    await request;
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
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) => const OwnerRejectRequestSheet(),
    );

    if (confirmed == true && context.mounted) {
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
    _pendingStatus.value = status;
    bool succeeded = false;
    void onSuccess() {
      succeeded = true;
      if (mounted) Go.back(resolution);
    }

    if (status == OwnerVisitUpdateStatus.confirmed) {
      await _visitStatusCubit.acceptVisitRequest(
        requestId: widget.requestId,
        onSuccess: onSuccess,
      );
    } else {
      await _visitStatusCubit.rejectVisitRequest(
        requestId: widget.requestId,
        onSuccess: onSuccess,
      );
    }
    if (!succeeded && mounted) _pendingStatus.value = null;
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
            child: AppScaffold(
              title: LocaleKeys.ownerRequestDetailsTitle,
              showBackButton: true,
              isBackEnabled: !isUpdating,
              backgroundColor: AppColors.scaffoldBackground,
              body: SafeArea(
                child: ValueListenableBuilder<OwnerVisitUpdateStatus?>(
                  valueListenable: _pendingStatus,
                  builder: (context, pendingStatus, _) =>
                      StatusBuilder<
                        OwnerRequestDetailsCubit,
                        OwnerVisitRequestDetailsContent
                      >.withShimmer(
                        initialDataForShimmer:
                            const OwnerVisitRequestDetailsContent.initial(),
                        onRetry: _retryRequestDetails,
                        builder: (request) => OwnerRequestDetailsContent(
                          request: request,
                          isAccepting:
                              isUpdating &&
                              pendingStatus == OwnerVisitUpdateStatus.confirmed,
                          isRejecting:
                              isUpdating &&
                              pendingStatus == OwnerVisitUpdateStatus.rejected,
                          onAcceptPressed: () =>
                              _acceptRequest(context, request),
                          onRejectPressed: () =>
                              _rejectRequest(context, request),
                        ),
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
