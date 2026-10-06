part of '../../imports.dart';

class VisitDetailsScreen extends StatefulWidget {
  const VisitDetailsScreen({super.key, required this.visit});
  final TenantVisitContent visit;
  @override
  State<VisitDetailsScreen> createState() => _VisitDetailsScreenState();
}

class _VisitDetailsScreenState extends State<VisitDetailsScreen> {
  late final VisitDetailsCubit _detailsCubit;
  late final VisitCancelCubit _cancelCubit;
  @override
  void initState() {
    super.initState();
    _detailsCubit = VisitDetailsCubit();
    _cancelCubit = VisitCancelCubit();
    _detailsCubit.load(widget.visit.id);
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
    if (!visit.canReview || _detailsCubit.data.review != null) return;
    final bool? submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (_) => VisitRatingSheet(
        visitId: visit.id,
        propertyTitle: visit.propertyTitle,
      ),
    );
    if (submitted == true && mounted) await _detailsCubit.load(widget.visit.id);
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
      body: SafeArea(
        child:
            StatusBuilder<
              VisitDetailsCubit,
              TenantVisitDetailsContent
            >.withShimmer(
              initialDataForShimmer: const TenantVisitDetailsContent.initial(),
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
  );
}
