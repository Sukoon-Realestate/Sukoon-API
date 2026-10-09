part of '../../imports.dart';

class VisitDetailsScreen extends StatefulWidget {
  const VisitDetailsScreen({
    super.key,
    required this.visit,
    this.openReview = false,
  });
  final TenantVisitContent visit;
  final bool openReview;
  @override
  State<VisitDetailsScreen> createState() => _VisitDetailsScreenState();
}

class _VisitDetailsScreenState extends State<VisitDetailsScreen> {
  late final VisitDetailsCubit _detailsCubit;
  late final VisitCancelCubit _cancelCubit;
  bool _reviewOpen = false;
  @override
  void initState() {
    super.initState();
    _detailsCubit = VisitDetailsCubit();
    _cancelCubit = VisitCancelCubit();
    unawaited(_loadDetails());
  }

  Future<void> _loadDetails() async {
    await _detailsCubit.load(widget.visit.id);
    if (!mounted ||
        !widget.openReview ||
        !_detailsCubit.state.isSuccess ||
        _detailsCubit.data.visit.id != widget.visit.id) {
      return;
    }
    await WidgetsBinding.instance.endOfFrame;
    if (!mounted) return;
    if (_detailsCubit.data.visit.canReview &&
        _detailsCubit.data.review == null) {
      await _review();
    } else {
      Messages.showToast(
        msg: LocaleKeys.professionalUnavailableDestination,
        status: BaseStatus.error,
      );
    }
  }

  @override
  void dispose() {
    _detailsCubit.close();
    _cancelCubit.close();
    super.dispose();
  }

  Future<void> _cancel() async {
    final visit = _detailsCubit.data.visit;
    if (!visit.canCancel ||
        !await VisitCancellationDialog.confirm(context, visit) ||
        !mounted) {
      return;
    }
    if (await _cancelCubit.cancel(visit.id) && mounted) Go.back(visit.canceled);
  }

  Future<void> _review() async {
    final TenantVisitContent visit = _detailsCubit.data.visit;
    if (_reviewOpen || !visit.canReview || _detailsCubit.data.review != null) {
      return;
    }
    _reviewOpen = true;
    bool? submitted;
    try {
      submitted = await showModalBottomSheet<bool>(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        builder: (_) => VisitRatingSheet(
          visitId: visit.id,
          propertyTitle: visit.propertyTitle,
        ),
      );
    } finally {
      _reviewOpen = false;
    }
    if (submitted == true && mounted) {
      WorkspaceCountsRefreshBus.refresh();
      await _detailsCubit.load(widget.visit.id);
    }
  }

  @override
  Widget build(BuildContext context) => MultiBlocProvider(
    providers: [
      BlocProvider.value(value: _detailsCubit),
      BlocProvider.value(value: _cancelCubit),
    ],
    child: AppScaffold(
      title: LocaleKeys.tenantVisitDetailsTitle,
      showBackButton: true,
      body: VisitContactRefresh(
        visitId: widget.visit.id,
        onRefresh: () => _detailsCubit.refresh(widget.visit.id),
        child: SafeArea(
          child:
              StatusBuilder<
                VisitDetailsCubit,
                TenantVisitDetailsContent
              >.withShimmer(
                initialDataForShimmer:
                    const TenantVisitDetailsContent.initial(),
                onRetry: () => _detailsCubit.load(widget.visit.id),
                builder: (details) => VisitDetailsContent(
                  visit: details.visit,
                  details: details,
                  onCancel: _cancel,
                  onReview: _review,
                ),
              ),
        ),
      ),
    ),
  );
}
