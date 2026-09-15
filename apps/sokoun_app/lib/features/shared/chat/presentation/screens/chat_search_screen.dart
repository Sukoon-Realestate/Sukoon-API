import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

import '../../data/models/chat_content.dart';
import '../widgets/chat_search/chat_search_header.dart';
import '../widgets/chat_search/chat_search_results.dart';

class ChatSearchScreen extends StatefulWidget {
  const ChatSearchScreen({super.key, required this.conversations});

  final List<ConversationContent> conversations;

  @override
  State<ChatSearchScreen> createState() => _ChatSearchScreenState();
}

class _ChatSearchScreenState extends State<ChatSearchScreen> {
  late final TextEditingController _searchController;
  String _query = '';

  List<ConversationContent> get _results => widget.conversations
      .where((conversation) => conversation.matchesQuery(_query))
      .toList(growable: false);

  List<String> get _mentionedProperties {
    final List<String> properties = widget.conversations
        .map((conversation) => conversation.property.trim())
        .where((property) => property.isNotEmpty)
        .toSet()
        .toList(growable: false);
    final String normalizedQuery = _query.trim();
    if (normalizedQuery.isEmpty) return properties;

    return properties
        .where((property) => property.contains(normalizedQuery))
        .toList(growable: false);
  }

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
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
    return Scaffold(
      backgroundColor: AppColors.white,
      body: SafeArea(
        child: Column(
          children: [
            ChatSearchHeader(
              controller: _searchController,
              onQueryChanged: _updateQuery,
              onClearPressed: _clearQuery,
            ),
            Expanded(
              child: ChatSearchResults(
                query: _query,
                conversations: _results,
                mentionedProperties: _mentionedProperties,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
