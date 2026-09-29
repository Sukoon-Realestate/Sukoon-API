import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../../data/models/chat_content.dart';
import 'chat_mentioned_property_row.dart';
import 'chat_search_empty_state.dart';
import 'chat_search_result_item.dart';

class ChatSearchResults extends StatelessWidget {
  const ChatSearchResults({
    super.key,
    required this.query,
    required this.conversations,
    required this.mentionedProperties,
  });

  final String query;
  final List<ConversationContent> conversations;
  final List<String> mentionedProperties;

  bool get _isEmpty => conversations.isEmpty && mentionedProperties.isEmpty;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.fromLTRB(20.w, 2.h, 20.w, 20.h),
      children: [
        AppText(
          '${LocaleKeys.chatSearchResultsFor} "$query"',
          style: AppTextStyles.bold12.copyWith(
            color: AppColors.sokoonGray,
            fontSize: 12.sp,
            height: 1.45,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        8.szH,
        if (_isEmpty)
          const ChatSearchEmptyState()
        else ...[
          for (int index = 0; index < conversations.length; index++) ...[
            ChatSearchResultItem(
              key: ValueKey<String>(conversations[index].id),
              conversation: conversations[index],
            ),
            if (index < conversations.length - 1)
              Divider(height: 1.h, color: AppColors.sokoonBorder),
          ],
          if (mentionedProperties.isNotEmpty) ...[
            16.szH,
            AppText(
              LocaleKeys.chatMentionedProperties,
              style: AppTextStyles.bold12.copyWith(
                color: AppColors.sokoonGray,
                fontSize: 12.sp,
                height: 1.45,
              ),
            ),
            8.szH,
            for (final String property in mentionedProperties)
              ChatMentionedPropertyRow(property: property),
          ],
        ],
      ],
    );
  }
}
