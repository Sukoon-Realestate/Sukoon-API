part of '../../../imports.dart';

class OwnerRequestInfoCard extends StatelessWidget {
  const OwnerRequestInfoCard({super.key, required this.request});

  final OwnerVisitRequestContent request;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16.r),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16.r),
        border: Border.all(color: AppColors.sokoonBorder),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 56.r,
                height: 56.r,
                alignment: Alignment.center,
                decoration: const BoxDecoration(
                  color: AppColors.bluePale,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.person_outline_rounded,
                  color: AppColors.blue,
                  size: 27.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: AppText(
                            request.name,
                            color: AppColors.sokoonNavy,
                            fontSize: 16.sp,
                            fontWeight: FontWeight.w900,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        if (request.isVerified) ...[
                          7.szW,
                          const OwnerVerifiedBadge(),
                        ],
                      ],
                    ),
                    4.szH,
                    AppText(
                      request.memberSince,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w400,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          12.szH,
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestedProperty,
            value: request.property,
          ),
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestDate,
            value: request.detailDate,
          ),
          _OwnerRequestInfoRow(
            label: LocaleKeys.ownerVisitRequestTime,
            value: request.time,
            showDivider: false,
          ),
        ],
      ),
    );
  }
}

class _OwnerRequestInfoRow extends StatelessWidget {
  const _OwnerRequestInfoRow({
    required this.label,
    required this.value,
    this.showDivider = true,
  });

  final String label;
  final String value;
  final bool showDivider;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 10.h),
      decoration: BoxDecoration(
        border: showDivider
            ? const Border(bottom: BorderSide(color: AppColors.sokoonBorder))
            : null,
      ),
      child: Row(
        children: [
          AppText(
            label,
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            fontWeight: FontWeight.w400,
          ),
          12.szW,
          Expanded(
            child: AppText(
              value,
              color: AppColors.sokoonNavy,
              fontSize: 13.sp,
              fontWeight: FontWeight.w800,
              textAlign: TextAlign.end,
              maxLines: 2,
            ),
          ),
        ],
      ),
    );
  }
}
