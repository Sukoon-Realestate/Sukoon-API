import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core_apps.admin_api.models import KYCSubmission, StaffProfile, UserReport
from core_apps.chat.models import Conversation, ConversationParticipant, Message
from core_apps.common.models import ContentView
from core_apps.notifications.models import DeviceToken, Notification
from core_apps.profiles.models import Profile, UserSettings
from core_apps.properties.models import (
    City,
    Governorate,
    OwnerAvailabilitySlot,
    Property,
    PropertyFavorite,
    PropertyImage,
    PropertyRating,
    PropertyType,
    PropertyVisit,
    PropertyVisitReview,
    SavedProperty,
)
from core_apps.users.models import SocialAccount

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with comprehensive, realistic test data for all tables"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing data before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== Starting Database Seeder ==="))

        if options["reset"]:
            self.stdout.write(self.style.WARNING("Flushing existing records..."))
            ContentView.objects.all().delete()
            PropertyVisitReview.objects.all().delete()
            PropertyVisit.objects.all().delete()
            OwnerAvailabilitySlot.objects.all().delete()
            PropertyRating.objects.all().delete()
            SavedProperty.objects.all().delete()
            PropertyFavorite.objects.all().delete()
            PropertyImage.objects.all().delete()
            Property.objects.all().delete()
            City.objects.all().delete()
            Governorate.objects.all().delete()
            PropertyType.objects.all().delete()
            Message.objects.all().delete()
            ConversationParticipant.objects.all().delete()
            Conversation.objects.all().delete()
            Notification.objects.all().delete()
            DeviceToken.objects.all().delete()
            UserReport.objects.all().delete()
            KYCSubmission.objects.all().delete()
            StaffProfile.objects.all().delete()
            SocialAccount.objects.all().delete()
            UserSettings.objects.all().delete()
            Profile.objects.all().delete()
            User.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("All tables cleared successfully."))

        # 1. Users & Profiles & Staff
        users = self._seed_users()
        self._seed_social_accounts(users)
        self._seed_staff_profiles(users)
        self._seed_kyc_submissions(users)
        self._seed_user_reports(users)

        # 2. Locations & Property Types
        governorates, cities = self._seed_locations()
        property_types = self._seed_property_types()

        # 3. Properties & Gallery
        properties = self._seed_properties(users, governorates, cities, property_types)
        self._seed_property_images(properties)

        # 4. Engagement (Favorites, Saves, Ratings)
        self._seed_engagement(users, properties)

        # 5. Visits, Slots & Reviews
        self._seed_visits_and_reviews(users, properties)

        # 6. Chat & Messages
        self._seed_chat(users)

        # 7. Notifications & Devices
        self._seed_notifications_and_devices(users, properties)

        # 8. Content Views
        self._seed_content_views(users, properties)

        self.stdout.write(self.style.SUCCESS("\n🎉 Database seeded successfully with all tables populated!"))

    def _seed_users(self):
        self.stdout.write("  Creating users and profiles...")
        users_data = [
            {
                "email": "admin@sukoon.com",
                "first_name": "سيف",
                "last_name": "النظام",
                "password": "password123",
                "is_staff": True,
                "is_superuser": True,
                "is_verified": True,
                "phone": "+201011111111",
                "gender": Profile.Gender.MALE,
                "national_id": "29001011234567",
            },
            {
                "email": "main_admin@sukoon.com",
                "first_name": "أحمد",
                "last_name": "محمود",
                "password": "password123",
                "is_staff": True,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201022222222",
                "gender": Profile.Gender.MALE,
                "national_id": "29102021234567",
            },
            {
                "email": "kyc_reviewer@sukoon.com",
                "first_name": "نادية",
                "last_name": "سامي",
                "password": "password123",
                "is_staff": True,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201033333333",
                "gender": Profile.Gender.FEMALE,
                "national_id": "29203031234567",
            },
            {
                "email": "property_reviewer@sukoon.com",
                "first_name": "كريم",
                "last_name": "جمال",
                "password": "password123",
                "is_staff": True,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201044444444",
                "gender": Profile.Gender.MALE,
                "national_id": "29304041234567",
            },
            {
                "email": "support@sukoon.com",
                "first_name": "منى",
                "last_name": "عادل",
                "password": "password123",
                "is_staff": True,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201055555555",
                "gender": Profile.Gender.FEMALE,
                "national_id": "29405051234567",
            },
            {
                "email": "owner1@sukoon.com",
                "first_name": "طارق",
                "last_name": "الشريف",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201112223344",
                "gender": Profile.Gender.MALE,
                "national_id": "28506061234567",
            },
            {
                "email": "owner2@sukoon.com",
                "first_name": "ياسمين",
                "last_name": "عبد الرحمن",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201122334455",
                "gender": Profile.Gender.FEMALE,
                "national_id": "28807071234567",
            },
            {
                "email": "owner3@sukoon.com",
                "first_name": "حسام",
                "last_name": "المهدي",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201133445566",
                "gender": Profile.Gender.MALE,
                "national_id": "28208081234567",
            },
            {
                "email": "tenant1@sukoon.com",
                "first_name": "عمر",
                "last_name": "خالد",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201211223344",
                "gender": Profile.Gender.MALE,
                "national_id": "29809091234567",
            },
            {
                "email": "tenant2@sukoon.com",
                "first_name": "سارة",
                "last_name": "حسن",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": True,
                "phone": "+201222334455",
                "gender": Profile.Gender.FEMALE,
                "national_id": "29910101234567",
            },
            {
                "email": "tenant3@sukoon.com",
                "first_name": "زياد",
                "last_name": "إبراهيم",
                "password": "password123",
                "is_staff": False,
                "is_superuser": False,
                "is_verified": False,
                "phone": "+201233445566",
                "gender": Profile.Gender.MALE,
                "national_id": "29711111234567",
            },
        ]

        users = {}
        for udata in users_data:
            user, created = User.objects.get_or_create(
                email=udata["email"],
                defaults={
                    "first_name": udata["first_name"],
                    "last_name": udata["last_name"],
                    "is_staff": udata["is_staff"],
                    "is_superuser": udata["is_superuser"],
                    "is_verified": udata["is_verified"],
                },
            )
            user.set_password(udata["password"])
            user.first_name = udata["first_name"]
            user.last_name = udata["last_name"]
            user.is_staff = udata["is_staff"]
            user.is_superuser = udata["is_superuser"]
            user.is_verified = udata["is_verified"]
            user.save()

            # Update profile and settings
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.phone_number = udata["phone"]
            profile.gender = udata["gender"]
            profile.national_id = udata["national_id"]
            profile.birth_date = datetime.date(1995, 4, 12)
            profile.avatar = f"https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
            profile.save()

            settings, _ = UserSettings.objects.get_or_create(user=user)
            settings.visit_notifications = True
            settings.owner_messages = True
            settings.security_alerts = True
            settings.show_profile_in_search = True
            settings.save()

            users[udata["email"]] = user

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(users)} users created."))
        return users

    def _seed_social_accounts(self, users):
        SocialAccount.objects.get_or_create(
            provider=SocialAccount.PROVIDER_GOOGLE,
            provider_uid="google-oauth2-1092837465",
            defaults={
                "user": users["tenant1@sukoon.com"],
                "email": "tenant1@sukoon.com",
            },
        )
        SocialAccount.objects.get_or_create(
            provider=SocialAccount.PROVIDER_APPLE,
            provider_uid="apple-id-9988776655",
            defaults={
                "user": users["tenant2@sukoon.com"],
                "email": "tenant2@sukoon.com",
            },
        )

    def _seed_staff_profiles(self, users):
        self.stdout.write("  Creating staff profiles...")
        staff_map = [
            (users["admin@sukoon.com"], StaffProfile.RoleName.SYSTEM_OWNER, "مالك النظام"),
            (users["main_admin@sukoon.com"], StaffProfile.RoleName.MAIN_ADMIN, "مدير عام"),
            (users["kyc_reviewer@sukoon.com"], StaffProfile.RoleName.KYC_REVIEWER, "مراجع الهويات"),
            (users["property_reviewer@sukoon.com"], StaffProfile.RoleName.PROPERTY_REVIEWER, "مراجع العقارات"),
            (users["support@sukoon.com"], StaffProfile.RoleName.SUPPORT, "خدمة العملاء"),
        ]
        for user, role, display in staff_map:
            StaffProfile.objects.update_or_create(
                user=user,
                defaults={
                    "role_name": role,
                    "display_role": display,
                    "is_active": True,
                },
            )

    def _seed_kyc_submissions(self, users):
        self.stdout.write("  Creating KYC submissions...")
        # 1. Approved KYC
        KYCSubmission.objects.get_or_create(
            profile=users["owner1@sukoon.com"].profile,
            defaults={
                "status": KYCSubmission.Status.APPROVED,
                "reviewer": users["kyc_reviewer@sukoon.com"],
                "reviewed_at": timezone.now() - datetime.timedelta(days=10),
                "notes": "تمت مطابقة بطاقة الرقم القومي بنجاح.",
            },
        )
        # 2. Pending KYC
        KYCSubmission.objects.get_or_create(
            profile=users["owner2@sukoon.com"].profile,
            defaults={
                "status": KYCSubmission.Status.PENDING,
                "notes": "قيد المراجعة والتدقيق.",
            },
        )
        # 3. Rejected KYC
        KYCSubmission.objects.get_or_create(
            profile=users["tenant3@sukoon.com"].profile,
            defaults={
                "status": KYCSubmission.Status.REJECTED,
                "reviewer": users["kyc_reviewer@sukoon.com"],
                "reviewed_at": timezone.now() - datetime.timedelta(days=2),
                "rejection_reason": "صورة بطاقة الرقم القومي غير واضحة المعالم.",
                "notes": "يرجى إعادة رفع صورة واضحة للوجهين.",
            },
        )

    def _seed_user_reports(self, users):
        self.stdout.write("  Creating user reports...")
        UserReport.objects.get_or_create(
            reported_user=users["tenant3@sukoon.com"],
            reporter=users["owner1@sukoon.com"],
            reason="إلغاء الموعد بدون إشعار مسبق واستخدام لغة غير لائقة",
            defaults={
                "reason_type": UserReport.ReasonType.ABUSIVE,
                "status": UserReport.Status.ACTIVE,
                "automation_level": UserReport.AutomationLevel.LOW,
                "notes": "تقرير قيد النظر من الدعم الفني.",
            },
        )
        UserReport.objects.get_or_create(
            reported_user=users["owner3@sukoon.com"],
            reporter=users["tenant1@sukoon.com"],
            reason="معلومات الإعلان تختلف عن الواقع بالنسبة للمساحة والفرش",
            defaults={
                "reason_type": UserReport.ReasonType.MISLEADING,
                "status": UserReport.Status.DISMISSED,
                "automation_level": UserReport.AutomationLevel.AUTO,
                "reviewed_by": users["main_admin@sukoon.com"],
                "reviewed_at": timezone.now() - datetime.timedelta(days=5),
                "notes": "تم التحقق من الوحدة وتحديث تفاصيل الإعلان.",
            },
        )

    def _seed_locations(self):
        self.stdout.write("  Creating governorates and cities...")
        loc_data = {
            "القاهرة": ["مدينة نصر", "القاهرة الجديدة", "المعادي", "الزمالك", "مصر الجديدة", "المقطم", "الشروق"],
            "الجيزة": ["الدقي", "المهندسين", "الشيخ زايد", "السادس من أكتوبر", "الهرم", "حدائق الأهرام"],
            "الإسكندرية": ["سموحة", "ميامي", "ستانلي", "جليم", "العجمي", "المنتزه"],
            "البحر الأحمر": ["الغردقة", "الجونة", "سهل حشيش"],
        }

        governorates = {}
        cities = {}

        for gov_name, city_list in loc_data.items():
            gov, _ = Governorate.objects.get_or_create(name=gov_name)
            governorates[gov_name] = gov

            for city_name in city_list:
                city, _ = City.objects.get_or_create(governorate=gov, name=city_name)
                cities[f"{gov_name}_{city_name}"] = city

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(governorates)} governorates, {len(cities)} cities created."))
        return governorates, cities

    def _seed_property_types(self):
        self.stdout.write("  Creating property types...")
        types_data = [
            ("شقة", "apartment", "شقة سكنية عصرية متكاملة المرافق"),
            ("فيلا", "villa", "فيلا مستقلة فاخرة مع حديقة ومسبح خاص"),
            ("استوديو", "studio", "استوديو مجهز بالكامل مناسب للأفراد والطلاب"),
            ("دوبلكس", "duplex", "وحدة سكنية من طابقين بمساحات واسعة"),
            ("شاليه", "chalet", "شاليه سياحي وإطلالة مميزة"),
            ("غرفة", "room", "غرفة خاصة في سكن مشترك"),
            ("بنتهاوس", "penthouse", "بنتهاوس فاخر بروف خاص وإطلالة بانورامية"),
        ]

        property_types = {}
        for name, slug, desc in types_data:
            ptype, _ = PropertyType.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": desc},
            )
            property_types[slug] = ptype

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(property_types)} property types created."))
        return property_types

    def _seed_properties(self, users, governorates, cities, property_types):
        self.stdout.write("  Creating property listings...")
        props_data = [
            {
                "title": "شقة فاخرة مفروشة بالكامل في قلب المعادي",
                "description": "شقة راقية جداً بإطلالة خلابة على المساحات الخضراء، مجهزة بأحدث الأجهزة الكهربائية وتكييفات مركزية في جميع الغرف. قريبة جداً من محطة المترو والمطاعم ومراكز التسوق.",
                "owner": users["owner1@sukoon.com"],
                "price": Decimal("18000.00"),
                "price_period": Property.PricePeriod.MONTHLY,
                "property_type": property_types["apartment"],
                "is_furnished": True,
                "is_verified": True,
                "status": Property.Status.VERIFIED,
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 165,
                "space": "165 م²",
                "floor": 4,
                "rental_period": 12,
                "suitable_for": Property.SuitableFor.FAMILIES,
                "smoking_allowed": False,
                "gov": governorates["القاهرة"],
                "city": cities["القاهرة_المعادي"],
                "district": "دجلة المعادي",
                "lat": Decimal("29.959200"),
                "lng": Decimal("31.282500"),
                "has_wifi": True,
                "has_elevator": True,
                "has_garage": True,
                "has_security": True,
                "has_balcony": True,
                "has_air_conditioning": True,
                "near_metro": True,
                "has_natural_gas": True,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=1200",
            },
            {
                "title": "استوديو مودرن للطلاب قرب الجامعة الأمريكية بالتجمع الخامس",
                "description": "استوديو هادئ ومريح مصمم خصيصاً للطلاب والباحثين، يشمل مكتب دراسي وسرير مريح وإنترنت فائق السرعة، على بُعد 5 دقائق من الجامعة الأمريكية ومول بوينت 90.",
                "owner": users["owner2@sukoon.com"],
                "price": Decimal("8500.00"),
                "price_period": Property.PricePeriod.MONTHLY,
                "property_type": property_types["studio"],
                "is_furnished": True,
                "is_verified": True,
                "status": Property.Status.VERIFIED,
                "bedrooms": 1,
                "bathrooms": 1,
                "area": 55,
                "space": "55 م²",
                "floor": 2,
                "rental_period": 6,
                "suitable_for": Property.SuitableFor.STUDENTS,
                "smoking_allowed": False,
                "gov": governorates["القاهرة"],
                "city": cities["القاهرة_القاهرة الجديدة"],
                "district": "حي المصراوية، التجمع الخامس",
                "lat": Decimal("30.013100"),
                "lng": Decimal("31.498900"),
                "has_wifi": True,
                "has_elevator": True,
                "has_garage": False,
                "has_security": True,
                "has_balcony": True,
                "has_air_conditioning": True,
                "near_metro": False,
                "has_natural_gas": True,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=1200",
            },
            {
                "title": "فيلا مستقلة فاخرة بحمام سباحة في الشيخ زايد",
                "description": "فيلا فخمة داخل كمبوند سكني هادئ ومتميز، تشمل حديقة خاصة كبيرة وحمام سباحة وغرفة حارس، تشطيبات ألترا سوبر لوكس وإضاءات ليد حديثة.",
                "owner": users["owner1@sukoon.com"],
                "price": Decimal("55000.00"),
                "price_period": Property.PricePeriod.MONTHLY,
                "property_type": property_types["villa"],
                "is_furnished": True,
                "is_verified": True,
                "status": Property.Status.VERIFIED,
                "bedrooms": 5,
                "bathrooms": 4,
                "area": 420,
                "space": "420 م²",
                "floor": 1,
                "rental_period": 12,
                "suitable_for": Property.SuitableFor.FAMILIES,
                "smoking_allowed": True,
                "gov": governorates["الجيزة"],
                "city": cities["الجيزة_الشيخ زايد"],
                "district": "حي الياسمين، كمبوند زايد ديونز",
                "lat": Decimal("30.052000"),
                "lng": Decimal("30.985000"),
                "has_wifi": True,
                "has_elevator": False,
                "has_garage": True,
                "has_security": True,
                "has_balcony": True,
                "has_air_conditioning": True,
                "near_metro": False,
                "has_natural_gas": True,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=1200",
            },
            {
                "title": "شاليه بإطلالة مباشرة على البحر في الجونة",
                "description": "استمتع بإجازة لا تُنسى في شاليه صف أول على اللاجون مباشرة، شاطئ خاص وتراس بانورامي للاسترخاء، متاح للإيجار اليومي والشهري.",
                "owner": users["owner3@sukoon.com"],
                "price": Decimal("3500.00"),
                "price_period": Property.PricePeriod.DAILY,
                "property_type": property_types["chalet"],
                "is_furnished": True,
                "is_verified": True,
                "status": Property.Status.VERIFIED,
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 110,
                "space": "110 م²",
                "floor": 1,
                "rental_period": 1,
                "suitable_for": Property.SuitableFor.ALL,
                "smoking_allowed": True,
                "gov": governorates["البحر الأحمر"],
                "city": cities["البحر الأحمر_الجونة"],
                "district": "حي الفنار",
                "lat": Decimal("27.394900"),
                "lng": Decimal("33.676600"),
                "has_wifi": True,
                "has_elevator": False,
                "has_garage": True,
                "has_security": True,
                "has_balcony": True,
                "has_air_conditioning": True,
                "near_metro": False,
                "has_natural_gas": False,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1200",
            },
            {
                "title": "دوبلكس راقي بحديقة خاصة في سموحة الإسكندرية",
                "description": "دوبلكس واسع يتميز بمدخل خاص وحديقة خارجية مشجرة، قريب من نادي سموحة وطريق 14 مايو، مناسب للعائلات الكبيرة.",
                "owner": users["owner2@sukoon.com"],
                "price": Decimal("22000.00"),
                "price_period": Property.PricePeriod.MONTHLY,
                "property_type": property_types["duplex"],
                "is_furnished": False,
                "is_verified": True,
                "status": Property.Status.VERIFIED,
                "bedrooms": 4,
                "bathrooms": 3,
                "area": 280,
                "space": "280 م²",
                "floor": 1,
                "rental_period": 12,
                "suitable_for": Property.SuitableFor.FAMILIES,
                "smoking_allowed": False,
                "gov": governorates["الإسكندرية"],
                "city": cities["الإسكندرية_سموحة"],
                "district": "شارع فيكتور عمانويل",
                "lat": Decimal("31.215600"),
                "lng": Decimal("29.955300"),
                "has_wifi": False,
                "has_elevator": True,
                "has_garage": True,
                "has_security": True,
                "has_balcony": True,
                "has_air_conditioning": False,
                "near_metro": False,
                "has_natural_gas": True,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1200",
            },
            {
                "title": "شقة جديدة قيد المراجعة في مدينة نصر",
                "description": "شقة سكنية واسعة بالقرب من سيتي ستارز وطريق النصر، موقع استراتيجي وتشطيب حديث ممتاز.",
                "owner": users["owner3@sukoon.com"],
                "price": Decimal("12000.00"),
                "price_period": Property.PricePeriod.MONTHLY,
                "property_type": property_types["apartment"],
                "is_furnished": False,
                "is_verified": False,
                "status": Property.Status.UNDER_REVIEW,
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 145,
                "space": "145 م²",
                "floor": 6,
                "rental_period": 12,
                "suitable_for": Property.SuitableFor.ALL,
                "smoking_allowed": False,
                "gov": governorates["القاهرة"],
                "city": cities["القاهرة_مدينة نصر"],
                "district": "المنطقة الأولى",
                "lat": Decimal("30.062600"),
                "lng": Decimal("31.336900"),
                "has_wifi": False,
                "has_elevator": True,
                "has_garage": False,
                "has_security": False,
                "has_balcony": True,
                "has_air_conditioning": True,
                "near_metro": True,
                "has_natural_gas": True,
                "has_electricity_meter": True,
                "has_water_meter": True,
                "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200",
            },
        ]

        properties = []
        for pdata in props_data:
            prop, _ = Property.objects.get_or_create(
                title=pdata["title"],
                defaults={
                    "description": pdata["description"],
                    "owner": pdata["owner"],
                    "price": pdata["price"],
                    "price_period": pdata["price_period"],
                    "property_type": pdata["property_type"],
                    "is_furnished": pdata["is_furnished"],
                    "is_verified": pdata["is_verified"],
                    "status": pdata["status"],
                    "bedrooms": pdata["bedrooms"],
                    "bathrooms": pdata["bathrooms"],
                    "area": pdata["area"],
                    "space": pdata["space"],
                    "floor": pdata["floor"],
                    "rental_period": pdata["rental_period"],
                    "suitable_for": pdata["suitable_for"],
                    "smoking_allowed": pdata["smoking_allowed"],
                    "governorate": pdata["gov"],
                    "city": pdata["city"],
                    "district": pdata["district"],
                    "latitude": pdata["lat"],
                    "longitude": pdata["lng"],
                    "has_wifi": pdata["has_wifi"],
                    "has_elevator": pdata["has_elevator"],
                    "has_garage": pdata["has_garage"],
                    "has_security": pdata["has_security"],
                    "has_balcony": pdata["has_balcony"],
                    "has_air_conditioning": pdata["has_air_conditioning"],
                    "near_metro": pdata["near_metro"],
                    "has_natural_gas": pdata["has_natural_gas"],
                    "has_electricity_meter": pdata["has_electricity_meter"],
                    "has_water_meter": pdata["has_water_meter"],
                    "main_image": pdata["image"],
                },
            )
            properties.append(prop)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(properties)} properties created."))
        return properties

    def _seed_property_images(self, properties):
        self.stdout.write("  Creating gallery images...")
        gallery_images = [
            "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=800",
            "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=800",
            "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800",
        ]
        count = 0
        for prop in properties:
            for idx, img_url in enumerate(gallery_images):
                PropertyImage.objects.get_or_create(
                    property=prop,
                    name=f"صورة إضافية {idx + 1}",
                    defaults={
                        "image": img_url,
                        "description": f"منظر داخلي للوحدة {prop.title}",
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"    ✓ {count} gallery images created."))

    def _seed_engagement(self, users, properties):
        self.stdout.write("  Creating user favorites, saves, and ratings...")
        p1, p2, p3 = properties[0], properties[1], properties[2]
        t1, t2 = users["tenant1@sukoon.com"], users["tenant2@sukoon.com"]

        # Favorites
        PropertyFavorite.objects.get_or_create(user=t1, property=p1)
        PropertyFavorite.objects.get_or_create(user=t1, property=p2)
        PropertyFavorite.objects.get_or_create(user=t2, property=p1)

        # Saves
        SavedProperty.objects.get_or_create(user=t1, property=p1)
        SavedProperty.objects.get_or_create(user=t2, property=p3)

        # Ratings
        PropertyRating.objects.get_or_create(user=t1, property=p1, defaults={"rating": 5})
        PropertyRating.objects.get_or_create(user=t2, property=p1, defaults={"rating": 4})
        PropertyRating.objects.get_or_create(user=t1, property=p2, defaults={"rating": 5})

    def _seed_visits_and_reviews(self, users, properties):
        self.stdout.write("  Creating visit slots, bookings, and reviews...")
        p1, p2 = properties[0], properties[1]
        t1, t2 = users["tenant1@sukoon.com"], users["tenant2@sukoon.com"]
        today = datetime.date.today()

        # Availability slots
        for day_offset in range(1, 4):
            slot_date = today + datetime.timedelta(days=day_offset)
            OwnerAvailabilitySlot.objects.get_or_create(
                property=p1,
                date=slot_date,
                time=datetime.time(16, 0),
                defaults={"owner": p1.owner, "is_enabled": True},
            )
            OwnerAvailabilitySlot.objects.get_or_create(
                property=p1,
                date=slot_date,
                time=datetime.time(18, 30),
                defaults={"owner": p1.owner, "is_enabled": True},
            )

        # Visits
        v1, _ = PropertyVisit.objects.get_or_create(
            property=p1,
            tenant=t1,
            visit_date=today - datetime.timedelta(days=3),
            visit_time=datetime.time(17, 0),
            defaults={
                "status": PropertyVisit.Status.CONFIRMED,
                "note": "أود معاينة الشقة والتأكد من سرعة الإنترنت",
            },
        )
        PropertyVisit.objects.get_or_create(
            property=p2,
            tenant=t2,
            visit_date=today + datetime.timedelta(days=2),
            visit_time=datetime.time(15, 0),
            defaults={
                "status": PropertyVisit.Status.PENDING,
                "note": "هل الاستوديو متاح للمعانية ظهراً؟",
            },
        )

        # Review
        PropertyVisitReview.objects.get_or_create(
            visit=v1,
            defaults={
                "overall_rating": 5,
                "cleanliness_rating": 5,
                "listing_accuracy_rating": 5,
                "owner_interaction_rating": 5,
                "comment": "المالك في قمة الذوق والشقة تطابق الصور تماماً!",
            },
        )

    def _seed_chat(self, users):
        self.stdout.write("  Creating chat conversations and messages...")
        t1 = users["tenant1@sukoon.com"]
        o1 = users["owner1@sukoon.com"]

        conv, _ = Conversation.objects.get_or_create(
            last_message_at=timezone.now(),
            last_message_preview="تمام، يسعدني استقبالك غداً في تمام الخامسة مساءً.",
        )

        ConversationParticipant.objects.get_or_create(
            conversation=conv,
            user=t1,
            defaults={"unread_count": 0, "last_read_at": timezone.now()},
        )
        ConversationParticipant.objects.get_or_create(
            conversation=conv,
            user=o1,
            defaults={"unread_count": 0, "last_read_at": timezone.now()},
        )

        Message.objects.get_or_create(
            conversation=conv,
            sender=t1,
            content="السلام عليكم، هل الشقة في المعادي متاحة للمعانية هذا الأسبوع؟",
            defaults={"created_at": timezone.now() - datetime.timedelta(hours=2)},
        )
        Message.objects.get_or_create(
            conversation=conv,
            sender=o1,
            content="وعليكم السلام ورحمة الله، نعم أهلاً بك، يمكنك اختيار الموعد المناسب من جدول المواعيد.",
            defaults={"created_at": timezone.now() - datetime.timedelta(hours=1)},
        )
        Message.objects.get_or_create(
            conversation=conv,
            sender=o1,
            content="تمام، يسعدني استقبالك غداً في تمام الخامسة مساءً.",
            defaults={"created_at": timezone.now() - datetime.timedelta(minutes=30)},
        )

    def _seed_notifications_and_devices(self, users, properties):
        self.stdout.write("  Creating device tokens and notifications...")
        t1 = users["tenant1@sukoon.com"]
        o1 = users["owner1@sukoon.com"]

        # Device tokens
        DeviceToken.objects.get_or_create(
            user=t1,
            token="fcm_token_sample_web_client_1234567890",
            defaults={"device_type": DeviceToken.DeviceType.WEB, "device_name": "Chrome on Windows"},
        )
        DeviceToken.objects.get_or_create(
            user=o1,
            token="fcm_token_sample_android_client_0987654321",
            defaults={"device_type": DeviceToken.DeviceType.ANDROID, "device_name": "Samsung Galaxy S24"},
        )

        # Notifications
        notifs = [
            (
                t1,
                Notification.NotificationType.VISIT_ACCEPTED,
                "تمت الموافقة على موعد المعاينة",
                "وافق المالك على موعد المعاينة لشقة المعادي.",
                "visits",
                "calendar",
                False,
            ),
            (
                t1,
                Notification.NotificationType.NEW_MESSAGE,
                "رسالة جديدة من طارق الشريف",
                "تمام، يسعدني استقبالك غداً في تمام الخامسة مساءً.",
                "chat",
                "message-square",
                True,
            ),
            (
                o1,
                Notification.NotificationType.PROPERTY_VERIFIED,
                "تم توثيق إعلانك بنجاح",
                "تمت مراجعة شقة المعادي وتوثيقها بالعلامة الزرقاء.",
                "properties",
                "check-circle",
                False,
            ),
            (
                o1,
                Notification.NotificationType.SECURITY_ALERT,
                "تسجيل دخول جديد",
                "تم تسجيل الدخول إلى حسابك من متصفح Chrome على نظام Windows.",
                "security",
                "shield-alert",
                True,
            ),
        ]

        for user, ntype, title, body, category, icon, is_read in notifs:
            Notification.objects.get_or_create(
                user=user,
                title=title,
                defaults={
                    "notification_type": ntype,
                    "body": body,
                    "category": category,
                    "icon_type": icon,
                    "is_read": is_read,
                    "read_at": timezone.now() if is_read else None,
                    "data": {"property_id": str(properties[0].id)},
                },
            )

    def _seed_content_views(self, users, properties):
        self.stdout.write("  Creating content views...")
        prop_ct = ContentType.objects.get_for_model(Property)
        for prop in properties:
            ContentView.objects.get_or_create(
                content_type=prop_ct,
                object_id=prop.pkid,
                user=users["tenant1@sukoon.com"],
                viewer_ip="192.168.1.100",
                defaults={"last_viewed": timezone.now()},
            )
            ContentView.objects.get_or_create(
                content_type=prop_ct,
                object_id=prop.pkid,
                user=None,
                viewer_ip="10.0.0.5",
                defaults={"last_viewed": timezone.now()},
            )
