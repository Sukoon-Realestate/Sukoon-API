import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_results_screen.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';

class HomeSectionHeader extends StatelessWidget {
  const HomeSectionHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: AppText(
            LocaleKeys.tenantHomeSuggestedForYou,
            style: AppTextStyles.bold15.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 15.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.start,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        Flexible(
          child: TextButton(
            onPressed: () => Go.to(
              const TenantSearchResultsScreen(
                initialFilters: PropertySearchFilters.initial(),
              ),
            ),
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.zero,
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              LocaleKeys.tenantHomeViewAll,
              style: AppTextStyles.bold12.copyWith(
                color: AppColors.sokoonTeal,
                fontSize: 12.sp,
                height: 1.45,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
      ],
    );
  }
}
