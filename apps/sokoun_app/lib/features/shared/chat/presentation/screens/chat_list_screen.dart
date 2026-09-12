import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';

import '../widgets/imports.dart';
import 'chat_empty_screen.dart';
import 'chat_search_screen.dart';

class ChatListScreen extends StatelessWidget {
  const ChatListScreen({
    super.key,
    this.conversations = ChatContent.conversations,
  });

  final List<ConversationContent> conversations;

  @override
  Widget build(BuildContext context) {
    if (conversations.isEmpty) {
      return const ChatEmptyScreen();
    }

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AppText(
                LocaleKeys.chatConversationsTitle,
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
                fontWeight: FontWeight.w900,
              ).padding(EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 12.h)),
              ChatSearchField(
                readOnly: true,
                onTap: () => Go.to(const ChatSearchScreen()),
              ).paddingSymmetric(horizontal: 20.w),
              ChatPrivacyBanner(
                text: LocaleKeys.chatPhonePrivacyInbox,
              ).padding(EdgeInsets.fromLTRB(8.w, 12.h, 8.w, 0)),
              Expanded(
                child: ListView.separated(
                  padding: EdgeInsets.only(top: 10.h, bottom: 14.h),
                  itemBuilder: (context, index) {
                    final ConversationContent conversation =
                        conversations[index];
                    return ChatListItem(
                      key: ValueKey(conversation.id),
                      conversation: conversation,
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
      ),
    );
  }
}
