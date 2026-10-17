"""Localized policy and mock workflow validation messages."""

MESSAGES = {
    "Enable the explicitly configured mock provider to continue.": (
        "فعّل مزود المحاكاة المهيأ صراحة للمتابعة."
    ),
    "Confirm the outgoing handover before reserving linked accommodation.": (
        "أكد تسليم السكن السابق قبل حجز السكن المرتبط."
    ),
    "Every participant must express interest in this move proposal.": (
        "يجب أن يبدي كل مشارك اهتمامه بمقترح الانتقال هذا."
    ),
    "Possession has not been returned for this accommodation.": (
        "لم يتم تأكيد إخلاء هذا السكن وتسليمه بعد."
    ),
    "Provide your own current inputs before choosing disclosure.": (
        "قدم مدخلاتك الحالية بنفسك قبل اختيار الإفصاح."
    ),
    "Only your selected room preferences and quiet windows may be disclosed.": (
        "يمكن الإفصاح فقط عن اختيارات الغرف وفترات الهدوء التي تحددها بنفسك."
    ),
    "Personally approve this exact disclosure preview.": (
        "وافق بنفسك على معاينة الإفصاح هذه تحديدًا."
    ),
    "Choose a documented household change scenario.": (
        "اختر أحد سيناريوهات تغيير ترتيبات المنزل المحددة."
    ),
    "Choose an arrangement belonging to this lab.": "اختر ترتيبًا تابعًا لهذا المختبر.",
    "Counterfactual arrangements cannot authorize a rental handoff.": (
        "لا تسمح الترتيبات الافتراضية بالانتقال إلى إجراء إيجار."
    ),
    "Each participant must separately approve this exact canonical cost proposal.": (
        "يجب أن يوافق كل مشارك بشكل مستقل على مقترح التكاليف الرسمي نفسه."
    ),
    "Choose a current participant for the departure assumption.": (
        "اختر مشاركًا حاليًا لافتراض المغادرة."
    ),
    "A quote-change scenario must use the same canonical offer.": (
        "يجب أن يستخدم سيناريو تغير السعر عرض السكن نفسه."
    ),
    "Restore the selected offer in the canonical shortlist first.": (
        "أعد العرض المختار إلى القائمة المختصرة للمجموعة أولًا."
    ),
    "Choose current canonical rooms for the vacancy assumption.": (
        "اختر غرفًا حالية من العرض لافتراض عدم الإتاحة."
    ),
    "Use at most eight weekly time windows.": "أضف بحد أقصى ثماني فترات أسبوعية.",
    "Use a documented cost allocation policy.": "استخدم إحدى سياسات توزيع التكاليف المحددة.",
    "Choose equal, weighted, or negotiated shares.": (
        "اختر حصصًا متساوية أو موزونة أو مبالغ متفاوضًا عليها."
    ),
    "Use the documented household arrangement fields.": "استخدم حقول ترتيبات المنزل المحددة.",
    "Use at most twelve voluntary household tasks.": (
        "أضف بحد أقصى اثنتي عشرة مهمة منزلية اختيارية."
    ),
    "Use a short visitor proposal and a nonnegative shared expense amount.": (
        "أدخل مقترحًا قصيرًا للزيارات ومبلغ مصروفات مشتركة غير سالب."
    ),
    "Specify a weekday and start and end minutes for each window.": (
        "حدد اليوم ووقت البداية والنهاية لكل فترة."
    ),
    "Weekly windows must stay within one day and have ordered times.": (
        "يجب أن تبقى كل فترة ضمن يوم واحد وأن يسبق وقت البداية وقت النهاية."
    ),
    "Every proposed participant needs an explicit integer share or weight.": (
        "يجب تحديد حصة أو وزن صحيح لكل مشارك مقترح."
    ),
    "Each household task needs its identity, person, and weekly time.": (
        "حدد هوية كل مهمة منزلية والمشارك المقترح وموعدها الأسبوعي."
    ),
    "Use unique household task identities and current participants.": (
        "استخدم هويات غير مكررة للمهام وأعضاء المجموعة الحاليين."
    ),
    "Household task times must fit within a day.": (
        "يجب أن تكون أوقات المهمة المنزلية ضمن يوم واحد."
    ),
    "Negotiated shares must sum exactly to the current quoted component.": (
        "يجب أن يساوي مجموع الحصص المتفاوض عليها مبلغ المكون الحالي في العرض تمامًا."
    ),
    "Unequal shares must respect the disclosed maximum ratio.": (
        "يجب أن تلتزم الحصص غير المتساوية بالنسبة القصوى المعلنة."
    ),
    "Use a nonnegative private shared expense limit.": (
        "أدخل حدًا خاصًا غير سالب للمصروفات المشتركة."
    ),
    "Personally choose only household tasks proposed for you.": (
        "اختر بنفسك المهام المنزلية المقترحة لك فقط."
    ),
    "Choose an entire property, room group, or room for shared planning.": (
        "اختر عقارًا كاملًا أو مجموعة غرف أو غرفة للتخطيط المشترك."
    ),
    "Use explicit room capacities within the configured planning limits.": (
        "استخدم سعات واضحة للغرف ضمن الحدود المحددة للتخطيط."
    ),
    "Use an existing group with at least two people within the configured planning limit.": (
        "استخدم مجموعة حالية تضم شخصين على الأقل ضمن الحد المحدد للتخطيط."
    ),
    "A calculation is already queued for this scenario.": (
        "يوجد حساب في قائمة الانتظار لهذا السيناريو بالفعل."
    ),
    "A common-fault hypothesis requires reports from two units within thirty days.": (
        "فرضية العطل المشترك تتطلب تقارير من وحدتين خلال ثلاثين يوماً."
    ),
    "Accept as an advisory observation, reject, or mark inconclusive.": (
        "اقبل كملاحظة استرشادية أو ارفض أو حدد أن النتيجة غير حاسمة."
    ),
    "Activate the named employee accounts before requesting personal execution consent.": (
        "فعّل حسابات الموظفين المحددين قبل طلب موافقتهم الشخصية على التنفيذ."
    ),
    "An independent approver must decide this accommodation package.": (
        "يجب أن يبت معتمد مستقل في حزمة السكن هذه."
    ),
    "Assign an active independent approver before submitting this package.": (
        "عيّن معتمداً مستقلاً نشطاً قبل إرسال هذه الحزمة."
    ),
    "Choose a document source for this item's property.": "اختر مصدر مستند لعقار هذا العنصر.",
    "Choose a per-person commute limit from 1 to 360 minutes.": (
        "اختر حداً لزمن انتقال الفرد من دقيقة إلى ٣٦٠ دقيقة."
    ),
    "Choose a reported fault category without attributing responsibility.": (
        "اختر فئة العطل المبلغ عنه دون نسب المسؤولية."
    ),
    "Choose a reported quality and confirm the physical item explicitly.": (
        "اختر جودة الالتقاط المعلنة وأكد العنصر الفعلي صراحة."
    ),
    "Choose a supported decision action.": "اختر إجراء قرار مدعوماً.",
    "Choose a supported documented system type.": "اختر نوع نظام موثق ومدعوماً.",
    "Choose a supported transport assumption.": "اختر افتراض انتقال مدعوماً.",
    "Choose an independently validated current plan.": "اختر خطة حالية تم التحقق منها بشكل مستقل.",
    "Choose approval, rejection, or changes requested.": "اختر الموافقة أو الرفض أو طلب تعديلات.",
    "Choose canonical selected properties for the unavailable scenario.": (
        "اختر العقارات الأساسية المحددة لسيناريو عدم الإتاحة."
    ),
    "Choose two to eight distinct authorized observations.": (
        "اختر من ملاحظتين إلى ثماني ملاحظات مصرح بها ومختلفة."
    ),
    "Choose two to twenty distinct items in the documented shared system.": (
        "اختر من عنصرين إلى عشرين عنصراً مختلفاً في النظام المشترك الموثق."
    ),
    "Compare distinct scenarios for the same company request.": (
        "قارن سيناريوهات مختلفة لنفس طلب الشركة."
    ),
    "Compare two or three authorized scenarios.": "قارن سيناريوهين أو ثلاثة مصرح بها.",
    "Every company agreement must be signed before the first company payment.": (
        "يجب توقيع جميع اتفاقيات الشركة قبل أول دفعة للشركة."
    ),
    "Every exact company package needs its independent commercial approval.": (
        "تحتاج كل حزمة شركة محددة إلى موافقتها التجارية المستقلة."
    ),
    "Explain the declared work site and cost assumptions.": (
        "وضح افتراضات موقع العمل والتكلفة المعلنة."
    ),
    "Insufficient or changed evidence cannot become an accepted observation.": (
        "لا يمكن قبول أدلة غير كافية أو متغيرة كملاحظة."
    ),
    "Link an acknowledged inspection or resolved maintenance record in this building.": (
        "اربط فحصاً تم الإقرار به أو سجل صيانة محلولاً في هذا المبنى."
    ),
    "Only the current corporate signer or payment authorizer can perform this step.": (
        "يمكن فقط لمفوض التوقيع أو الدفع الحالي للشركة تنفيذ هذه الخطوة."
    ),
    "Prepare and independently approve the canonical company packages first.": (
        "جهز حزم الشركة الأساسية واعتمدها بشكل مستقل أولاً."
    ),
    "Reconcile the original uncertain provider instruction first.": (
        "تحقق أولًا من نتيجة التعليمة الأصلية غير المؤكدة لدى مزود الخدمة."
    ),
    "Record an inspected common issue, separate issues, or an inconclusive outcome.": (
        "سجل مشكلة مشتركة تم فحصها أو مشكلات منفصلة أو نتيجة غير حاسمة."
    ),
    "Refresh and review the current decision snapshot.": "حدّث وراجع نسخة القرار الحالية.",
    "Refresh the expired commercial package before proceeding.": (
        "جدّد الحزمة التجارية المنتهية قبل المتابعة."
    ),
    "Rerun only an analysis of this same physical item.": (
        "أعد تشغيل تحليل لهذا العنصر الفعلي نفسه فقط."
    ),
    "Review the current company authority and exact decision.": (
        "راجع صلاحية الشركة الحالية والقرار المحدد."
    ),
    "Supply a bounded reported capture timestamp.": "أدخل وقت الالتقاط المعلن ضمن الطول المسموح.",
    "Supply a bounded text assumption.": "أدخل افتراضاً نصياً ضمن الطول المسموح.",
    "Supply a nonnegative estimate in minor units or leave it unknown.": (
        "أدخل تقديراً غير سالب بأصغر وحدة نقدية أو اتركه غير معروف."
    ),
    "Supply a supported reported capture context.": "أدخل سياق التقاط معلناً ومدعوماً.",
    "Supply valid coordinates or leave them unknown.": "أدخل إحداثيات صالحة أو اتركها غير معروفة.",
    "The canonical company hold expired. Reconcile and prepare a current package.": (
        "انتهت مهلة حجز الشركة الأساسي. تحقق من الحالة وجهز حزمة حالية."
    ),
    "The canonical company package changed.": "تغيرت حزمة الشركة الأساسية.",
    "The evidence snapshot changed. Request a new comparison.": (
        "تغيرت نسخة الأدلة. اطلب مقارنة جديدة."
    ),
    "The recorded warranty end must follow its start.": (
        "يجب أن يلي تاريخ انتهاء الضمان المسجل تاريخ بدايته."
    ),
    "The selected plan no longer satisfies its hard constraints.": (
        "الخطة المحددة لم تعد تستوفي القيود الملزمة."
    ),
    "The source records changed.": "تغيرت السجلات المصدرية.",
    "The warranty document source changed. Record a new reference.": (
        "تغير مصدر مستند الضمان. سجل مرجعاً جديداً."
    ),
    "This execution participant no longer has current authority.": (
        "لم يعد لهذا المشارك في التنفيذ صلاحية حالية."
    ),
    "This finding already has a preserved review. Rerun for a new version.": (
        "لهذه النتيجة مراجعة محفوظة بالفعل. أعد التحليل للحصول على نسخة جديدة."
    ),
    "This investigation has a preserved closure decision.": "لهذا التحقيق قرار إغلاق محفوظ.",
    "Use documented observations from this registered shared system.": (
        "استخدم ملاحظات موثقة من هذا النظام المشترك المسجل."
    ),
    "Use the supported versioned planning assumptions.": (
        "استخدم افتراضات التخطيط المدعومة ذات الإصدار المحدد."
    ),
    "Agreed rent and deposit must use valid integer minor units.": (
        "يجب إدخال الإيجار والتأمين المتفق عليهما بوحدات نقدية صغرى صحيحة وصالحة."
    ),
    "Choose a supported mock provider outcome.": "اختر نتيجة مدعومة لمزود الخدمة التجريبي.",
    "Choose signing or first-invoice payment.": "اختر التوقيع أو سداد الفاتورة الأولى.",
    "Conditional execution requires every agreement signed before payment.": (
        "يتطلب التنفيذ المشروط توقيع جميع العقود وتسوية النتائج غير المؤكدة قبل السداد."
    ),
    "Each quoted accommodation unit can be allocated only once.": (
        "يمكن تخصيص كل وحدة سكنية في العرض مرة واحدة فقط."
    ),
    "Every allocated participant must accept the package.": (
        "يجب أن يقبل كل مشارك مخصص له سكن هذه الحزمة."
    ),
    "Every execution leg needs a unique stable key.": (
        "يجب أن يكون لكل جزء من خطة التنفيذ معرّف ثابت وفريد."
    ),
    "Every execution leg requires named consent actors.": (
        "يتطلب كل جزء من خطة التنفيذ حسابات محددة لتقديم الموافقة."
    ),
    "Every intended occupant needs a current named account and consent.": (
        "يحتاج كل ساكن مقصود إلى حساب محدد وسارٍ وموافقة شخصية."
    ),
    "Every required actor must accept this exact execution plan.": (
        "يجب أن يقبل كل طرف مطلوب هذه النسخة المحددة من خطة التنفيذ."
    ),
    "Every required participant must have a current verified account.": (
        "يجب أن يملك كل مشارك مطلوب حسابًا موثقًا وساريًا."
    ),
    "Execution consent must be supplied by the required actor personally.": (
        "يجب أن يقدم الطرف المطلوب موافقته على التنفيذ بنفسه."
    ),
    "Execution requires distinct named owner and tenant accounts.": (
        "يتطلب التنفيذ حسابين محددين ومختلفين للمالك والمستأجر."
    ),
    "Explicitly accept preserving confirmed obligations and unchanged prices.": (
        "وافق صراحةً على استمرار الالتزامات المؤكدة دون تغيير الأسعار."
    ),
    "Only an agreement signer may authorize a signature.": (
        "لا يمكن اعتماد التوقيع إلا بواسطة أحد الموقّعين على العقد."
    ),
    "Only the actual owner or tenant can sign their agreement.": (
        "لا يمكن توقيع العقد إلا بواسطة المالك أو المستأجر الفعلي."
    ),
    "Only the canonical payer may authorize this payment.": (
        "لا يمكن اعتماد هذه الدفعة إلا بواسطة المسؤول عن السداد في السجل الأصلي."
    ),
    "Only the canonical tenant can authorize this rental payment.": (
        "لا يمكن اعتماد دفعة الإيجار إلا بواسطة المستأجر المسجل في العقد الأصلي."
    ),
    "Only the current coordinator can prepare the execution proposal.": (
        "يمكن للمنسق الحالي وحده إعداد مقترح التنفيذ."
    ),
    "Prepare this execution before signing or payment.": "أعدّ خطة التنفيذ قبل التوقيع أو السداد.",
    "Prepared execution terms cannot be silently reconsented.": (
        "لا يمكن تجديد الموافقة على شروط التنفيذ المعدّة دون مسار مراجعة صريح."
    ),
    "Provide a supported execution mode and 1 to 24 exact legs.": (
        "حدد نمط تنفيذ مدعومًا ومن جزء واحد إلى ٢٤ جزءًا محددًا بدقة."
    ),
    "Reconcile uncertain outcomes before releasing accommodation.": (
        "تحقق من النتائج غير المؤكدة قبل تحرير السكن."
    ),
    "Resolve every binding or uncertain canonical outcome before closing.": (
        "عالج جميع النتائج الملزمة أو غير المؤكدة في السجلات الأصلية قبل الإغلاق."
    ),
    "Review current arrival and exclusive departure dates.": (
        "راجع تاريخ الوصول وتاريخ المغادرة الذي لا يشمل الإقامة في يومه."
    ),
    "Review the current agreement and unexpired hold.": (
        "راجع العقد الحالي والحجز المؤقت غير المنتهي."
    ),
    "Review the current exact agreement before this step.": (
        "راجع النسخة الحالية والمحددة من العقد قبل هذه الخطوة."
    ),
    "Review the exact current first invoice and payable amount.": (
        "راجع الفاتورة الأولى الحالية والمبلغ المستحق بدقة."
    ),
    "Review the exact execution snapshot and partial-resolution policy.": (
        "راجع نسخة التنفيذ المحددة وسياسة معالجة الإكمال الجزئي."
    ),
    "Review the exact package before execution.": "راجع الحزمة المحددة قبل التنفيذ.",
    "The accepted tender package changed before preparation.": (
        "تغيرت حزمة المناقصة المقبولة قبل الإعداد."
    ),
    "The canonical first rental invoice is not payable.": (
        "لا يمكن سداد فاتورة الإيجار الأولى في السجل الأصلي حاليًا."
    ),
    "The exact package allocation changed.": "تغير توزيع الحزمة المحدد.",
    "The execution inventory is no longer verified and available.": (
        "لم يعد السكن المحدد للتنفيذ موثقًا ومتاحًا."
    ),
    "The execution snapshot changed.": "تغيرت نسخة خطة التنفيذ.",
    "The original provider instruction has different inputs.": (
        "تختلف المدخلات عن التعليمة الأصلية المرسلة إلى مزود الخدمة."
    ),
    "The reviewed inventory selection changed.": "تغير اختيار السكن الذي تمت مراجعته.",
    "This execution action is not currently authorized.": (
        "هذا الإجراء في خطة التنفيذ غير مصرح به حاليًا."
    ),
    "This execution leg belongs to another participant.": (
        "هذا الجزء من خطة التنفيذ يخص مشاركًا آخر."
    ),
    "This quote already has a replacement.": "يوجد عرض بديل لهذا العرض بالفعل.",
    "Unknown execution action.": "إجراء التنفيذ غير معروف.",
    "Unsupported execution source.": "مصدر التنفيذ غير مدعوم.",
    "Only a queued package search can be dispatched again.": (
        "يمكن إعادة إرسال البحث عن الحزم إذا كان في قائمة الانتظار فقط."
    ),
    "A participant requested withdrawal after a binding or partially signed step.": (
        "طلب مشارك الانسحاب بعد خطوة ملزمة أو توقيع جزئي."
    ),
    (
        "Support must review canonical lease change authority. Confirmed leases and prices "
        "remain unchanged."
    ): (
        "يجب أن يراجع الدعم صلاحية تعديل العقد الأصلي. تظل العقود والأسعار المؤكدة دون تغيير."
    ),
    "Choose a supported recorded item status.": "اختر حالة مسجلة ومدعومة للعنصر.",
    "A status correction must follow the recorded lifecycle history.": (
        "يجب أن يلي تصحيح الحالة تاريخ دورة العنصر المسجل."
    ),
}
