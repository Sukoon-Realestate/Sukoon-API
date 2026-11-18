from pathlib import Path
p = Path('/Users/demo23home/code/sukoon/sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/book_visit/book_visit_form.dart')
s = p.read_text()
a = s.index('        Container(\n')
b = s.index('\n\n        16.szH,', a)
s = s[:a] + '''        DefaultTextField(
          controller: noteController,
          inputType: TextInputType.multiline,
          action: TextInputAction.newline,
          minLines: 3,
          maxLines: 5,
          maxLength: 1000,
          textAlign: TextAlign.start,
          useGlass: false,
          style: AppTextStyles.medium13.copyWith(
            color: context.appColor(AppColors.sokoonNavy),
            fontSize: 13.sp,
            height: 1.45,
          ),
          decoration: InputDecoration(
            filled: true,
            fillColor: context.appColor(AppColors.white, surface: true),
            isDense: true,
            contentPadding: EdgeInsets.symmetric(
              horizontal: 14.w,
              vertical: 14.h,
            ),
            hintText: LocaleKeys.tenantVisitNoteHint,
            hintStyle: AppTextStyles.base.copyWith(
              color: context.appColor(AppColors.sokoonMuted),
              fontSize: 13.sp,
              height: 1.45,
            ),
            counterStyle: AppTextStyles.regular12.copyWith(
              color: context.appColor(AppColors.sokoonMuted),
              fontSize: 12.sp,
              height: 1.5,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14.r),
              borderSide: BorderSide(
                color: context.appColor(AppColors.sokoonBorder),
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14.r),
              borderSide: BorderSide(
                color: context.appColor(AppColors.sokoonBorder),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14.r),
              borderSide: BorderSide(
                color: context.appColor(AppColors.primary),
                width: 1.5,
              ),
            ),
          ),
        ),''' + s[b:]
p.write_text(s)
