part of '../../imports.dart';

class TenantVisitsScreen extends StatefulWidget {
  const TenantVisitsScreen({
    super.key,
    this.initialVisits,
    this.useRequestEndpoint = true,
  });

  final List<TenantVisitContent>? initialVisits;
  final bool useRequestEndpoint;

  @override
  State<TenantVisitsScreen> createState() => _TenantVisitsScreenState();
}

class _TenantVisitsScreenState extends State<TenantVisitsScreen> {
  // Filter and fixture mutations replace the filters and visit list together.
  PagifyController<TenantVisitContent>? _pagifyController;
  late final List<TenantVisitContent>? _fixtureVisits;
  late final VisitCancelCubit _cancelCubit;
  TenantVisitFilter _selectedFilter = TenantVisitFilter.all;

  @override
  void initState() {
    super.initState();
    _cancelCubit = VisitCancelCubit();
    final List<TenantVisitContent>? initialVisits = widget.initialVisits;
    _fixtureVisits = initialVisits == null
        ? null
        : List<TenantVisitContent>.of(initialVisits);
    if (_fixtureVisits == null) {
      _pagifyController = PagifyController<TenantVisitContent>();
    }
  }

  @override
  void dispose() {
    _cancelCubit.close();
    super.dispose();
  }

  void _selectFilter(TenantVisitFilter filter) {
    if (filter.isSame(_selectedFilter)) return;
    setState(() => _selectedFilter = filter);

    final PagifyController<TenantVisitContent>? controller = _pagifyController;
    if (controller == null) return;
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      if (!mounted) return;
      await controller.refresh();
    });
  }

  Future<void> _openDetails(TenantVisitContent visit) async {
    final bool? canceled = await Go.to<bool>(VisitDetailsScreen(visit: visit));
    if (canceled == true && mounted) _removeVisit(visit);
  }

  Future<void> _cancelVisit(TenantVisitContent visit) async {
    if (!visit.canCancel) return;
    if (await _cancelCubit.cancel(visit.id) && mounted) _removeVisit(visit);
  }

  void _removeVisit(TenantVisitContent visit) {
    final List<TenantVisitContent>? fixtureVisits = _fixtureVisits;
    if (fixtureVisits != null) {
      setState(() {
        fixtureVisits.removeWhere((item) => item.id == visit.id);
      });
    } else {
      _pagifyController?.removeWhere((item) => item.id == visit.id);
    }
    _showMessage(LocaleKeys.tenantVisitRequestCanceled);
  }

  Future<void> _showRating(TenantVisitContent visit) async {
    final bool? submitted = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha50,
      builder: (context) {
        return VisitRatingSheet(
          visitId: visit.id,
          propertyTitle: visit.propertyTitle,
        );
      },
    );

    if (submitted == true && mounted) {
      _showMessage(LocaleKeys.tenantVisitRatingSubmitted);
      await _pagifyController?.refresh();
    }
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
    return AppScaffold(
      title: LocaleKeys.tenantVisitsTitle,
      showBackButton: true,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: TenantVisitsScreenContent(
          useRequestEndpoint: widget.useRequestEndpoint,
          selectedFilter: _selectedFilter,
          initialVisits: _fixtureVisits,
          pagifyController: _pagifyController,
          onFilterSelected: _selectFilter,
          onVisitPressed: _openDetails,
          onRatePressed: _showRating,
          onCancelPressed: _cancelVisit,
        ),
      ),
    );
  }
}
