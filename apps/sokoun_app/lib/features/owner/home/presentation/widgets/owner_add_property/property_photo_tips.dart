import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_section_card.dart';

class PhotoTipsSection extends StatelessWidget {
  const PhotoTipsSection({super.key});

  @override
  Widget build(BuildContext context) {
    return AddPropertySectionCard(
      title: LocaleKeys.ownerAddPropertyPhotoTips,
      child: Column(
        children: [
          for (
            int index = 0;
            index < OwnerAddPropertyContent.photoTips.length;
            index++
          ) ...[
            TipRow(text: OwnerAddPropertyContent.photoTips[index]),
            if (index < OwnerAddPropertyContent.photoTips.length - 1)
              const Divider(color: AppColors.sokoonBorder),
          ],
        ],
      ),
    );
  }
}

class TipRow extends StatelessWidget {
  const TipRow({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(
          Icons.check_circle_outline_rounded,
          color: AppColors.sokoonTeal,
          size: 16.r,
        ),
        8.szW,
        Expanded(
          child: AppText(
            text,
            style: AppTextStyles.regular12.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 12.sp,
              height: 1.45,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ),
      ],
    ).paddingSymmetric(vertical: 4.h);
  }
}
