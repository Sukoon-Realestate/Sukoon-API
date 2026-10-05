part of '../../../imports.dart';

class OwnerPropertiesStatusTabs extends StatelessWidget {
  const OwnerPropertiesStatusTabs({
    super.key,
    required this.selectedFilter,
    required this.onFilterSelected,
  });

  final OwnerPropertyFilter selectedFilter;
  final ValueChanged<OwnerPropertyFilter> onFilterSelected;

  @override
  Widget build(BuildContext context) => ColoredBox(
    color: AppColors.white,
    child: TabBar(
      indicatorSize: TabBarIndicatorSize.tab,
      isScrollable: true,
      tabAlignment: TabAlignment.center,
      padding: EdgeInsets.symmetric(horizontal: 20.w),
      labelPadding: EdgeInsets.symmetric(horizontal: 16.w),
      indicatorColor: AppColors.sokoonTeal,
      indicatorWeight: 2,
      dividerColor: AppColors.sokoonBorder,
      onTap: (index) => onFilterSelected(OwnerPropertyFilter.values[index]),
      tabs: [
        for (final filter in OwnerPropertyFilter.values)
          Tab(
            height: 50.h,
            child: AppText(
              filter.label,
              style:
                  (selectedFilter == filter
                          ? AppTextStyles.bold
                          : AppTextStyles.medium)
                      .copyWith(
                        fontSize: 14.sp,
                        color: selectedFilter == filter
                            ? AppColors.sokoonTeal
                            : AppColors.sokoonGray,
                      ),
            ),
          ),
      ],
    ),
  );
}
