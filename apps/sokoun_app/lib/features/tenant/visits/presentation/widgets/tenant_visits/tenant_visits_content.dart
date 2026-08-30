part of '../../../imports.dart';

class TenantVisitsScreenContent extends StatelessWidget {
  const TenantVisitsScreenContent({
    super.key,
    required this.selectedFilter,
    required this.initialVisits,
    required this.pagifyController,
    required this.cacheKey,
    required this.loadPage,
    required this.onBackPressed,
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
  final VoidCallback onBackPressed;
  final ValueChanged<TenantVisitFilter> onFilterSelected;
  final ValueChanged<TenantVisitContent> onVisitPressed;
  final VoidCallback onChatPressed;
  final ValueChanged<TenantVisitContent> onRatePressed;
  final ValueChanged<TenantVisitContent> onCancelPressed;
  final VoidCallback onBrowsePropertiesPressed;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        VisitHeader(
          title: LocaleKeys.tenantVisitsTitle,
          backKey: const ValueKey('tenant-visits-back'),
          onBackPressed: onBackPressed,
        ),
        TenantVisitsFilters(
          selectedFilter: selectedFilter,
          onFilterSelected: onFilterSelected,
        ),
        10.szH,
        Expanded(
          child: TenantVisitsList(
            selectedFilter: selectedFilter,
            initialVisits: initialVisits,
            pagifyController: pagifyController,
            cacheKey: cacheKey,
            loadPage: loadPage,
            onFilterSelected: onFilterSelected,
            onVisitPressed: onVisitPressed,
            onChatPressed: onChatPressed,
            onRatePressed: onRatePressed,
            onCancelPressed: onCancelPressed,
            onBrowsePropertiesPressed: onBrowsePropertiesPressed,
          ),
        ),
      ],
    );
  }
}
