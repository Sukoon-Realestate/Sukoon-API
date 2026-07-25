import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/chat/data/models/tenant_chat_content.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_search_screen.dart';

import '../widgets/imports.dart';
import 'tenant_chat_empty_screen.dart';
import 'tenant_chat_restricted_screen.dart';
import 'tenant_chat_search_screen.dart';
import 'tenant_chat_thread_screen.dart';

class TenantChatListScreen extends StatelessWidget {
  const TenantChatListScreen({
    super.key,
    this.conversations = TenantChatContent.conversations,
  });

  final List<TenantConversationContent> conversations;

  void _openConversation(TenantConversationContent conversation) {
    if (conversation.isVerified) {
      Go.to(TenantChatThreadScreen(conversation: conversation));
      return;
    }

    Go.to(TenantChatRestrictedScreen(conversation: conversation));
  }

  @override
  Widget build(BuildContext context) {
    if (conversations.isEmpty) {
      return TenantChatEmptyScreen(
        onExplorePressed: () => Go.off(const TenantSearchScreen()),
      );
    }

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 12.h),
                child: AppText(
                  LocaleKeys.chatConversationsTitle,
                  color: AppColors.sokoonNavy,
                  fontSize: 20.sp,
                  fontWeight: FontWeight.w900,
                ),
              ),
              Padding(
                padding: EdgeInsets.symmetric(horizontal: 20.w),
                child: TenantChatSearchField(
                  readOnly: true,
                  onTap: () => Go.to(const TenantChatSearchScreen()),
                ),
              ),
              Padding(
                padding: EdgeInsets.fromLTRB(8.w, 12.h, 8.w, 0),
                child: ChatPrivacyBanner(
                  text: LocaleKeys.chatPhonePrivacyInbox,
                ),
              ),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.only(top: 10.h, bottom: 14.h),
                  itemBuilder: (context, index) {
                    final TenantConversationContent conversation =
                        conversations[index];
                    return TenantChatListItem(
                      conversation: conversation,
                      onPressed: () => _openConversation(conversation),
                    );
                  },
                  separatorBuilder: (context, index) => Divider(
                    height: 1.h,
                    thickness: 1.h,
                    color: AppColors.sokoonBorder,
                  ),
                  itemCount: conversations.length,
                ),
              ),
            ],
          ),
        ),
        bottomNavigationBar: const TenantChatBottomNavigation(),
      ),
    );
  }
}
