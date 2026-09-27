import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
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
  final VoidCallback onSavedPressed;
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
    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 18.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        children: [
          Expanded(
            child: GestureDetector(
              onTap: _openBookVisit,
              behavior: HitTestBehavior.opaque,
              child: Container(
                height: 48.h,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.sokoonTeal,
                  borderRadius: BorderRadius.circular(14.r),
                ),
                child: AppText(
                  _isOwnProperty
                      ? LocaleKeys.workspaceManageProperty
                      : LocaleKeys.tenantVisitBookTitle,
                  color: AppColors.white,
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w900,
                ),
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
                    color: AppColors.grayBackground,
                    borderRadius: BorderRadius.circular(14.r),
                  ),
                  child: isOpeningChat
                      ? SizedBox.square(
                          dimension: 19.r,
                          child: const CircularProgressIndicator(
                            strokeWidth: 2,
                            color: AppColors.sokoonTeal,
                          ),
                        )
                      : Icon(
                          Icons.chat_bubble_outline_rounded,
                          color: onChatPressed == null
                              ? AppColors.sokoonMuted
                              : AppColors.sokoonTeal,
                          size: 21.r,
                        ),
                ),
              ),
            ),
          10.szW,
          GestureDetector(
            onTap: onSavedPressed,
            behavior: HitTestBehavior.opaque,
            child: Container(
              width: 48.r,
              height: 48.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.grayBackground,
                borderRadius: BorderRadius.circular(14.r),
              ),
              child: Icon(
                isSaved
                    ? Icons.bookmark_rounded
                    : Icons.bookmark_border_rounded,
                color: AppColors.sokoonTeal,
                size: 22.r,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
