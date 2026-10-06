part of '../../../imports.dart';

class TenantVisitsScreenContent extends StatelessWidget {
  const TenantVisitsScreenContent({
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

  @override
  Widget build(BuildContext context) {
    return TenantVisitsList(
      useRequestEndpoint: useRequestEndpoint,
      cancelingVisitId: cancelingVisitId,
      selectedFilter: selectedFilter,
      initialVisits: initialVisits,
      pagifyController: pagifyController,
      onFilterSelected: onFilterSelected,
      onVisitPressed: onVisitPressed,
      onRatePressed: onRatePressed,
      onCancelPressed: onCancelPressed,
    );
  }
}
