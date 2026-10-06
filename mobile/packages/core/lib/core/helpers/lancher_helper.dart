import 'dart:developer';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../config/language/locale_keys.g.dart';

class LauncherHelper {
  static Future<void> launchGoogleMaps({
    required String latitude,
    required String longitude,
  }) async {
    final double? parsedLatitude = double.tryParse(latitude.trim());
    final double? parsedLongitude = double.tryParse(longitude.trim());

    if (parsedLatitude == null ||
        parsedLongitude == null ||
        parsedLatitude < -90 ||
        parsedLatitude > 90 ||
        parsedLongitude < -180 ||
        parsedLongitude > 180) {
      throw ArgumentError('Invalid latitude or longitude');
    }

    final Uri googleMapsUrl = Uri.https('www.google.com', '/maps/search/', {
      'api': '1',
      'query': '$parsedLatitude,$parsedLongitude',
    });

    final bool didLaunch = await launchUrl(
      googleMapsUrl,
      mode: LaunchMode.externalApplication,
    );
    if (!didLaunch) {
      throw LocaleKeys.exceptionError;
    }
  }

  static void launchURL({required String url}) async {
    if (!url.toString().startsWith('https')) {
      url = 'https://$url';
    }
    await launchUrl(Uri.parse(url));
  }

  static Future<void> launchWhatsApp(String phone) async {
    // Normalize input
    if (phone.startsWith('+')) {
      phone = phone.substring(1);
    } else if (phone.startsWith('00')) {
      phone = phone.substring(2);
    }

    final String message = Uri.encodeComponent(
      'مرحبا بك',
    ); // ✅ encode Arabic text

    final Uri nativeUrl = Uri.parse(
      "whatsapp://send?phone=$phone&text=$message",
    );
    final Uri webUrl = Uri.parse("https://wa.me/$phone?text=$message");

    debugPrint("Trying WhatsApp URL: $nativeUrl");

    if (await canLaunchUrl(nativeUrl)) {
      await launchUrl(nativeUrl, mode: LaunchMode.externalApplication);
    } else if (await canLaunchUrl(webUrl)) {
      await launchUrl(webUrl, mode: LaunchMode.externalApplication);
    } else {
      throw LocaleKeys.exceptionError;
    }
  }

  static void launchYoutube({required String url}) async {
    final Uri parsedUrl = Uri.parse(url);
    if (Platform.isIOS) {
      if (await canLaunchUrl(parsedUrl)) {
        await launchUrl(parsedUrl);
      } else {
        if (await canLaunchUrl(parsedUrl)) {
          await launchUrl(parsedUrl);
        } else {
          throw 'Could not launch $parsedUrl';
        }
      }
    } else {
      if (await canLaunchUrl(parsedUrl)) {
        await launchUrl(parsedUrl);
      } else {
        throw 'Could not launch $url';
      }
    }
  }

  static Future<void> launchTwitter(String userName) async {
    final twitterProfileUrl = Uri.parse(
      'twitter://user?screen_name=$userName',
    ); // Twitter app URL
    final Uri webUrl = Uri.parse('https://twitter.com/$userName'); // Web URL
    try {
      if (await canLaunchUrl(twitterProfileUrl)) {
        await launchUrl(twitterProfileUrl);
      } else {
        if (await canLaunchUrl(webUrl)) {
          await launchUrl(webUrl);
        } else {
          throw 'Could not launch Twitter in a web browser';
        }
      }
    } catch (e) {
      log('Error: $e');
    }
  }

  static Future<void> launchInstagram(String userName) async {
    final Uri instagramProfileUrl = Uri.parse(
      'https://www.instagram.com/$userName',
    ); // Replace with your Instagram profile URL
    final Uri instagramNativeApp = Uri.parse(
      'instagram://user?username=$userName',
    );

    try {
      if (await canLaunchUrl(instagramNativeApp)) {
        await launchUrl(instagramNativeApp); // Open Instagram app
      } else {
        if (await canLaunchUrl(instagramProfileUrl)) {
          await launchUrl(instagramProfileUrl);
        } else {
          throw 'Could not launch Instagram in a web browser';
        }
      }
    } catch (e) {
      log('Error: $e');
    }
  }

  static void launchFacebook(String userName) async {
    final Uri nativeUrl = Uri.parse(
      'fb://facewebmodal/f?href=https://www.facebook.com/$userName',
    );
    final Uri webUrl = Uri.parse('https://www.facebook.com/$userName');
    if (await canLaunchUrl(nativeUrl)) {
      await launchUrl(nativeUrl);
    } else {
      if (await canLaunchUrl(webUrl)) {
        await launchUrl(webUrl);
      } else {
        throw 'Could not launch $webUrl';
      }
    }
  }

  static Future<void> launchSnapchat(String userName) async {
    final snapchatProfileUrl = Uri.parse(
      'https://www.snapchat.com/add/$userName',
    );
    final snapChatNativeApp = Uri.parse('snapchat://add/$userName');

    try {
      if (await canLaunchUrl(snapChatNativeApp)) {
        await launchUrl(snapChatNativeApp);
      } else {
        if (await canLaunchUrl(snapchatProfileUrl)) {
          await launchUrl(snapchatProfileUrl);
        } else {
          throw 'Could not launch Snapchat in a web browser';
        }
      }
    } catch (e) {
      log('Error: $e');
    }
  }

  static Future<void> launchTikTok(String userName) async {
    final tiktokProfileUrl = Uri.parse('https://www.tiktok.com/@$userName');

    try {
      if (await canLaunchUrl(Uri.parse('com.zhiliaoapp.musically'))) {
        await launchUrl(
          Uri.parse('com.zhiliaoapp.musically://user?u=$userName'),
        );
      } else {
        if (await canLaunchUrl(tiktokProfileUrl)) {
          await launchUrl(tiktokProfileUrl);
        } else {
          throw 'Could not launch TikTok in a web browser';
        }
      }
    } catch (e) {
      log('Error: $e');
    }
  }

  static void callPhone({required String phone}) async {
    await launchUrl(Uri.parse('tel:$phone'));
  }

  static void sendMail({required String mail}) async {
    await launchUrl(Uri.parse('mailto:$mail'));
  }
}
