part of '../../../imports.dart';

class TenantVisitsFilters extends StatelessWidget {
  const TenantVisitsFilters({
    super.key,
    required this.selectedFilter,
    required this.onFilterSelected,
  });

  final TenantVisitFilter selectedFilter;
  final ValueChanged<TenantVisitFilter> onFilterSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 44.h,
      child: ListView.separated(
        key: const ValueKey('tenant-visits-filters'),
        scrollDirection: Axis.horizontal,
        padding: EdgeInsets.symmetric(horizontal: 20.w),
        itemBuilder: (context, index) {
          final TenantVisitFilter filter = TenantVisitFilter.values[index];
          return VisitFilterChip(
            key: ValueKey('tenant-visits-filter-${filter.name}'),
            label: filter.label,
            isSelected: filter.isSame(selectedFilter),
            onPressed: () => onFilterSelected(filter),
          );
        },
        separatorBuilder: (context, index) => 8.szW,
        itemCount: TenantVisitFilter.values.length,
      ),
    );
  }
}
