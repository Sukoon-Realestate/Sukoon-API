"""System service: logger."""

import logging


logger = logging.getLogger(__name__)


_PUSH_CAMPAIGNS = [
    {
        "id": "nc-1",
        "title": "عروض الصيف!",
        "timeAgo": "النهاردة 9:00 ص",
        "body": "احجز زيارتك واستمتع بخصم 20%",
        "openRate": "34% فتح",
        "recipientCount": "2,847 وصل",
    },
    {
        "id": "nc-2",
        "title": "عقارات جديدة!",
        "timeAgo": "أمس 3:00 م",
        "body": "شقق جديدة في مدينة نصر",
        "openRate": "28% فتح",
        "recipientCount": "1,924 وصل",
    },
    {
        "id": "nc-3",
        "title": "تذكير توثيق",
        "timeAgo": "قبل 3 أيام",
        "body": "وثّق هويتك وابدأ التواصل",
        "openRate": "45% فتح",
        "recipientCount": "923 وصل",
    },
]
