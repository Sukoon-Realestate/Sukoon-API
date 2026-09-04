part of '../../../imports.dart';

class TenantVisitsList extends StatelessWidget {
  const TenantVisitsList({
    super.key,
    required this.selectedFilter,
    required this.initialVisits,
    required this.pagifyController,
    required this.onFilterSelected,
    required this.onVisitPressed,
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final TenantVisitFilter selectedFilter;
  final List<TenantVisitContent>? initialVisits;
  final PagifyController<TenantVisitContent>? pagifyController;
  final ValueChanged<TenantVisitFilter> onFilterSelected;
  final ValueChanged<TenantVisitContent> onVisitPressed;
  final ValueChanged<TenantVisitContent> onRatePressed;
  final ValueChanged<TenantVisitContent> onCancelPressed;

  List<TenantVisitContent> get _visibleInitialVisits {
    final List<TenantVisitContent> visits = initialVisits ?? const [];
    return visits
        .where((visit) => selectedFilter.accepts(visit.status))
        .toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    final List<TenantVisitContent>? visits = initialVisits;
    if (visits != null) {
      return _buildInitialList(_visibleInitialVisits);
    }

    return AppPagify<TenantVisitContent>(
      pagifyController: pagifyController!,
      asyncCall: (_, page) =>
          TenantVisitsData.getVisitsPage(page: page, filter: selectedFilter),
      shrinkWrap: false,
      cacheKey: TenantVisitsData.cacheKeyFor(selectedFilter),
      cacheToJson: (item) => item.toJson(),
      cacheFromJson: TenantVisitContent.fromJson,
      emptyListView: _buildEmptyState(),
      itemBuilder: (context, data, index, visit) =>
          _buildVisitCard(visit).paddingBottom(12.h),
    ).padding(EdgeInsets.fromLTRB(20.w, 0, 20.w, 18.h));
  }

  Widget _buildInitialList(List<TenantVisitContent> visits) {
    if (visits.isEmpty) return _buildEmptyState();

    return ListView.separated(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 18.h),
      itemBuilder: (context, index) => _buildVisitCard(visits[index]),
      separatorBuilder: (context, index) => 12.szH,
      itemCount: visits.length,
    );
  }

  Widget _buildVisitCard(TenantVisitContent visit) {
    return TenantVisitCard(
      visit: visit,
      onPressed: () => onVisitPressed(visit),
      onRatePressed: () => onRatePressed(visit),
      onCancelPressed: () => onCancelPressed(visit),
    );
  }

  Widget _buildEmptyState() {
    return TenantVisitsEmptyState(
      isFiltered: !selectedFilter.isAll,
      onClearFiltersPressed: () => onFilterSelected(TenantVisitFilter.all),
    );
  }
}
