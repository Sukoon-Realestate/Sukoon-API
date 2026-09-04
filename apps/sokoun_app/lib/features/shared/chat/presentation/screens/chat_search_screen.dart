import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_content.dart';

import '../widgets/imports.dart';

class ChatSearchScreen extends StatefulWidget {
  const ChatSearchScreen({super.key});

  @override
  State<ChatSearchScreen> createState() => _ChatSearchScreenState();
}

class _ChatSearchScreenState extends State<ChatSearchScreen> {
  late final TextEditingController _searchController;
  String _query = 'أحمد';

  List<ConversationContent> get _results {
    return ChatContent.searchConversations
        .where((conversation) => conversation.matchesQuery(_query))
        .toList(growable: false);
  }

  List<String> get _mentionedProperties {
    final String normalizedQuery = _query.trim();
    if (normalizedQuery.isEmpty) {
      return ChatContent.mentionedProperties;
    }

    return ChatContent.mentionedProperties
        .where((property) => property.contains(normalizedQuery))
        .toList(growable: false);
  }

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController(text: _query);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _updateQuery(String value) => setState(() => _query = value);

  void _clearQuery() {
    _searchController.clear();
    setState(() => _query = '');
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.white,
        body: SafeArea(
          child: Column(
            children: [
              Padding(
                padding: EdgeInsets.fromLTRB(14.w, 8.h, 20.w, 12.h),
                child: Row(
                  children: [
                    IconButton(
                      key: const ValueKey('chat-search-back'),
                      onPressed: () => Go.back(),
                      icon: Icon(
                        Icons.arrow_back_ios_new_rounded,
                        color: AppColors.sokoonNavy,
                        size: 19.r,
                      ),
                    ),
                    8.szW,
                    Expanded(
                      child: ChatSearchField(
                        controller: _searchController,
                        autofocus: false,
                        isActive: true,
                        onChanged: _updateQuery,
                        onClearPressed: _clearQuery,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView(
                  padding: EdgeInsets.fromLTRB(20.w, 2.h, 20.w, 20.h),
                  children: [
                    AppText(
                      '${LocaleKeys.chatSearchResultsFor} "$_query"',
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w900,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    8.szH,
                    for (int index = 0; index < _results.length; index++) ...[
                      ChatSearchResultItem(conversation: _results[index]),
                      if (index < _results.length - 1)
                        Divider(height: 1.h, color: AppColors.sokoonBorder),
                    ],
                    16.szH,
                    AppText(
                      LocaleKeys.chatMentionedProperties,
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      fontWeight: FontWeight.w900,
                    ),
                    8.szH,
                    for (final property in _mentionedProperties)
                      _MentionedPropertyRow(property: property),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MentionedPropertyRow extends StatelessWidget {
  const _MentionedPropertyRow({required this.property});

  final String property;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 12.h),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.grayBluePale,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(
              Icons.apartment_rounded,
              color: AppColors.blueGrayLight,
              size: 16.r,
            ),
          ),
          12.szW,
          Expanded(
            child: AppText(
              property,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Icon(
            Icons.arrow_forward_ios_rounded,
            color: AppColors.sokoonGray,
            size: 13.r,
          ),
        ],
      ),
    );
  }
}
