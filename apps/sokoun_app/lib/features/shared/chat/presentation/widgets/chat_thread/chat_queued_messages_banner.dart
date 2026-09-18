import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../cubits/socket_cubit.dart';

class ChatQueuedMessagesBanner extends StatelessWidget {
  const ChatQueuedMessagesBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocSelector<ChatThreadCubit, ChatThreadState, int>(
      selector: (state) => state.queuedMessageCount,
      builder: (context, queuedMessageCount) {
        if (queuedMessageCount == 0) {
          return const SizedBox.shrink();
        }

        return Semantics(
          liveRegion: true,
          label: LocaleKeys.chatQueuedMessages,
          child: Container(
            width: double.infinity,
            margin: EdgeInsetsDirectional.fromSTEB(16.w, 0, 16.w, 8.h),
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 9.h),
            decoration: BoxDecoration(
              color: AppColors.amberPale,
              borderRadius: BorderRadius.circular(12.r),
              border: Border.all(color: AppColors.amber),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.schedule_send_rounded,
                  color: AppColors.brown,
                  size: 17.r,
                ),
                SizedBox(width: 8.w),
                Flexible(
                  child: AppText(
                    LocaleKeys.chatQueuedMessages,
                    color: AppColors.brown,
                    fontSize: 12.sp,
                    fontWeight: FontWeight.w600,
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
