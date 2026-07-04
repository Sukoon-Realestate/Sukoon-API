// import 'package:flutter/material.dart';
// import 'package:flutter_bloc/flutter_bloc.dart';
// import 'package:flutter_screenutil/flutter_screenutil.dart';
// import '../../../config/language/locale_keys.g.dart';
// import '../../../config/res/config_imports.dart';
// import '../../../features/packages/presentation/screens/subscription_screen.dart';
// import '../../navigation/navigator.dart';
// import '../../shared/get_paymeny_brands_cubit.dart';
// import '../app_text.dart';
// import '../default_bottom_sheet.dart';
// import '../image_widgets/cached_image.dart';
// import '../radio_bottom_sheet.dart';
// import '../sheets/payment_sheet.dart';
// import '../sheets/success_sheet.dart';
// import 'app_loading_button.dart';
//
// class PayButton extends StatelessWidget {
//   final GlobalKey<FormState> formKey;
//   final bool withShowPaymentSheet;
//   final void Function(BuildContext context)? onFinish;
//   final Future<void> Function(BuildContext context, int brandId, void Function(String url) onSuccess) onPay;
//   const PayButton({super.key,
//     required this.formKey,
//     required this.onPay,
//     this.withShowPaymentSheet = false,
//     this.onFinish,
//   });
//
//   Future<void> _asyncCall(BuildContext context)async{
//     if(formKey.currentState!.validate()){
//       await context.read<PaymentBrands>().get(
//           onSuccess: (data) => showDefaultBottomSheet(
//               child: RadioSelectionWidget<int>(
//                   selectedBackgroundColor: AppColors.primary.withOpacity(.2),
//                   title: LocaleKeys.choosePaymentMethod,
//                   onSubmit: (ctx, brandId) async => await onPay.call(context, brandId, (url) async{
//                     final result = await Go.to(SubscriptionScreen(initialUrl: url));
//                     if(result == 'success'){
//                       await showDefaultBottomSheet(
//                           child: SuccessSheet(
//                             isInAuth: false,
//                             upperText: Text(LocaleKeys.walletChargedSuccessfully),
//                           ));
//                       Go.back('success');
//                       onFinish?.call(context);
//                     }
//                   }),
//                   values: data.map((e) => e.id??0).toList(),
//                   showSubmitButton: true,
//                   titles: List.generate(
//                       data.length,
//                           (i) => Expanded(child: Row(
//                         spacing: 10.w,
//                         children: [
//                           CachedImage(
//                               width: 50.w,
//                               height: 50.h,
//                               url: data[i].image??''
//                           ),
//                           AppText(data[i].name??''),
//                         ],
//                       ))
//                   )
//               )
//           )
//       );
//     }
//   }
//
//   @override
//   Widget build(BuildContext context) {
//     return BlocProvider(
//       create: (context) => PaymentBrands(),
//       child: AppLoadingButton(
//           asyncCall: (context) async{
//             if(withShowPaymentSheet){
//               showDefaultBottomSheet(
//                   child: PaymentSheet(
//                       onPay: (ctx, method) => method == PaymentMethod.online?
//                       _asyncCall(context) : ,
//                   ),
//               );
//
//             }else{
//               _asyncCall(context);
//             }
//           },
//           title: LocaleKeys.confirm
//       ),
//     );
//   }
// }
