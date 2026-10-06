import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_content_transition.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import '../../../data/models/property_location.dart';
import '../owner_add_property/add_property_primary_button.dart';

class PropertyLocationConfirmation extends StatelessWidget {
  const PropertyLocationConfirmation({
    super.key,
    required this.selected,
    required this.busy,
  });
  final PropertyLocation? selected;
  final bool busy;

  @override
  Widget build(BuildContext context) => SokounActionFooter(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      spacing: 8.h,
      children: [
        AnimatedSize(
          duration: SokounMotion.duration(context, milliseconds: 240),
          curve: SokounMotion.curve,
          alignment: AlignmentDirectional.topStart,
          child: SokounContentTransition(
            identity: (selected?.latitude, selected?.longitude),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              spacing: 8.h,
              children: [
                AppText(
                  selected == null
                      ? LocaleKeys.propertyMapTapHint
                      : selected!.address.isEmpty
                      ? LocaleKeys.ownerAddPropertySelectedLocation
                      : selected!.address,
                  style: AppTextStyles.regular14.copyWith(
                    color: context.appColor(AppColors.sokoonNavy),
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (selected != null)
                  Text(selected!.coordinates, textDirection: TextDirection.ltr),
              ],
            ),
          ),
        ),
        AddPropertyPrimaryButton(
          label: LocaleKeys.propertyMapConfirm,
          onTap: selected?.isValid == true && !busy
              ? () => Go.back(selected)
              : null,
        ),
      ],
    ),
  );
}
