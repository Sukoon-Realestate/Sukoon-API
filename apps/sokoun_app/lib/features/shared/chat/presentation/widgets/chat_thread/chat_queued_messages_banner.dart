import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../../cubits/chat_thread_cubit.dart';

class ChatQueuedMessagesBanner extends StatelessWidget {
  const ChatQueuedMessagesBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocSelector<
      ChatThreadCubit,
      ChatThreadState,
      ({bool show, bool unknown})
    >(
      selector: (state) =>
          (show: state.showQueuedMessages, unknown: state.unknownDelivery),
      builder: (context, delivery) {
        if (!delivery.show) {
          return const SizedBox.shrink();
        }

        return Semantics(
          liveRegion: true,
          label: delivery.unknown
              ? LocaleKeys.professionalUnknownDelivery
              : LocaleKeys.chatQueuedMessages,
          child: Container(
            width: double.infinity,
            margin: EdgeInsetsDirectional.fromSTEB(16.w, 0, 16.w, 8.h),
            padding: EdgeInsets.symmetric(horizontal: 12.w, vertical: 9.h),
            decoration: BoxDecoration(
              color: context.appColor(AppColors.amberPale, surface: true),
              borderRadius: BorderRadius.circular(12.r),
              border: Border.all(color: context.appColor(AppColors.amber)),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 8.w,
                  children: [
                    Icon(
                      Icons.schedule_send_rounded,
                      color: context.appColor(AppColors.brown),
                      size: 17.r,
                    ),
                    Expanded(
                      child: AppText(
                        delivery.unknown
                            ? LocaleKeys.professionalUnknownDelivery
                            : LocaleKeys.chatQueuedMessages,
                        style: AppTextStyles.semiBold.copyWith(
                          color: context.appColor(AppColors.brown),
                          fontSize: 12.sp,
                        ),
                      ),
                    ),
                  ],
                ),
                Align(
                  alignment: AlignmentDirectional.centerEnd,
                  child: TextButton(
                    onPressed: () => delivery.unknown
                        ? context.read<ChatThreadCubit>().checkDelivery()
                        : context.read<ChatThreadCubit>().retryPending(),
                    child: AppText(
                      delivery.unknown
                          ? LocaleKeys.professionalCheckDelivery
                          : LocaleKeys.ownerRetryAction,
                    ),
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
