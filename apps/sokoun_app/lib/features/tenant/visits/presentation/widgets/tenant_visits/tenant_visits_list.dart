part of '../../../imports.dart';

typedef TenantVisitsPageLoader =
    Future<(List<TenantVisitContent>, PaginationData)> Function(
      BuildContext context,
      int page,
    );

class TenantVisitsList extends StatelessWidget {
  const TenantVisitsList({
    super.key,
    required this.selectedFilter,
    required this.initialVisits,
    required this.pagifyController,
    required this.cacheKey,
    required this.loadPage,
    required this.onFilterSelected,
    required this.onVisitPressed,
    required this.onChatPressed,
    required this.onRatePressed,
    required this.onCancelPressed,
    required this.onBrowsePropertiesPressed,
  });

  final TenantVisitFilter selectedFilter;
  final List<TenantVisitContent>? initialVisits;
  final PagifyController<TenantVisitContent>? pagifyController;
  final String cacheKey;
  final TenantVisitsPageLoader loadPage;
  final ValueChanged<TenantVisitFilter> onFilterSelected;
  final ValueChanged<TenantVisitContent> onVisitPressed;
  final VoidCallback onChatPressed;
  final ValueChanged<TenantVisitContent> onRatePressed;
  final ValueChanged<TenantVisitContent> onCancelPressed;
  final VoidCallback onBrowsePropertiesPressed;

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

    return Padding(
      padding: EdgeInsets.fromLTRB(20.w, 0, 20.w, 18.h),
      child: AppPagify<TenantVisitContent>(
        pagifyController: pagifyController!,
        asyncCall: loadPage,
        shrinkWrap: false,
        cacheKey: cacheKey,
        cacheToJson: (item) => item.toJson(),
        cacheFromJson: TenantVisitContent.fromJson,
        emptyListView: _buildEmptyState(),
        itemBuilder: (context, data, index, visit) => Padding(
          padding: EdgeInsets.only(bottom: 12.h),
          child: _buildVisitCard(visit),
        ),
      ),
    );
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
      onChatPressed: onChatPressed,
      onRatePressed: () => onRatePressed(visit),
      onCancelPressed: () => onCancelPressed(visit),
      onAlternativePressed: onBrowsePropertiesPressed,
    );
  }

  Widget _buildEmptyState() {
    return TenantVisitsEmptyState(
      isFiltered: !selectedFilter.isAll,
      onActionPressed: selectedFilter.isAll
          ? onBrowsePropertiesPressed
          : () => onFilterSelected(TenantVisitFilter.all),
    );
  }
}
