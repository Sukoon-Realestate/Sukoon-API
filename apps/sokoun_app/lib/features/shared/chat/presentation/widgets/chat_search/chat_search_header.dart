import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';

import '../chat_list/chat_search_field.dart';

class ChatSearchHeader extends StatelessWidget {
  const ChatSearchHeader({
    super.key,
    required this.controller,
    required this.onQueryChanged,
    required this.onClearPressed,
  });

  final TextEditingController controller;
  final ValueChanged<String> onQueryChanged;
  final VoidCallback onClearPressed;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const SokoonBackButton(),
        8.szW,
        Expanded(
          child: ChatSearchField(
            controller: controller,
            autofocus: false,
            isActive: true,
            onChanged: onQueryChanged,
            onClearPressed: onClearPressed,
          ),
        ),
      ],
    ).padding(EdgeInsetsDirectional.fromSTEB(14.w, 8.h, 20.w, 12.h));
  }
}
