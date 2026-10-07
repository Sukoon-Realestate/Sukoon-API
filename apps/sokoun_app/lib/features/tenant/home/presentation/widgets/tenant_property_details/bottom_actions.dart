import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_feedback.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:melos_core/core/widgets/custom_loading.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';

class TenantPropertyBottomActions extends StatelessWidget {
  const TenantPropertyBottomActions({
    super.key,
    required this.property,
    required this.isSaved,
    required this.onSavedPressed,
    this.onChatPressed,
    this.isOpeningChat = false,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback? onSavedPressed;
  final VoidCallback? onChatPressed;
  final bool isOpeningChat;

  bool get _isOwnProperty =>
      property.ownerId.isNotEmpty &&
      property.ownerId == UserModel.currentUser?.id;

  void _openBookVisit() {
    if (_isOwnProperty) {
      WorkspaceNavigation.open(
        workspace: AppWorkspace.owner,
        tab: WorkspaceTab.properties,
      );
      return;
    }
    if (!WorkspaceNavigation.isAuthenticated) {
      WorkspaceNavigation.open(
        workspace: AppWorkspace.tenant,
        showLoginSheet: true,
        detail: () => Go.to(
          BookVisitScreen(
            property: VisitPropertyContent.fromPropertyDetails(property),
          ),
        ),
      );
      return;
    }
    Go.to(
      BookVisitScreen(
        property: VisitPropertyContent.fromPropertyDetails(property),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SokounActionFooter(
      child: Row(
        children: [
          Expanded(
            child: DefaultButton(
              onTap:
                  _isOwnProperty ||
                      !property.hasRentalOffers ||
                      (property.selectionConfirmed &&
                          property.selection?.isAvailable == true &&
                          property.selection?.canIdentify == true &&
                          RentalOfferCapabilities.configured.canRequestViewing)
                  ? _openBookVisit
                  : null,
              title: _isOwnProperty
                  ? LocaleKeys.workspaceManageProperty
                  : property.hasRentalOffers && property.selection == null
                  ? LocaleKeys.rentalSelectOffer
                  : property.hasRentalOffers && !property.selectionConfirmed
                  ? LocaleKeys.rentalConfirmAccommodation
                  : property.hasRentalOffers &&
                        !RentalOfferCapabilities.configured.canRequestViewing
                  ? LocaleKeys.rentalUnavailableCapability
                  : LocaleKeys.tenantVisitBookTitle,
              isFitted: false,
              minHeight: 48.h,
              padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 12.h),
              borderRadius: BorderRadius.circular(12.r),
              textStyle: AppTextStyles.medium13.copyWith(
                fontSize: FontSize.s13,
                height: 1.45,
              ),
            ),
          ),
          10.szW,
          if (!_isOwnProperty)
            Semantics(
              button: true,
              enabled: onChatPressed != null && !isOpeningChat,
              label: LocaleKeys.tenantVisitOpenOwnerChat,
              child: GestureDetector(
                onTap: isOpeningChat ? null : onChatPressed,
                behavior: HitTestBehavior.opaque,
                child: Container(
                  width: 48.r,
                  height: 48.r,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: context.appColor(
                      AppColors.grayBackground,
                      surface: true,
                    ),
                    borderRadius: BorderRadius.circular(14.r),
                  ),
                  child: isOpeningChat
                      ? SizedBox.square(
                          dimension: 19.r,
                          child: CustomLoading.showLoadingView(
                            color: context.appColor(AppColors.sokoonTeal),
                            size: 19.r,
                          ),
                        )
                      : Icon(
                          Icons.chat_bubble_outline_rounded,
                          color: onChatPressed == null
                              ? context.appColor(AppColors.sokoonMuted)
                              : context.appColor(AppColors.sokoonTeal),
                          size: 21.r,
                        ),
                ),
              ),
            ),
          10.szW,
          IconButton(
            tooltip: LocaleKeys.favoritesNavigationSaved,
            onPressed: onSavedPressed,
            isSelected: isSaved,
            style: IconButton.styleFrom(
              backgroundColor: context.appColor(
                AppColors.grayBackground,
                surface: true,
              ),
              minimumSize: Size(48.r, 48.r),
            ),
            icon: SokounSelectionFeedback(
              selected: isSaved,
              child: Icon(
                isSaved
                    ? Icons.bookmark_rounded
                    : Icons.bookmark_border_rounded,
                color: context.appColor(AppColors.sokoonTeal),
                size: 22.r,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
