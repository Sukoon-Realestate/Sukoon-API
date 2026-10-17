"""Exact, localized advanced-planning errors. Stable API codes are unchanged."""

MESSAGES = {
    "Additional or unconfirmed occupants require assisted review.": (
        "تحتاج حالات وجود مقيمين إضافيين أو عدم تأكيد عدد المقيمين إلى مراجعة بمساعدة"
        " مختص."
    ),
    "Unsupported move action.": "إجراء الانتقال غير مدعوم.",
    "Linked signing, payment and move execution is unavailable.": (
        "التوقيع والدفع وتنفيذ الانتقالات المترابطة غير متاحة."
    ),
    "The outgoing relationship needs a new review.": (
        "تحتاج علاقة الإيجار الحالية إلى مراجعة جديدة."
    ),
    "A supported contract change is needed before an earlier move.": (
        "يلزم تعديل عقد مدعوم قبل الانتقال في موعد أبكر."
    ),
    "The owner must approve the existing replacement availability first.": (
        "يجب أن يعتمد المالك توفر السكن في طلب الاستبدال الحالي أولًا."
    ),
    "The reviewed outgoing relationship must match.": (
        "يجب مطابقة علاقة الإيجار الحالية التي تمت مراجعتها."
    ),
    "Choose one person, exact scope, dates, monthly rent and a budget.": (
        "حدد شخصًا واحدًا ونطاق السكن والتواريخ والإيجار الشهري والميزانية."
    ),
    "Additional suitability constraints require assisted review.": (
        "تحتاج شروط الملاءمة الإضافية إلى مراجعة بمساعدة مختص."
    ),
    "Open your existing move plan.": "افتح خطة انتقالك الحالية.",
    "This action is not available for the move plan.": (
        "هذا الإجراء غير متاح لخطة الانتقال."
    ),
    "Explicit matching consent is required.": "تلزم موافقة صريحة على المطابقة.",
    "Refresh the changed move proposal.": "حدّث مقترح الانتقال الذي تغيرت معطياته.",
    "Respond only for your own account.": "قدم الرد لحسابك فقط.",
    "Choose interested or declined.": "اختر إبداء الاهتمام أو الرفض.",
    "The source inventory needs review.": "تحتاج بيانات السكن المصدر إلى مراجعة.",
    "The offer is unavailable.": "العرض غير متاح.",
    "The current monthly quote is incomplete.": "عرض السعر الشهري الحالي غير مكتمل.",
    "Use an integer within the supported range.": (
        "استخدم عددًا صحيحًا ضمن النطاق المدعوم."
    ),
    "A verified active account is required.": "يلزم حساب نشط وموثق.",
    "This planning service is disabled.": "خدمة التخطيط هذه متوقفة حاليًا.",
    "Refresh and review the current revision.": "حدّث البيانات وراجع النسخة الحالية.",
    "A participant declined. Rebuild and review the affected package.": (
        "رفض أحد المشاركين. أعد إعداد الحزمة المتأثرة ومراجعتها."
    ),
    "A participant has not authorized a multi-property package.": (
        "لم يوافق أحد المشاركين على حزمة تضم عدة عقارات."
    ),
    "A quote does not reserve inventory.": "عرض السعر لا يحجز مكان الإقامة.",
    "A selected owner quote cannot be combined.": (
        "لا يمكن دمج أحد عروض الأسعار المختارة مع عروض أخرى."
    ),
    "Accommodation scope and dates must satisfy each participant.": (
        "يجب أن يلائم نوع مكان الإقامة والتواريخ متطلبات كل مشارك."
    ),
    (
        "Acknowledge that completed individual leases can remain valid when "
        "others decline."
    ): ("أقر بأن عقود الإيجار الفردية المكتملة قد تظل سارية إذا رفض الآخرون."),
    "Allocate each current authorized participant at most once.": (
        "خصص مكان إقامة لكل مشارك حالي مخول مرة واحدة على الأكثر."
    ),
    "Allocations overlap physical accommodation.": (
        "تتداخل التخصيصات في أماكن الإقامة الفعلية."
    ),
    "An allocation exceeds an individual rent or deposit limit.": (
        "يتجاوز أحد التخصيصات الحد الفردي للإيجار أو التأمين."
    ),
    "An owner quote expired, changed or was withdrawn.": (
        "انتهت صلاحية أحد عروض الملاك أو تغير أو سُحب."
    ),
    "Bid lines overlap physical accommodation.": (
        "تتداخل بنود العرض في أماكن الإقامة الفعلية."
    ),
    "Canonical pricing has no quantity tiers.": (
        "التسعير الأساسي المسجل لا يتضمن شرائح للكميات."
    ),
    "Choose an exact supported accommodation scope.": (
        "اختر نوعًا محددًا ومدعومًا لمكان الإقامة."
    ),
    "Current ownership authority changed.": "تغيرت صلاحية المالك الحالية.",
    "Each assignment needs participant_id and line_id.": (
        "يحتاج كل تخصيص إلى معرف المشارك ومعرف بند العرض."
    ),
    (
        "Each current member must review and authorize their own requirements and"
        " reduced disclosure."
    ): (
        "يجب أن يراجع كل عضو حالي متطلباته ويوافق بنفسه عليها وعلى مشاركة ملخصها "
        "المحدود."
    ),
    (
        "Group membership changed. Create a new tender so new members cannot "
        "inherit private history or consent."
    ): (
        "تغيرت عضوية المجموعة. أنشئ مناقصة جديدة حتى لا يرث الأعضاء الجدد السجل الخاص"
        " أو الموافقات السابقة."
    ),
    "Inventory must match the demand city and monthly billing.": (
        "يجب أن يطابق مكان الإقامة مدينة الطلب وأن يكون إيجاره شهريًا."
    ),
    "Only an allocated participant can supply their own decision.": (
        "يمكن فقط للمشارك الذي خُصص له مكان إقامة تقديم قراره بنفسه."
    ),
    "Only monthly EGP rent and explicit canonical deposits are supported.": (
        "المدعوم هو الإيجار الشهري بالجنيه المصري وقيمة التأمين المحددة في العرض "
        "الأساسي فقط."
    ),
    "Only the current group coordinator can create a tender.": (
        "يمكن فقط لمنسق المجموعة الحالي إنشاء مناقصة."
    ),
    "Package consent cannot be supplied for another person.": (
        "لا يمكن تقديم الموافقة على الحزمة نيابة عن شخص آخر."
    ),
    (
        "Package execution awaits verified canonical terms handoff. This proposal"
        " reserves nothing and creates no lease."
    ): (
        "ينتظر تنفيذ الحزمة التحقق من تمرير شروطها إلى مسار الإيجار الأساسي. هذا "
        "المقترح لا يحجز أي مكان ولا ينشئ عقد إيجار."
    ),
    "Provide 1 to 12 participant and bid-line assignments.": (
        "أضف من تخصيص واحد إلى 12 تخصيصًا، يربط كل منها مشاركًا ببند عرض."
    ),
    "Publish a current housing request first.": "انشر طلب سكن ساريًا أولًا.",
    "Quantity tiers require a homogeneous set of monthly units.": (
        "تتطلب شرائح الكميات وحدات ذات تسعير شهري أساسي متساوٍ."
    ),
    "Quote 1 to 12 exact rental selections.": (
        "حدد من خيار إيجار واحد إلى 12 خيارًا محددًا لعرض السعر."
    ),
    "Refresh the current tender and permissions.": "حدّث المناقصة الحالية والصلاحيات.",
    "Restore a current source group and request before amendment.": (
        "تأكد من سريان المجموعة وطلب السكن الأصليين قبل التعديل."
    ),
    "Review the current published demand.": "راجع طلب السكن المنشور حاليًا.",
    "Review this exact package and choose accept or decline.": (
        "راجع هذه الحزمة المحددة واختر القبول أو الرفض."
    ),
    "Supply exact from_quantity, to_quantity and rent_minor fields.": (
        "حدد حقول بداية الكمية ونهايتها وقيمة الإيجار بالقرش فقط."
    ),
    "Supply the supported requirement fields only.": (
        "أرسل حقول المتطلبات المدعومة فقط."
    ),
    "The accepted quantity does not satisfy this bid.": (
        "الكمية المقبولة لا تحقق شروط هذا العرض."
    ),
    "The authenticated participant supplies only their own response.": (
        "يقدم المشارك المسجل دخوله إجابته الشخصية فقط."
    ),
    "The canonical offer terms changed.": "تغيرت شروط عرض الإيجار الأساسي.",
    "The demand changed; review a new package.": "تغير طلب السكن؛ راجع حزمة جديدة.",
    "The demand or group changed; create a new reviewed package.": (
        "تغير طلب السكن أو المجموعة؛ أنشئ حزمة جديدة وراجعها."
    ),
    "The exact allocation terms changed.": "تغيرت شروط التخصيص المحددة.",
    "The owner must configure an explicit deposit.": (
        "يجب أن يحدد المالك قيمة التأمين صراحةً."
    ),
    "The physical inventory map changed.": "تغير توزيع أماكن الإقامة الفعلية.",
    "The proposed completion is below an individual requirement.": (
        "عدد المشاركين المشمولين في المقترح أقل من الحد المطلوب لأحدهم."
    ),
    "The published snapshot changed.": "تغيرت النسخة المنشورة من الطلب.",
    "The quantity tier requires review.": "تحتاج شريحة الكمية إلى المراجعة.",
    (
        "This pilot does not support extra fees, inventory dependencies or "
        "unstructured quote conditions."
    ): (
        "هذه المرحلة التجريبية لا تدعم الرسوم الإضافية أو اشتراط اختيار أماكن إقامة "
        "أخرى أو شروط التسعير غير المنظمة."
    ),
    "This pilot supports at most 12 current group members.": (
        "تدعم هذه المرحلة التجريبية 12 عضوًا حاليًا في المجموعة كحد أقصى."
    ),
    "This quote can no longer be withdrawn.": "لم يعد سحب عرض السعر هذا متاحًا.",
    "Tiers must cover all quantities without gaps or overlap.": (
        "يجب أن تغطي الشرائح جميع الكميات دون فجوات أو تداخل."
    ),
    "Tiers must cover every offered unit.": "يجب أن تغطي الشرائح كل الوحدات المعروضة.",
    "Use a boolean.": "استخدم قيمة صحيحة أو خاطئة.",
    "Use a future timezone-aware time within 30 days.": (
        "اختر وقتًا مستقبليًا خلال 30 يومًا مع تحديد المنطقة الزمنية."
    ),
    "Use an exclusive end date within one year of arrival.": (
        "اختر تاريخ مغادرة خلال سنة من الوصول؛ يوم المغادرة غير مشمول في الإقامة."
    ),
    "Use canonical, all_units or marginal pricing.": (
        "اختر التسعير الأساسي أو تسعير جميع الوحدات أو تسعير الشرائح التدريجي."
    ),
    "Use true or false.": "استخدم قيمة صحيحة أو خاطئة.",
    "Use your authorized request for this group.": (
        "استخدم طلب السكن الذي تملك صلاحية استخدامه لهذه المجموعة."
    ),
    "Verified owned inventory is required to read tender demand.": (
        "يلزم امتلاك مكان إقامة موثّق للاطلاع على طلب المناقصة."
    ),
    "conditional_package is unsupported.": "تنفيذ الحزمة المشروط غير مدعوم.",
    "conditional_package is unsupported; no commitments were made.": (
        "تنفيذ الحزمة المشروط غير مدعوم؛ لم تُنشأ أي التزامات."
    ),
    "Only the current group coordinator can organize a living lab.": (
        "يمكن لمنسق المجموعة الحالي فقط تنظيم مختبر للسكن المشترك."
    ),
    "Only documented fields for your own action are accepted.": (
        "تقبل فقط الحقول المحددة للإجراء الخاص بك."
    ),
    "This pilot supports existing groups with two to six participants.": (
        "تدعم هذه المرحلة التجريبية المجموعات الحالية التي تضم من مشاركين إلى ستة "
        "مشاركين."
    ),
    "The daily group planning limit has been reached.": (
        "وصلت المجموعة إلى الحد اليومي لمحاولات التخطيط."
    ),
    "Choose a current canonical shortlist item.": (
        "اختر عرض سكن حاليًا من القائمة المختصرة للمجموعة."
    ),
    "Choose a period of one to 730 days.": "اختر مدة من يوم واحد إلى 730 يومًا.",
    "Use at most four short, voluntary household proposals.": (
        "أضف بحد أقصى أربعة مقترحات منزلية قصيرة واختيارية."
    ),
    "Refresh the current group, access period, and lab state.": (
        "حدث بيانات المجموعة وفترة عضويتك وحالة مختبر السكن."
    ),
    "Choose provided or omitted.": "اختر تقديم بياناتك أو تركها دون تقديم.",
    "Use a private requirements object.": "أدخل المتطلبات الخاصة بالتنسيق المطلوب.",
    "Personally accept this specific computation purpose.": (
        "وافق بنفسك على استخدام بياناتك لهذا الغرض المحدد من الحساب."
    ),
    "Supply the documented private bounds and room choices.": (
        "أدخل الحدود الخاصة واختيارات الغرف المطلوبة."
    ),
    "Use a nonnegative integer number of minor units.": (
        "أدخل عددًا صحيحًا غير سالب من القروش."
    ),
    "Use ordered dates and an explicit private-room choice.": (
        "رتب تاريخ البداية والنهاية وحدد صراحة حاجتك إلى غرفة خاصة."
    ),
    "Choose room identities from this exact offer.": (
        "اختر الغرف المتاحة ضمن هذا العرض نفسه."
    ),
    "Omitted inputs must not contain private values.": (
        "عند اختيار عدم تقديم البيانات، يجب ترك القيم الخاصة فارغة."
    ),
    "The bounded group scenario limit has been reached.": (
        "وصلت المجموعة إلى الحد المسموح لمحاولات حساب الترتيبات."
    ),
    "This input revision already has a result.": (
        "حُسبت نتيجة لهذا الإصدار من البيانات بالفعل."
    ),
    "Choose a current candidate and your own explicit response.": (
        "اختر ترتيبًا مقترحًا حاليًا وحدد ردك الشخصي بوضوح."
    ),
    "Choose the current unanimously accepted arrangement.": (
        "اختر الترتيب الحالي الذي وافق عليه جميع المشاركين."
    ),
    "This planning action is unsupported.": "إجراء التخطيط هذا غير متاح.",
    "The selected quote changed. Start a fresh reviewed lab.": (
        "تغير عرض السكن المختار. ابدأ مختبرًا جديدًا بعد مراجعة العرض."
    ),
    "The explicit offer capacity must cover every participant.": (
        "يجب أن تتسع السعة المعلنة للعرض لجميع المشاركين."
    ),
    "This pilot requires an entire property, room group, or room.": (
        "تتطلب هذه المرحلة التجريبية عرضًا لعقار كامل أو مجموعة غرف أو غرفة."
    ),
    "Explicit capacities for one to six rooms are required.": (
        "يجب تحديد سعة كل غرفة مع اختيار غرفة واحدة إلى ست غرف."
    ),
    "The owner must specify deposit terms before this calculation.": (
        "يجب أن يحدد المالك شروط التأمين قبل إجراء هذا الحساب."
    ),
    "The room map or private input snapshot changed.": (
        "تغير توزيع الغرف أو إصدار البيانات الخاصة المستخدم في الحساب."
    ),
    "This release supports planning only.": "هذا الإصدار يدعم التخطيط فقط.",
    "Choose a request from this company.": "اختر طلبًا تابعًا لهذه الشركة.",
    "Choose requests, staff, or offers.": "اختر الطلبات أو الموظفين أو العروض.",
    "The source records changed. Duplicate and review fresh inputs.": (
        "تغيّرت السجلات المصدرية. انسخ السيناريو وراجع البيانات المحدثة."
    ),
    "Record an observed lifecycle date, not a future move.": (
        "سجّل تاريخًا فعليًا لدورة حياة الأصل، وليس موعد نقل مستقبليًا."
    ),
    "Choose a room in the canonical property inventory.": (
        "اختر غرفة من مخزون العقار المسجل."
    ),
    "This physical identity is closed.": "تم إغلاق سجل هذا الأصل الفعلي.",
    (
        "The date must preserve the recorded location and observations. Choose a "
        "later date."
    ): ("يجب أن يحافظ التاريخ على المكان والملاحظات المسجلة. اختر تاريخًا لاحقًا."),
    "Choose a supported physical lifecycle action.": (
        "اختر إجراءً مدعومًا لدورة حياة الأصل."
    ),
    "This item is closed. Use its successor for current observations.": (
        "سجل هذا الأصل مغلق. استخدم سجل الأصل البديل للملاحظات الحالية."
    ),
    "An observation cannot describe a future date.": (
        "لا يمكن تسجيل ملاحظة عن تاريخ مستقبلي."
    ),
    "Select an explicit observed condition.": "اختر حالة معاينة واضحة.",
    "Select an existing condition report, handover, or maintenance request.": (
        "اختر تقرير حالة أو محضر تسليم أو طلب صيانة قائمًا."
    ),
    (
        "The source tenancy and reported observation date must match the item's "
        "location period."
    ): ("يجب أن يتطابق عقد المصدر وتاريخ الملاحظة مع فترة وجود الأصل في المكان."),
    "Choose distinct evidence linked to this source.": (
        "اختر أدلة غير مكررة ومرتبطة بهذا المصدر."
    ),
    "Evidence must belong to this source and have a completed safe scan.": (
        "يجب أن تتبع الأدلة هذا المصدر وأن يكتمل فحص سلامتها."
    ),
    "Review a published offer.": "راجع عرضًا منشورًا.",
    "The selected capacity needs confirmation.": "السعة المحددة تحتاج إلى تأكيد.",
    ("This planning release supports one to three whole future monthly " "periods."): (
        "يدعم هذا الإصدار التخطيط لمدة شهر إلى ثلاثة أشهر كاملة مستقبلية."
    ),
    "Choose between 1 and 40 distinct current records.": (
        "اختر من سجل واحد إلى ٤٠ سجلًا حاليًا غير مكرر."
    ),
    "Choose between 1 and 12 distinct current records.": (
        "اختر من سجل واحد إلى ١٢ سجلًا حاليًا غير مكرر."
    ),
    (
        "Full-coverage planning requires one active eligible staff record for "
        "every requested person."
    ): ("يتطلب التخطيط لجميع الأفراد سجل موظف نشط ومؤهل لكل شخص في الطلب."),
    (
        "A confirmed placement needs its authorized transition workflow before "
        "this planning release can relocate it."
    ): (
        "تتطلب الإقامة المؤكدة مسار الانتقال المصرح به قبل إعادة تخصيصها في هذا "
        "الإصدار."
    ),
    "Configure the current turnover and date policy before planning.": (
        "اضبط سياسة تجهيز الوحدة والتواريخ الحالية قبل التخطيط."
    ),
    "One or more selected offers are unavailable.": (
        "عرض واحد أو أكثر من العروض المحددة غير متاح."
    ),
    "Use supported explicit constraints.": "استخدم قيودًا واضحة ومدعومة.",
    (
        "The cap must be a nonnegative minor-unit amount within current "
        "uncommitted policy limits."
    ): (
        "يجب أن يكون الحد مبلغًا غير سالب بالقرش وضمن حدود السياسة الحالية غير "
        "الملتزم بها."
    ),
    (
        "Location constraints must reference selected staff and canonical "
        "selected properties."
    ): ("يجب ربط قيود المكان بالموظفين والعقارات المسجلة المحددة."),
}

