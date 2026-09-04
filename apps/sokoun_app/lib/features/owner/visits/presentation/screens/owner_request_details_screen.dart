part of '../../imports.dart';

class OwnerRequestDetailsScreen extends StatefulWidget {
  const OwnerRequestDetailsScreen({super.key, required this.request});

  final OwnerVisitRequestContent request;

  @override
  State<OwnerRequestDetailsScreen> createState() =>
      _OwnerRequestDetailsScreenState();
}

class _OwnerRequestDetailsScreenState extends State<OwnerRequestDetailsScreen> {
  late final OwnerVisitStatusCubit _visitStatusCubit;
  OwnerVisitUpdateStatus? _pendingStatus;

  OwnerVisitRequestContent get request => widget.request;

  @override
  void initState() {
    super.initState();
    _visitStatusCubit = OwnerVisitStatusCubit();
  }

  @override
  void dispose() {
    _visitStatusCubit.close();
    super.dispose();
  }

  Future<void> _acceptRequest(BuildContext context) async {
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) => OwnerAcceptRequestSheet(request: request),
    );

    if (confirmed == true && context.mounted) {
      await _updateVisitStatus(
        status: OwnerVisitUpdateStatus.confirmed,
        resolution: OwnerRequestResolution.accepted,
      );
    }
  }

  Future<void> _rejectRequest(BuildContext context) async {
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
    await _visitStatusCubit.updateVisitStatus(
      visitId: request.id,
      status: status,
      onSuccess: () {
        if (mounted) Go.back(resolution);
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider<OwnerVisitStatusCubit>.value(
      value: _visitStatusCubit,
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
                        child: OwnerRequestDetailsContent(
                          request: request,
                          isAccepting:
                              isUpdating &&
                              _pendingStatus ==
                                  OwnerVisitUpdateStatus.confirmed,
                          isRejecting:
                              isUpdating &&
                              _pendingStatus == OwnerVisitUpdateStatus.rejected,
                          onAcceptPressed: () => _acceptRequest(context),
                          onRejectPressed: () => _rejectRequest(context),
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
