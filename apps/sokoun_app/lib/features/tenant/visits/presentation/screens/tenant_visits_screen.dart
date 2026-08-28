part of '../../imports.dart';

class TenantVisitsScreen extends StatefulWidget {
  const TenantVisitsScreen({super.key, this.initialVisits});

  final List<TenantVisitContent>? initialVisits;

  @override
  State<TenantVisitsScreen> createState() => _TenantVisitsScreenState();
}

class _TenantVisitsScreenState extends State<TenantVisitsScreen> {
  late List<TenantVisitContent> _visits;
  TenantVisitFilter _selectedFilter = TenantVisitFilter.all;

  List<TenantVisitFilter> get _filters => TenantVisitFilter.values;

  List<TenantVisitContent> get _visibleVisits {
    return _visits
        .where((visit) => _selectedFilter.accepts(visit.status))
        .toList(growable: false);
  }

  @override
  void initState() {
    super.initState();
    _visits = List<TenantVisitContent>.of(
      widget.initialVisits ?? TenantVisitsContent.visits,
    );
  }

  void _selectFilter(TenantVisitFilter filter) {
    setState(() => _selectedFilter = filter);
  }

  Future<void> _openDetails(TenantVisitContent visit) async {
    if (!visit.status.isAccepted) {
      return;
    }

    final bool? canceled = await Go.to<bool>(VisitDetailsScreen(visit: visit));
    if (canceled == true && mounted) {
      _removeVisit(visit);
    }
  }

  void _removeVisit(TenantVisitContent visit) {
    setState(() {
      _visits.removeWhere((item) => item.id == visit.id);
    });
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
          propertyTitle: visit.propertyTitle,
          onSubmitted: (rating, comment) => Go.back(true),
        );
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

  void _openChat() {
    Go.to(ChatThreadScreen(conversation: ChatContent.conversations.first));
  }

  @override
  Widget build(BuildContext context) {
    final List<TenantVisitContent> visibleVisits = _visibleVisits;

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              VisitHeader(
                title: LocaleKeys.tenantVisitsTitle,
                backKey: const ValueKey('tenant-visits-back'),
                onBackPressed: () => Go.back(),
              ),
              SizedBox(
                height: 44.h,
                child: ListView.separated(
                  key: const ValueKey('tenant-visits-filters'),
                  scrollDirection: Axis.horizontal,
                  padding: EdgeInsets.symmetric(horizontal: 20.w),
                  itemBuilder: (context, index) {
                    final TenantVisitFilter filter = _filters[index];
                    return VisitFilterChip(
                      key: ValueKey('tenant-visits-filter-${filter.name}'),
                      label: filter.label,
                      isSelected: filter.isSame(_selectedFilter),
                      onPressed: () => _selectFilter(filter),
                    );
                  },
                  separatorBuilder: (context, index) => 8.szW,
                  itemCount: _filters.length,
                ),
              ),
              10.szH,
              Expanded(
                child: visibleVisits.isEmpty
                    ? Center(
                        child: AppText(
                          LocaleKeys.tenantVisitsNoResults,
                          color: AppColors.sokoonGray,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w700,
                          textAlign: TextAlign.center,
                        ),
                      )
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 18.h),
                        itemBuilder: (context, index) {
                          final TenantVisitContent visit = visibleVisits[index];
                          return TenantVisitCard(
                            visit: visit,
                            onPressed: () => _openDetails(visit),
                            onChatPressed: _openChat,
                            onRatePressed: () => _showRating(visit),
                            onCancelPressed: () => _removeVisit(visit),
                            onAlternativePressed: () =>
                                Go.to(const TenantSearchScreen()),
                          );
                        },
                        separatorBuilder: (context, index) => 12.szH,
                        itemCount: visibleVisits.length,
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
