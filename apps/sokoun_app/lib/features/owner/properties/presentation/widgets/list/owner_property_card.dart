part of '../../../imports.dart';

class OwnerPropertyCard extends StatelessWidget {
  const OwnerPropertyCard({
    super.key,
    required this.property,
    required this.onEditPressed,
    required this.onAnalyticsPressed,
    required this.onActionsPressed,
    required this.onPressed,
  });

  final OwnerPropertyContent property;
  final VoidCallback onEditPressed;
  final VoidCallback onAnalyticsPressed;
  final VoidCallback onActionsPressed;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.white,
      borderRadius: BorderRadius.circular(20.r),
      child: InkWell(
        key: ValueKey('owner-property-card-${property.id}'),
        onTap: onPressed,
        borderRadius: BorderRadius.circular(20.r),
        child: Container(
          padding: EdgeInsets.all(16.w),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20.r),
            border: Border.all(color: AppColors.sokoonBorder),
            boxShadow: const [
              BoxShadow(
                color: AppColors.shadowBlack04,
                blurRadius: 4,
                offset: Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: [
              Row(
                textDirection: TextDirection.ltr,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 80.r,
                    height: 80.r,
                    decoration: BoxDecoration(
                      color: AppColors.grayBluePale,
                      borderRadius: BorderRadius.circular(16.r),
                    ),
                    child: property.mainImage.isEmpty
                        ? Icon(
                            property.icon,
                            color: AppColors.blueGrayLight,
                            size: 30.r,
                          )
                        : CachedImage(
                            url: property.mainImage,
                            width: 80.r,
                            height: 80.r,
                            fit: BoxFit.cover,
                            borderRadius: BorderRadius.circular(16.r),
                            placeHolder: Icon(
                              property.icon,
                              color: AppColors.blueGrayLight,
                              size: 30.r,
                            ),
                          ),
                  ),
                  12.szW,
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        AppText(
                          property.title,
                          color: AppColors.sokoonNavy,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w900,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          textAlign: TextAlign.right,
                        ),
                        6.szH,
                        OwnerPropertyStatusBadge(status: property.status),
                        8.szH,
                        AppText(
                          '${_formatNumber(property.monthlyPrice)} '
                          '${LocaleKeys.ownerPropertiesPriceUnit}',
                          color: AppColors.sokoonTeal,
                          fontSize: 16.sp,
                          fontWeight: FontWeight.w900,
                          textAlign: TextAlign.right,
                        ),
                        6.szH,
                        AppText(
                          '${property.views} ${LocaleKeys.ownerPropertiesViewUnit}'
                          ' · ${property.visitRequests} ${LocaleKeys.ownerPropertiesVisitUnit}',
                          color: AppColors.sokoonGray,
                          fontSize: 12.sp,
                          fontWeight: FontWeight.w400,
                          textAlign: TextAlign.right,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              14.szH,
              Row(
                textDirection: TextDirection.ltr,
                children: [
                  _OwnerPropertyCardAction(
                    key: ValueKey('owner-property-edit-${property.id}'),
                    label: LocaleKeys.ownerPropertiesEdit,
                    foregroundColor: AppColors.blue,
                    backgroundColor: AppColors.bluePale,
                    onPressed: onEditPressed,
                  ),
                  8.szW,
                  _OwnerPropertyCardAction(
                    key: ValueKey('owner-property-analytics-${property.id}'),
                    label: LocaleKeys.ownerPropertiesAnalytics,
                    foregroundColor: AppColors.sokoonTeal,
                    backgroundColor: AppColors.mintLight,
                    onPressed: onAnalyticsPressed,
                  ),
                  8.szW,
                  _OwnerPropertyCardAction(
                    key: ValueKey('owner-property-actions-${property.id}'),
                    label: LocaleKeys.ownerPropertiesActions,
                    foregroundColor: AppColors.red,
                    backgroundColor: AppColors.redPale,
                    onPressed: onActionsPressed,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatNumber(int value) {
    return value.toString().replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]},',
    );
  }
}

class _OwnerPropertyCardAction extends StatelessWidget {
  const _OwnerPropertyCardAction({
    super.key,
    required this.label,
    required this.foregroundColor,
    required this.backgroundColor,
    required this.onPressed,
  });

  final String label;
  final Color foregroundColor;
  final Color backgroundColor;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Material(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12.r),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(12.r),
          child: SizedBox(
            height: 34.h,
            child: Center(
              child: AppText(
                label,
                color: foregroundColor,
                fontSize: 12.sp,
                fontWeight: FontWeight.w900,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
