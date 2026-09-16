part of '../../imports.dart';

class TenantVisitsScreen extends StatefulWidget {
  const TenantVisitsScreen({super.key, this.initialVisits});

  final List<TenantVisitContent>? initialVisits;

  @override
  State<TenantVisitsScreen> createState() => _TenantVisitsScreenState();
}

class _TenantVisitsScreenState extends State<TenantVisitsScreen> {
  PagifyController<TenantVisitContent>? _pagifyController;
  late final List<TenantVisitContent>? _fixtureVisits;
  TenantVisitFilter _selectedFilter = TenantVisitFilter.all;

  @override
  void initState() {
    super.initState();
    final List<TenantVisitContent>? initialVisits = widget.initialVisits;
    _fixtureVisits = initialVisits == null
        ? null
        : List<TenantVisitContent>.of(initialVisits);
    if (_fixtureVisits == null) {
      _pagifyController = PagifyController<TenantVisitContent>();
    }
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
        return VisitRatingSheet(propertyTitle: visit.propertyTitle);
      },
    );

    if (submitted == true && mounted) {
      _showMessage(LocaleKeys.tenantVisitRatingSubmitted);
    }
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: AppText(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: TenantVisitsScreenContent(
          selectedFilter: _selectedFilter,
          initialVisits: _fixtureVisits,
          pagifyController: _pagifyController,
          onFilterSelected: _selectFilter,
          onVisitPressed: _openDetails,
          onRatePressed: _showRating,
          onCancelPressed: _removeVisit,
        ),
      ),
    );
  }
}
