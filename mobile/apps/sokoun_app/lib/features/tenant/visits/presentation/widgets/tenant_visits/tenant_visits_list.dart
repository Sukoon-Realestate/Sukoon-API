part of '../../../imports.dart';

class TenantVisitsList extends StatelessWidget {
  const TenantVisitsList({
    super.key,
    this.useRequestEndpoint = true,
    this.cancelingVisitId,
    required this.selectedFilter,
    required this.initialVisits,
    required this.pagifyController,
    required this.onFilterSelected,
    required this.onVisitPressed,
    required this.onRatePressed,
    required this.onCancelPressed,
  });

  final bool useRequestEndpoint;
  final String? cancelingVisitId;
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
      enablePullRefresh: true,
      pagifyController: pagifyController!,
      asyncCall: (_, page) => TenantVisitsData.getVisitsPage(
        page: page,
        filter: selectedFilter,
        requests: useRequestEndpoint,
      ),
      shrinkWrap: false,
      header: _buildHeader(),
      contentPadding: EdgeInsets.symmetric(horizontal: 20.w),
      cacheKey: TenantVisitsData.cacheKeyFor(
        selectedFilter,
        requests: useRequestEndpoint,
      ),
      cacheToJson: (item) => item.toJson(),
      cacheFromJson: TenantVisitContent.fromJson,
      emptyListView: _buildEmptyState(),
      itemBuilder: (context, data, index, visit) =>
          _buildVisitCard(visit).paddingBottom(12.h),
    ).paddingBottom(18.h);
  }

  Widget _buildInitialList(List<TenantVisitContent> visits) {
    return ListView(
      padding: EdgeInsets.only(bottom: 18.h),
      children: [
        _buildHeader(),
        if (visits.isEmpty)
          _buildEmptyState()
        else
          for (final visit in visits)
            _buildVisitCard(
              visit,
            ).padding(EdgeInsets.fromLTRB(20.w, 0, 20.w, 12.h)),
      ],
    );
  }

  Widget _buildHeader() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      VisitCollectionCount(initialCount: initialVisits?.length),
      TenantVisitsFilters(
        selectedFilter: selectedFilter,
        onFilterSelected: onFilterSelected,
      ),
      10.szH,
    ],
  );

  Widget _buildVisitCard(TenantVisitContent visit) {
    return TenantVisitCard(
      key: ValueKey(visit.id),
      visit: visit,
      isCanceling: cancelingVisitId == visit.id,
      canStartCancellation: cancelingVisitId == null,
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
