part of '../../../imports.dart';

class OwnerEditField extends StatelessWidget {
  const OwnerEditField({
    super.key,
    required this.label,
    required this.controller,
    this.hint,
    this.keyboardType,
    this.maxLines = 1,
    this.suffixText,
  });

  final String label;
  final TextEditingController controller;
  final String? hint;
  final TextInputType? keyboardType;
  final int maxLines;
  final String? suffixText;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AppText(
          label,
          color: AppColors.sokoonNavy,
          fontSize: 13.sp,
          fontWeight: FontWeight.w800,
        ),
        7.szH,
        TextField(
          controller: controller,
          keyboardType: keyboardType,
          maxLines: maxLines,
          textDirection: TextDirection.rtl,
          inputFormatters: keyboardType == TextInputType.number
              ? [FilteringTextInputFormatter.digitsOnly]
              : null,
          decoration: InputDecoration(
            hintText: hint,
            suffixText: suffixText,
            filled: true,
            fillColor: AppColors.white,
            contentPadding: EdgeInsets.symmetric(
              horizontal: 14.w,
              vertical: 13.h,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14.r),
              borderSide: const BorderSide(color: AppColors.sokoonBorder),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14.r),
              borderSide: const BorderSide(
                color: AppColors.sokoonTeal,
                width: 1.5,
              ),
            ),
          ),
          style: TextStyle(
            color: AppColors.sokoonNavy,
            fontSize: 14.sp,
            fontFamily: ConstantManager.fontFamily,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
