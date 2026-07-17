class ApiConstants {
// ---------------------- Home -----------------------------------
  // auth
  static const String login = 'auth/login/';

  // packages
  static const String getPackages = 'packages/';
  static const String individual = 'individual';
  static const String family = 'family';
  static const String subscribePackage = 'subscribe-package';
  static const String renewPackage = 'renew-package';
  static const String getMyPackage = 'my-package';
  static const String relations = 'relations';
  static const String cities = 'cities';
  static const String getPartnerInfo = 'opportunity-profile/';

  // Settings/Data
  static const String maritalStatuses = 'marital-status';
  static const String hijabTypes = 'hijab';
  static const String skinColors = 'skin-colors';
  static const String weddingTypes = 'wedding-types';
  static const String childCustodies = 'child-custody';
  static const String chatLanguages = 'chat-languages';
  static const String religiousCommitments = 'religious-commitment';
  static const String getNotifications = 'notifications';
  static const String getNotificationsCount = 'count-notifications';
  static const String countUnreadMessages = 'count-unread-messages';
  static const String deleteNotification = 'delete-notification/';
  static const String deleteAllNotification = 'delete-notifications';
  static const String profile = 'profile';
  static const String myPackage = 'my-package';
  static const String getWallet = 'show-wallet';
  static const String deleteAccount = 'delete-account';
  static const String switchNotify = 'switch-notify';
  static const String sendCodeToOldPhone = 'old-phone-send-code';
  static const String checkCodeToOldPhone = 'old-phone-check-code';

  static const String sendCodeToNewPhone = 'new-phone-send-code';
  static const String checkCodeToNewPhone = 'new-phone-check-code';
  static const String oath = 'oath';
  static const String changeLang = 'change-lang';
  static const String editProfile = 'update-profile';
  static const String addChild = 'add-child';
  static const String deleteChild = 'delete-child/';
  static const String opportunityChildren = 'opportunity-children/';
  static const String getChildren = 'children';
  static const String getChildProfile = 'get-child-profile/';
  static const String pendingChats = 'chats/pending'; // معلقة
  static const String cancelledChats = 'chats/cancelled'; // ملغية
  static const String completedChats = 'chats/completed'; // مكتملة
  static const String rejectedChats = 'chats/rejected'; // مرفوضة
  static const String currentChats = 'chats/current'; // محادثاتي
  static const String report = 'user-reports';
  static const String updateChildProfile = 'update-child-profile/';
  static const String sendMsg = 'send-message/';
  static const String filter = 'filter';



  static const String startChat = 'start-chat';
  static const String appStages = 'app-stages';
  static const String parentExchangeNumbers = 'parent-exchange-numbers';
  static const String parentIndividualConversation = 'parent-individual-conversation';
  static const String uploadImage = 'upload-room-file/';
  static const String matchTipPageSeen = 'match-tip-page-seen';
  static const String finishChat = 'finish-chat';
  static const String socials = 'socials';

  // Chat
  // ============================== Tips ==============================
  static const String chattingStageTips = 'chatting-stage-tips';
  static const String shariaComplaintMeetingTerms = 'sharia-complaint-meeting-terms';
  static const String shariaComplaintMeetingTips = 'sharia-complaint-meeting-tips';
  static const String istikharaTips = 'istikhara-tips';
  static const String informParentsTips = 'inform-parents';
  static const String engagementTips = 'engagement-tips';

// ============================== user request ==============================

  static const String matchRequestAnd = 'user-match-request/';
  static const String userMoveToNextRequest = 'next_stage_request';
  static const String continueStageRequest = 'continue_stage_request';
  static const String userExtensionRequest = 'extension_request';
  static const String videoCallRequest = 'video_call_request';
  static const String adminMeetingRequest = 'admin_meeting_request';
  static const String parentMeetingRequest = 'parent_meeting_request';
  static const String forceReject = 'force-reject-match';


  static const String istikharaReminder = 'istikhara-reminder';
  static const String istikharaDua = 'istikhara-dua';

  static const String rejectAll = 'reject-match-request';
  static const String shariaChoiceRequest = 'sharia_choice_request';
  static const String payRequest = 'pay-request/';
  static const String endVideoCall = 'end-video-call';
  static const String markRead = 'mark-read';
  static const String checkChatEligibility = 'check-chat-eligibility';

// ============================== acceptance ==============================
  static const String acceptRequest = 'accept-request/';
  static const String rejectRequest = 'reject-request/';

}