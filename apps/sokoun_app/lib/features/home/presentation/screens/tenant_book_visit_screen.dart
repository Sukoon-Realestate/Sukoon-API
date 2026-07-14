import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/tenant_property_content.dart';

import '../widgets/tenant_book_visit/imports.dart';
import 'tenant_visit_confirmed_screen.dart';

class TenantBookVisitScreen extends StatefulWidget {
  const TenantBookVisitScreen({super.key, required this.property});

  final TenantPropertyDetailsContent property;

  @override
  State<TenantBookVisitScreen> createState() => _TenantBookVisitScreenState();
}

class _TenantBookVisitScreenState extends State<TenantBookVisitScreen> {
  int _selectedDayIndex = 1;
  String _selectedSlot = '2:00 م';
  late final TextEditingController _noteController;

  @override
  void initState() {
    super.initState();
    _noteController = TextEditingController();
  }

  @override
  void dispose() {
    _noteController.dispose();
    super.dispose();
  }

  void _confirmVisit() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => TenantVisitConfirmedScreen(
          property: widget.property,
          selectedDay: TenantPropertyFilterOptions.visitDays[_selectedDayIndex],
          selectedTime: _selectedSlot,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              BookVisitTopBar(onBack: () => Navigator.of(context).pop()),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(18.w, 0, 18.w, 20.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      VisitPropertySummaryCard(property: widget.property),
                      18.szH,
                      const VisitSectionTitle('اختار يوم الزيارة'),
                      10.szH,
                      SizedBox(
                        height: 74.h,
                        child: ListView.separated(
                          scrollDirection: Axis.horizontal,
                          reverse: true,
                          itemBuilder: (context, index) {
                            final day =
                                TenantPropertyFilterOptions.visitDays[index];
                            return VisitDayChip(
                              day: day,
                              isSelected: index == _selectedDayIndex,
                              onTap: () =>
                                  setState(() => _selectedDayIndex = index),
                            );
                          },
                          separatorBuilder: (context, index) => 8.szW,
                          itemCount:
                              TenantPropertyFilterOptions.visitDays.length,
                        ),
                      ),
                      18.szH,
                      const VisitSectionTitle('اختار الوقت'),
                      10.szH,
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 3,
                          childAspectRatio: 2.6,
                          crossAxisSpacing: 10.w,
                          mainAxisSpacing: 10.h,
                        ),
                        itemCount:
                            TenantPropertyFilterOptions.visitSlots.length,
                        itemBuilder: (context, index) {
                          final slot =
                              TenantPropertyFilterOptions.visitSlots[index];
                          return VisitSlotChip(
                            slot: slot,
                            isSelected: slot.label == _selectedSlot,
                            onTap: slot.isAvailable
                                ? () =>
                                      setState(() => _selectedSlot = slot.label)
                                : null,
                          );
                        },
                      ),
                      22.szH,
                      const VisitSectionTitle('ملاحظة للمالك (اختياري)'),
                      10.szH,
                      Container(
                        height: 92.h,
                        padding: EdgeInsets.symmetric(horizontal: 14.w),
                        decoration: BoxDecoration(
                          color: AppColors.white,
                          borderRadius: BorderRadius.circular(16.r),
                          border: Border.all(color: AppColors.sokoonBorder),
                        ),
                        child: TextField(
                          controller: _noteController,
                          maxLines: 4,
                          textAlign: TextAlign.right,
                          style: TextStyle(
                            color: AppColors.sokoonNavy,
                            fontSize: 13.sp,
                            fontWeight: FontWeight.w500,
                          ),
                          decoration: InputDecoration(
                            hintText: 'أي تفاصيل تريد ذكرها…',
                            hintStyle: TextStyle(
                              color: AppColors.navyAlpha50,
                              fontSize: 13.sp,
                            ),
                            border: InputBorder.none,
                          ),
                        ),
                      ),
                      16.szH,
                      Container(
                        padding: EdgeInsets.all(12.w),
                        decoration: BoxDecoration(
                          color: AppColors.bluePale,
                          borderRadius: BorderRadius.circular(14.r),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              Icons.privacy_tip_outlined,
                              color: AppColors.blue,
                              size: 16.r,
                            ),
                            8.szW,
                            Expanded(
                              child: AppText(
                                'رقمك لن يُشارك مع المالك حتى تأكيد الزيارة',
                                color: AppColors.blue,
                                fontSize: 12.sp,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ],
                        ),
                      ),
                      16.szH,
                      GestureDetector(
                        onTap: _confirmVisit,
                        behavior: HitTestBehavior.opaque,
                        child: Container(
                          height: 50.h,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            color: AppColors.sokoonTeal,
                            borderRadius: BorderRadius.circular(14.r),
                          ),
                          child: AppText(
                            'تأكيد طلب الزيارة',
                            color: AppColors.white,
                            fontSize: 15.sp,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
