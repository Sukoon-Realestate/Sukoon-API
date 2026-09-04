part of '../../../imports.dart';

class TenantVisitsScreenContent extends StatelessWidget {
  const TenantVisitsScreenContent({
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

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        VisitHeader(
          title: LocaleKeys.tenantVisitsTitle,
          backKey: const ValueKey('tenant-visits-back'),
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
            onFilterSelected: onFilterSelected,
            onVisitPressed: onVisitPressed,
            onRatePressed: onRatePressed,
            onCancelPressed: onCancelPressed,
          ),
        ),
      ],
    );
  }
}