FIELD_LABELS = {
    "Lease Id": "معرف الإيجار",
    "Source Id": "معرف المصدر",
    "Source Transition Id": "طلب الاستبدال المصدر",
    "Criteria": "متطلبات السكن",
    "Decision": "القرار",
    "Expected Revision": "النسخة المتوقعة",
    "Max Deposit Minor": "الحد الأقصى للتأمين",
    "Max Gap Days": "الحد الأقصى للأيام دون سكن",
    "Turnover Days": "أيام تجهيز السكن",
    "Matching Consent": "موافقة المطابقة",
    "Snapshot Digest": "مرجع النسخة التي تمت مراجعتها",
    "Selections": "اختيارات السكن",
    "Selection": "اختيار السكن",
    "Action": "الإجراء",
    "Room Id": "معرف الغرفة",
    "Property Id": "معرف العقار",
    "Source Kind": "نوع المصدر",
    "Occurred On": "تاريخ الملاحظة",
    "Installed On": "تاريخ التركيب",
    "Removed On": "تاريخ الإزالة",
    "Evidence Id": "معرف الدليل",
    "Evidence Ids": "معرفات الأدلة",
    "Group Id": "معرف المجموعة",
    "Request Id": "معرف الطلب",
    "Participant Id": "معرف المشارك",
    "Staff Ids": "الموظفون",
    "Offer Ids": "العروض",
    "Requirements": "الاحتياجات",
    "Assignments": "توزيع السكن",
    "Allocations": "تخصيصات السكن",
    "Pricing Rule": "قاعدة التسعير",
    "Price Tiers": "شرائح الأسعار",
    "Deposit Minor": "مبلغ التأمين",
    "Rent Minor": "مبلغ الإيجار",
    "Title": "العنوان",
    "Note": "الملاحظة",
    "Budget": "الميزانية",
    "Start On": "تاريخ البداية",
    "End On": "تاريخ النهاية",
    "Participant Ids": "المشاركون",
    "Rules": "القواعد",
    "Location Rules": "قيود الموقع",
    "Period Months": "مدة الإيجار بالأشهر",
    "Supersedes Id": "المعرف السابق",
    "Purpose Consent": "الموافقة على الاستخدام",
    "Room Requirements": "احتياجات الغرفة",
    "Disclosure Consent": "موافقة الإفصاح",
    "Independent Ack": "إقرار الالتزام الفردي",
}

from .advanced_housing_v2_translations import MESSAGES as V2_MESSAGES

MESSAGES.update(V2_MESSAGES)
