"""
AI Centers Hub Bot — i18n translations for sales funnel
6 languages: ru, en, ka, tr, kk, uz
"""

I18N = {
    # ─── Step 1: Welcome + business type ───
    "welcome": {
        "ru": "👋 {name}, привет!\n\nЯ помогу <b>автоматизировать ваш бизнес</b> за 5 минут.\n\nКакой у вас бизнес?",
        "en": "👋 Hi {name}!\n\nI'll help <b>automate your business</b> in 5 minutes.\n\nWhat's your business?",
        "ka": "👋 გამარჯობა {name}!\n\nდაგეხმარებით <b>ბიზნესის ავტომატიზაციაში</b> 5 წუთში.\n\nრა ბიზნესი გაქვთ?",
        "tr": "👋 Merhaba {name}!\n\nİşletmenizi 5 dakikada <b>otomatikleştirmenize</b> yardımcı olacağım.\n\nİşletmeniz ne?",
        "kk": "👋 Сәлем {name}!\n\nБизнесіңізді 5 минутта <b>автоматтандыруға</b> көмектесемін.\n\nБизнесіңіз қандай?",
        "uz": "👋 Salom {name}!\n\nBiznesingizni 5 daqiqada <b>avtomatlashtirish</b>ga yordam beraman.\n\nBiznesingiz nima?",
    },

    # Business type buttons
    "biz_restaurant": {
        "ru": "🍽 Ресторан / кафе", "en": "🍽 Restaurant / café",
        "ka": "🍽 რესტორანი / კაფე", "tr": "🍽 Restoran / kafe",
        "kk": "🍽 Мейрамхана / кафе", "uz": "🍽 Restoran / kafe",
    },
    "biz_clinic": {
        "ru": "🏥 Клиника", "en": "🏥 Clinic",
        "ka": "🏥 კლინიკა", "tr": "🏥 Klinik",
        "kk": "🏥 Клиника", "uz": "🏥 Klinika",
    },
    "biz_salon": {
        "ru": "💇 Салон красоты", "en": "💇 Beauty salon",
        "ka": "💇 სილამაზის სალონი", "tr": "💇 Güzellik salonu",
        "kk": "💇 Сұлулық салоны", "uz": "💇 Go'zallik saloni",
    },
    "biz_shop": {
        "ru": "🛍 Магазин", "en": "🛍 Shop / E-commerce",
        "ka": "🛍 მაღაზია", "tr": "🛍 Mağaza / E-ticaret",
        "kk": "🛍 Дүкен", "uz": "🛍 Do'kon",
    },
    "biz_services": {
        "ru": "🏗 Услуги / B2B", "en": "🏗 Services / B2B",
        "ka": "🏗 მომსახურება / B2B", "tr": "🏗 Hizmetler / B2B",
        "kk": "🏗 Қызметтер / B2B", "uz": "🏗 Xizmatlar / B2B",
    },
    "biz_other": {
        "ru": "📦 Другое", "en": "📦 Other",
        "ka": "📦 სხვა", "tr": "📦 Diğer",
        "kk": "📦 Басқа", "uz": "📦 Boshqa",
    },

    # ─── Step 2: Pain — leads question ───
    "leads_question": {
        "ru": "✅ {niche} — отличная ниша!\n\n<b>Сколько заявок/обращений в день</b> вы обрабатываете вручную?",
        "en": "✅ {niche} — great niche!\n\n<b>How many leads/inquiries per day</b> do you handle manually?",
        "ka": "✅ {niche} — შესანიშნავი ნიშა!\n\n<b>რამდენ მოთხოვნას</b> ამუშავებთ ხელით დღეში?",
        "tr": "✅ {niche} — harika bir alan!\n\nGünde <b>kaç başvuruyu</b> manuel işliyorsunuz?",
        "kk": "✅ {niche} — тамаша салада!\n\nКүніне <b>қанша өтінімді</b> қолмен өңдейсіз?",
        "uz": "✅ {niche} — ajoyib soha!\n\nKuniga <b>nechta so'rovni</b> qo'lda ishlaysiz?",
    },
    "leads_10": {
        "ru": "📩 До 10", "en": "📩 Up to 10",
        "ka": "📩 10-მდე", "tr": "📩 10'a kadar",
        "kk": "📩 10-ға дейін", "uz": "📩 10 gacha",
    },
    "leads_50": {
        "ru": "📩 10-50", "en": "📩 10-50",
        "ka": "📩 10-50", "tr": "📩 10-50",
        "kk": "📩 10-50", "uz": "📩 10-50",
    },
    "leads_100": {
        "ru": "📩 50+", "en": "📩 50+",
        "ka": "📩 50+", "tr": "📩 50+",
        "kk": "📩 50+", "uz": "📩 50+",
    },
    "leads_unknown": {
        "ru": "🤷 Не знаю точно", "en": "🤷 Not sure",
        "ka": "🤷 ზუსტად არ ვიცი", "tr": "🤷 Tam bilmiyorum",
        "kk": "🤷 Нақты білмеймін", "uz": "🤷 Aniq bilmayman",
    },

    # ─── Step 3: Case studies per niche ───
    "case_restaurant": {
        "ru": "🍽 <b>Кейс: Ресторан в Тбилиси</b>\n\nПодключили AI-бота для бронирования столов и приёма заказов.\n\n📊 <b>Результат:</b>\n• Бот принимает 80% бронирований автоматически\n• Экономит <b>2-3 часа</b> хостес каждый день\n• Отвечает клиентам в WhatsApp и Telegram <b>24/7</b>\n• Меню, адрес, часы работы — без звонков\n\n💰 Окупился за <b>2 недели</b>.",
        "en": "🍽 <b>Case: Restaurant in Tbilisi</b>\n\nConnected AI bot for table reservations and order taking.\n\n📊 <b>Result:</b>\n• Bot handles 80% of reservations automatically\n• Saves <b>2-3 hours</b> of host time daily\n• Answers clients on WhatsApp & Telegram <b>24/7</b>\n• Menu, address, hours — no phone calls needed\n\n💰 Paid for itself in <b>2 weeks</b>.",
        "ka": "🍽 <b>ქეისი: რესტორანი თბილისში</b>\n\nAI ბოტი მაგიდის დაჯავშნისა და შეკვეთების მისაღებად.\n\n📊 <b>შედეგი:</b>\n• ბოტი ამუშავებს ჯავშნების 80%-ს ავტომატურად\n• ზოგავს <b>2-3 საათს</b> ყოველდღე\n• პასუხობს კლიენტებს WhatsApp და Telegram-ში <b>24/7</b>\n• მენიუ, მისამართი, საათები — ზარების გარეშე\n\n💰 ანაზღაურდა <b>2 კვირაში</b>.",
        "tr": "🍽 <b>Vaka: Tiflis'te Restoran</b>\n\nMasa rezervasyonu ve sipariş alma için AI bot bağlandı.\n\n📊 <b>Sonuç:</b>\n• Bot rezervasyonların %80'ini otomatik işliyor\n• Günde <b>2-3 saat</b> tasarruf\n• WhatsApp ve Telegram'da <b>7/24</b> cevap veriyor\n• Menü, adres, çalışma saatleri — aramasız\n\n💰 <b>2 haftada</b> kendini amorti etti.",
        "kk": "🍽 <b>Кейс: Тбилисидегі мейрамхана</b>\n\nАI бот үстел брондау мен тапсырыс қабылдау үшін қосылды.\n\n📊 <b>Нәтиже:</b>\n• Бот брондаулардың 80%-ын автоматты өңдейді\n• Күн сайын <b>2-3 сағат</b> үнемдейді\n• WhatsApp пен Telegram-да <b>24/7</b> жауап береді\n\n💰 <b>2 аптада</b> өтелді.",
        "uz": "🍽 <b>Keys: Tbilisidagi restoran</b>\n\nStol band qilish va buyurtma qabul qilish uchun AI bot ulandi.\n\n📊 <b>Natija:</b>\n• Bot bandlarning 80% ni avtomatik ishlaydi\n• Kuniga <b>2-3 soat</b> tejaydi\n• WhatsApp va Telegram'da <b>24/7</b> javob beradi\n\n💰 <b>2 haftada</b> o'zini oqladi.",
    },
    "case_clinic": {
        "ru": "🏥 <b>Кейс: Стоматологическая клиника</b>\n\nAI-бот заменил администратора на входящих обращениях.\n\n📊 <b>Результат:</b>\n• <b>0 пропущенных</b> обращений — бот отвечает мгновенно\n• Запись на приём, напоминания, FAQ — автоматически\n• Пациенты получают ответы в <b>3 секунды</b> вместо 15 минут\n• Администратор занимается только сложными случаями\n\n💰 Экономия: <b>$800/мес</b> на зарплате.",
        "en": "🏥 <b>Case: Dental Clinic</b>\n\nAI bot replaced front desk for incoming inquiries.\n\n📊 <b>Result:</b>\n• <b>Zero missed</b> inquiries — bot replies instantly\n• Appointments, reminders, FAQ — automatic\n• Patients get answers in <b>3 seconds</b> instead of 15 min\n• Admin only handles complex cases\n\n💰 Saving: <b>$800/mo</b> on salary.",
        "ka": "🏥 <b>ქეისი: სტომატოლოგიური კლინიკა</b>\n\nAI ბოტმა შეცვალა ადმინისტრატორი შემოსულ მოთხოვნებზე.\n\n📊 <b>შედეგი:</b>\n• <b>0 გამოტოვებული</b> მოთხოვნა — ბოტი მყისიერად პასუხობს\n• ჩაწერა, შეხსენებები, FAQ — ავტომატურად\n• პაციენტები პასუხს იღებენ <b>3 წამში</b>\n\n💰 ეკონომია: <b>$800/თვე</b>.",
        "tr": "🏥 <b>Vaka: Diş Kliniği</b>\n\nAI bot gelen başvurularda resepsiyonun yerini aldı.\n\n📊 <b>Sonuç:</b>\n• <b>Sıfır kaçırılan</b> başvuru — bot anında cevaplıyor\n• Randevu, hatırlatma, SSS — otomatik\n• Hastalar <b>3 saniyede</b> cevap alıyor\n\n💰 Tasarruf: <b>$800/ay</b> maaştan.",
        "kk": "🏥 <b>Кейс: Стоматологиялық клиника</b>\n\nAI бот кіріс өтінімдерде администраторды алмастырды.\n\n📊 <b>Нәтиже:</b>\n• <b>0 жіберіп алған</b> өтінім\n• Жазылу, еске салу, FAQ — автоматты\n• Пациенттер жауапты <b>3 секундта</b> алады\n\n💰 Үнемдеу: <b>$800/ай</b>.",
        "uz": "🏥 <b>Keys: Stomatologiya klinikasi</b>\n\nAI bot kiruvchi so'rovlarda administratorni almashtirdi.\n\n📊 <b>Natija:</b>\n• <b>0 ta o'tkazilgan</b> so'rov\n• Yozilish, eslatmalar, FAQ — avtomatik\n• Bemorlar javobni <b>3 soniyada</b> oladi\n\n💰 Tejash: <b>$800/oy</b>.",
    },
    "case_salon": {
        "ru": "💇 <b>Кейс: Салон красоты</b>\n\nБот принимает записи в Instagram, WhatsApp и Telegram.\n\n📊 <b>Результат:</b>\n• Клиенты записываются <b>24/7</b> без администратора\n• Бот показывает свободные слоты и цены\n• Напоминания за 2 часа — <b>на 40% меньше</b> неприходов\n• Мастера видят расписание в реальном времени\n\n💰 +15 записей/неделю, которые раньше уходили конкурентам.",
        "en": "💇 <b>Case: Beauty Salon</b>\n\nBot takes bookings via Instagram, WhatsApp & Telegram.\n\n📊 <b>Result:</b>\n• Clients book <b>24/7</b> without receptionist\n• Bot shows available slots and prices\n• 2-hour reminders — <b>40% fewer</b> no-shows\n• Stylists see schedule in real time\n\n💰 +15 bookings/week that used to go to competitors.",
        "ka": "💇 <b>ქეისი: სილამაზის სალონი</b>\n\nბოტი იღებს ჩაწერებს Instagram, WhatsApp და Telegram-ში.\n\n📊 <b>შედეგი:</b>\n• კლიენტები იწერებიან <b>24/7</b> ადმინისტრატორის გარეშე\n• ბოტი აჩვენებს თავისუფალ სლოტებს და ფასებს\n• შეხსენებები 2 საათით ადრე — <b>40%-ით ნაკლები</b> გამოუცხადებლობა\n\n💰 +15 ჩაწერა/კვირაში.",
        "tr": "💇 <b>Vaka: Güzellik Salonu</b>\n\nBot Instagram, WhatsApp ve Telegram'dan randevu alıyor.\n\n📊 <b>Sonuç:</b>\n• Müşteriler <b>7/24</b> resepsiyonsuz randevu alıyor\n• Bot müsait saatleri ve fiyatları gösteriyor\n• 2 saat önceden hatırlatma — <b>%40 daha az</b> gelmeme\n\n💰 Haftada +15 randevu.",
        "kk": "💇 <b>Кейс: Сұлулық салоны</b>\n\nБот Instagram, WhatsApp пен Telegram арқылы жазылымдар қабылдайды.\n\n📊 <b>Нәтиже:</b>\n• Клиенттер <b>24/7</b> жазылады\n• 2 сағат бұрын еске салу — <b>40% аз</b> келмеу\n\n💰 Аптасына +15 жазылым.",
        "uz": "💇 <b>Keys: Go'zallik saloni</b>\n\nBot Instagram, WhatsApp va Telegram orqali yozilishlarni qabul qiladi.\n\n📊 <b>Natija:</b>\n• Mijozlar <b>24/7</b> yoziladi\n• 2 soat oldin eslatma — <b>40% kam</b> kelmaslik\n\n💰 Haftasiga +15 yozilish.",
    },
    "case_shop": {
        "ru": "🛍 <b>Кейс: Интернет-магазин</b>\n\nAI-бот консультирует клиентов и помогает с выбором.\n\n📊 <b>Результат:</b>\n• Отвечает на вопросы о товарах, наличии, доставке\n• <b>+30%</b> к конверсии корзины\n• Обрабатывает возвраты и рекламации автоматически\n• Работает на сайте, в Telegram и WhatsApp\n\n💰 Заменяет 2 операторов поддержки.",
        "en": "🛍 <b>Case: Online Store</b>\n\nAI bot consults customers and helps choose products.\n\n📊 <b>Result:</b>\n• Answers questions about products, stock, delivery\n• <b>+30%</b> cart conversion\n• Handles returns and complaints automatically\n• Works on website, Telegram & WhatsApp\n\n💰 Replaces 2 support operators.",
        "ka": "🛍 <b>ქეისი: ონლაინ მაღაზია</b>\n\nAI ბოტი კონსულტაციას უწევს მყიდველებს.\n\n📊 <b>შედეგი:</b>\n• პასუხობს საქონლის, მარაგის, მიწოდების შესახებ\n• კალათის კონვერსია <b>+30%</b>\n• ავტომატურად ამუშავებს დაბრუნებებს\n\n💰 ცვლის 2 ოპერატორს.",
        "tr": "🛍 <b>Vaka: Online Mağaza</b>\n\nAI bot müşterilere danışmanlık yapıyor.\n\n📊 <b>Sonuç:</b>\n• Ürün, stok, teslimat sorularını cevaplıyor\n• Sepet dönüşümü <b>+%30</b>\n• İadeleri otomatik işliyor\n\n💰 2 destek operatörünün yerini alıyor.",
        "kk": "🛍 <b>Кейс: Интернет-дүкен</b>\n\nAI бот клиенттерге кеңес береді.\n\n📊 <b>Нәтиже:</b>\n• Тауарлар, қор, жеткізу жөнінде жауап береді\n• Себет конверсиясы <b>+30%</b>\n\n💰 2 операторды алмастырады.",
        "uz": "🛍 <b>Keys: Internet-do'kon</b>\n\nAI bot mijozlarga maslahat beradi.\n\n📊 <b>Natija:</b>\n• Tovar, zaxira, yetkazib berish haqida javob beradi\n• Savat konversiyasi <b>+30%</b>\n\n💰 2 operatorni almashtiradi.",
    },
    "case_services": {
        "ru": "🏗 <b>Кейс: Сервисная компания</b>\n\nAI-бот квалифицирует лиды и собирает заявки.\n\n📊 <b>Результат:</b>\n• Собирает данные клиента: имя, задача, бюджет, сроки\n• Передаёт горячих лидов менеджеру\n• Отвечает на типовые вопросы (цены, сроки, портфолио)\n• Менеджер тратит время только на <b>готовых</b> клиентов\n\n💰 Экономит <b>3 часа/день</b> на обработке входящих.",
        "en": "🏗 <b>Case: Service Company</b>\n\nAI bot qualifies leads and collects applications.\n\n📊 <b>Result:</b>\n• Collects client data: name, task, budget, timeline\n• Passes hot leads to manager\n• Answers common questions (prices, timeline, portfolio)\n• Manager spends time only on <b>ready</b> clients\n\n💰 Saves <b>3 hours/day</b> on incoming requests.",
        "ka": "🏗 <b>ქეისი: სერვისული კომპანია</b>\n\nAI ბოტი ლიდებს კვალიფიცირებს და განაცხადებს აგროვებს.\n\n📊 <b>შედეგი:</b>\n• აგროვებს კლიენტის მონაცემებს: სახელი, ამოცანა, ბიუჯეტი\n• ცხელ ლიდებს მენეჯერს გადასცემს\n• პასუხობს ტიპიურ კითხვებს\n\n💰 ზოგავს <b>3 საათს/დღეში</b>.",
        "tr": "🏗 <b>Vaka: Hizmet Şirketi</b>\n\nAI bot potansiyel müşterileri nitelendirir ve başvuru toplar.\n\n📊 <b>Sonuç:</b>\n• Müşteri verilerini toplar: ad, görev, bütçe, süre\n• Sıcak leadleri yöneticiye aktarır\n• Standart soruları cevaplar\n\n💰 Günde <b>3 saat</b> tasarruf.",
        "kk": "🏗 <b>Кейс: Сервистік компания</b>\n\nAI бот лидтерді біліктілендіреді және өтінімдер жинайды.\n\n📊 <b>Нәтиже:</b>\n• Клиент деректерін жинайды\n• Ыстық лидтерді менеджерге жібереді\n\n💰 Күніне <b>3 сағат</b> үнемдейді.",
        "uz": "🏗 <b>Keys: Xizmat kompaniyasi</b>\n\nAI bot lidlarni malakali qiladi va arizalar yig'adi.\n\n📊 <b>Natija:</b>\n• Mijoz ma'lumotlarini yig'adi\n• Issiq lidlarni menejerga uzatadi\n\n💰 Kuniga <b>3 soat</b> tejaydi.",
    },
    "case_other": {
        "ru": "🤖 <b>AI-сотрудник для любого бизнеса</b>\n\nНаши боты работают в 20+ нишах:\n\n• Отвечают клиентам в <b>3 секунды</b>\n• Принимают заявки, записи, заказы\n• Работают в Telegram, WhatsApp, на сайте\n• Знают всё о вашем бизнесе — обучаются за 5 минут\n\n💰 От <b>$19/мес</b>. Замещает 1-2 сотрудников.",
        "en": "🤖 <b>AI employee for any business</b>\n\nOur bots work in 20+ industries:\n\n• Reply to clients in <b>3 seconds</b>\n• Accept applications, bookings, orders\n• Work on Telegram, WhatsApp, website\n• Learn everything about your business in 5 minutes\n\n💰 From <b>$19/mo</b>. Replaces 1-2 employees.",
        "ka": "🤖 <b>AI თანამშრომელი ნებისმიერი ბიზნესისთვის</b>\n\nჩვენი ბოტები 20+ ინდუსტრიაში მუშაობენ:\n\n• კლიენტებს <b>3 წამში</b> პასუხობენ\n• იღებენ განაცხადებს, ჩაწერებს, შეკვეთებს\n• მუშაობენ Telegram, WhatsApp, საიტზე\n\n💰 <b>$19/თვე</b>-დან. ცვლის 1-2 თანამშრომელს.",
        "tr": "🤖 <b>Her işletme için AI çalışanı</b>\n\nBotlarımız 20+ sektörde çalışıyor:\n\n• Müşterilere <b>3 saniyede</b> cevap veriyor\n• Başvuru, randevu, sipariş alıyor\n• Telegram, WhatsApp, web sitesinde çalışıyor\n\n💰 <b>$19/ay</b>'dan başlıyor. 1-2 çalışanın yerini alıyor.",
        "kk": "🤖 <b>Кез келген бизнес үшін AI қызметкер</b>\n\nБіздің боттар 20+ салада жұмыс істейді:\n\n• Клиенттерге <b>3 секундта</b> жауап береді\n• Өтінімдер, жазылымдар, тапсырыстар қабылдайды\n\n💰 <b>$19/ай</b>-дан. 1-2 қызметкерді алмастырады.",
        "uz": "🤖 <b>Har qanday biznes uchun AI xodim</b>\n\nBotlarimiz 20+ sohada ishlaydi:\n\n• Mijozlarga <b>3 soniyada</b> javob beradi\n• Arizalar, yozilishlar, buyurtmalar qabul qiladi\n\n💰 <b>$19/oy</b>dan. 1-2 xodimni almashtiradi.",
    },

    # ─── Step 4: Offer ───
    "savings": {
        "leads_10":      {"ru": "1-2 часа/день", "en": "1-2 hours/day", "ka": "1-2 საათი/დღეში", "tr": "günde 1-2 saat", "kk": "1-2 сағат/күн", "uz": "kuniga 1-2 soat"},
        "leads_50":      {"ru": "3-5 часов/день", "en": "3-5 hours/day", "ka": "3-5 საათი/დღეში", "tr": "günde 3-5 saat", "kk": "3-5 сағат/күн", "uz": "kuniga 3-5 soat"},
        "leads_100":     {"ru": "1-2 сотрудника", "en": "1-2 employees", "ka": "1-2 თანამშრომელი", "tr": "1-2 çalışan", "kk": "1-2 қызметкер", "uz": "1-2 xodim"},
        "leads_unknown": {"ru": "до 3 часов/день", "en": "up to 3 hours/day", "ka": "3 საათამდე/დღეში", "tr": "günde 3 saate kadar", "kk": "3 сағатқа дейін/күн", "uz": "kuniga 3 soatgacha"},
    },
    "offer": {
        "ru": "⚡ <b>AI-сотрудник сэкономит вам {savings}</b>\n\nЗапустим за 5 минут. Первые <b>3 дня бесплатно</b>.\nНе подойдёт — просто отключите.\n\nЧто выберете?",
        "en": "⚡ <b>AI employee will save you {savings}</b>\n\nLaunch in 5 minutes. First <b>3 days free</b>.\nDoesn't work out — just cancel.\n\nWhat will you choose?",
        "ka": "⚡ <b>AI თანამშრომელი დაზოგავს {savings}</b>\n\nგაშვება 5 წუთში. პირველი <b>3 დღე უფასოდ</b>.\nარ მოგეწონათ — უბრალოდ გამორთეთ.\n\nრას აირჩევთ?",
        "tr": "⚡ <b>AI çalışan size {savings} kazandıracak</b>\n\n5 dakikada başlatın. İlk <b>3 gün ücretsiz</b>.\nİşe yaramazsa — iptal edin.\n\nNe seçersiniz?",
        "kk": "⚡ <b>AI қызметкер сізге {savings} үнемдейді</b>\n\n5 минутта іске қосамыз. Алғашқы <b>3 күн тегін</b>.\nСізге сәйкес келмесе — өшіріңіз.\n\nНе таңдайсыз?",
        "uz": "⚡ <b>AI xodim sizga {savings} tejaydi</b>\n\n5 daqiqada ishga tushiramiz. Birinchi <b>3 kun bepul</b>.\nYoqmasa — o'chiring.\n\nNimani tanlaysiz?",
    },

    # ─── Step 5: CTA buttons ───
    "btn_try_free": {
        "ru": "🚀 Попробовать бесплатно (3 дня)", "en": "🚀 Try free (3 days)",
        "ka": "🚀 სცადეთ უფასოდ (3 დღე)", "tr": "🚀 Ücretsiz deneyin (3 gün)",
        "kk": "🚀 Тегін байқап көріңіз (3 күн)", "uz": "🚀 Bepul sinab ko'ring (3 kun)",
    },
    "btn_pricing": {
        "ru": "💰 Посмотреть тарифы", "en": "💰 View pricing",
        "ka": "💰 ტარიფების ნახვა", "tr": "💰 Fiyatları görün",
        "kk": "💰 Тарифтерді көру", "uz": "💰 Narxlarni ko'rish",
    },
    "btn_question": {
        "ru": "❓ Задать вопрос", "en": "❓ Ask a question",
        "ka": "❓ კითხვის დასმა", "tr": "❓ Soru sorun",
        "kk": "❓ Сұрақ қою", "uz": "❓ Savol berish",
    },

    # ─── Demo result ───
    "demo_intro": {
        "ru": "🎉 <b>Отлично!</b>\n\nВот демо-бот — попробуйте как AI отвечает клиентам.\n\nА если у вас есть сайт — я могу создать бота <b>прямо сейчас</b>, обученного на вашем бизнесе. За 5 минут. Бесплатно.",
        "en": "🎉 <b>Great!</b>\n\nHere's a demo bot — try how AI responds to customers.\n\nIf you have a website — I can create a bot <b>right now</b>, trained on your business. In 5 minutes. Free.",
        "ka": "🎉 <b>შესანიშნავია!</b>\n\nაი დემო ბოტი — სცადეთ როგორ პასუხობს AI კლიენტებს.\n\nთუ საიტი გაქვთ — შემიძლია ბოტი <b>ახლავე</b> შევქმნა, თქვენს ბიზნესზე მორგებული. 5 წუთში. უფასოდ.",
        "tr": "🎉 <b>Harika!</b>\n\nİşte demo bot — AI'ın müşterilere nasıl cevap verdiğini deneyin.\n\nWeb siteniz varsa — işletmenize özel bir bot <b>hemen şimdi</b> oluşturabilirim. 5 dakikada. Ücretsiz.",
        "kk": "🎉 <b>Тамаша!</b>\n\nМіне демо-бот — AI клиенттерге қалай жауап беретінін байқап көріңіз.\n\nСайтыңыз бар ма? — <b>дәл қазір</b> сіздің бизнесіңізге бот жасай аламын. 5 минутта. Тегін.",
        "uz": "🎉 <b>Ajoyib!</b>\n\nMana demo-bot — AI mijozlarga qanday javob berishini sinab ko'ring.\n\nSaytingiz bormi? — biznesingiz uchun botni <b>hoziroq</b> yarataman. 5 daqiqada. Bepul.",
    },
    "btn_open_demo": {
        "ru": "🤖 Открыть демо-бота", "en": "🤖 Open demo bot",
        "ka": "🤖 დემო ბოტის გახსნა", "tr": "🤖 Demo botu açın",
        "kk": "🤖 Демо-ботты ашу", "uz": "🤖 Demo-botni ochish",
    },
    "btn_create_site": {
        "ru": "🌐 Создать бота с вашим сайтом", "en": "🌐 Create bot from your website",
        "ka": "🌐 ბოტის შექმნა თქვენი საიტით", "tr": "🌐 Web sitenizden bot oluşturun",
        "kk": "🌐 Сайтыңыздан бот жасау", "uz": "🌐 Saytingizdan bot yaratish",
    },
    "btn_go_pricing": {
        "ru": "💰 Сразу к тарифам", "en": "💰 Go to pricing",
        "ka": "💰 ტარიფებზე გადასვლა", "tr": "💰 Fiyatlara git",
        "kk": "💰 Тарифтерге өту", "uz": "💰 Narxlarga o'tish",
    },

    # ─── Pricing ───
    "pricing_title": {
        "ru": "💰 <b>Тарифы AI Centers</b>", "en": "💰 <b>AI Centers Pricing</b>",
        "ka": "💰 <b>AI Centers ტარიფები</b>", "tr": "💰 <b>AI Centers Fiyatlar</b>",
        "kk": "💰 <b>AI Centers тарифтері</b>", "uz": "💰 <b>AI Centers narxlari</b>",
    },
    "pricing_starter_label": {
        "ru": "⭐ Starter — $149 + $19/мес", "en": "⭐ Starter — $149 + $19/mo",
        "ka": "⭐ Starter — $149 + $19/თვე", "tr": "⭐ Starter — $149 + $19/ay",
        "kk": "⭐ Starter — $149 + $19/ай", "uz": "⭐ Starter — $149 + $19/oy",
    },
    "pricing_starter_note": {
        "ru": "← 90% клиентов начинают здесь", "en": "← 90% of clients start here",
        "ka": "← კლიენტების 90% აქედან იწყებს", "tr": "← Müşterilerin %90'ı buradan başlıyor",
        "kk": "← Клиенттердің 90%-ы осыдан бастайды", "uz": "← Mijozlarning 90% shu yerdan boshlaydi",
    },
    "pricing_footer": {
        "ru": "💡 Все тарифы: настройка + первый месяц. Отмена в любой момент.",
        "en": "💡 All plans: setup + first month. Cancel anytime.",
        "ka": "💡 ყველა ტარიფი: დაყენება + პირველი თვე. გაუქმება ნებისმიერ დროს.",
        "tr": "💡 Tüm planlar: kurulum + ilk ay. İstediğiniz zaman iptal edin.",
        "kk": "💡 Барлық тарифтер: баптау + бірінші ай. Кез келген уақытта бас тарту.",
        "uz": "💡 Barcha tariflar: sozlash + birinchi oy. Istalgan vaqtda bekor qilish.",
    },
    "btn_try_free_short": {
        "ru": "🆓 Сначала попробовать бесплатно", "en": "🆓 Try free first",
        "ka": "🆓 ჯერ უფასოდ სცადეთ", "tr": "🆓 Önce ücretsiz deneyin",
        "kk": "🆓 Алдымен тегін байқап көріңіз", "uz": "🆓 Avval bepul sinab ko'ring",
    },
    "btn_help_choose": {
        "ru": "❓ Помогите выбрать", "en": "❓ Help me choose",
        "ka": "❓ არჩევაში დამეხმარეთ", "tr": "❓ Seçmeme yardım edin",
        "kk": "❓ Таңдауға көмектесіңіз", "uz": "❓ Tanlashga yordam bering",
    },

    # ─── Payment ───
    "payment_choose": {
        "ru": "🎯 <b>Тариф {plan}</b>\n\nНастройка: {setup} (разово)\nПодписка: {monthly}\n\nВыберите способ оплаты:",
        "en": "🎯 <b>Plan {plan}</b>\n\nSetup: {setup} (one-time)\nSubscription: {monthly}\n\nChoose payment method:",
        "ka": "🎯 <b>ტარიფი {plan}</b>\n\nდაყენება: {setup} (ერთჯერადი)\nგამოწერა: {monthly}\n\nაირჩიეთ გადახდის მეთოდი:",
        "tr": "🎯 <b>Plan {plan}</b>\n\nKurulum: {setup} (tek seferlik)\nAbonelik: {monthly}\n\nÖdeme yöntemi seçin:",
        "kk": "🎯 <b>Тариф {plan}</b>\n\nБаптау: {setup} (бір рет)\nЖазылым: {monthly}\n\nТөлем әдісін таңдаңыз:",
        "uz": "🎯 <b>Tarif {plan}</b>\n\nSozlash: {setup} (bir martalik)\nObuna: {monthly}\n\nTo'lov usulini tanlang:",
    },
    "btn_pay_stars": {
        "ru": "⭐ Оплатить {stars} Stars", "en": "⭐ Pay {stars} Stars",
        "ka": "⭐ გადახდა {stars} Stars", "tr": "⭐ {stars} Stars öde",
        "kk": "⭐ {stars} Stars төлеу", "uz": "⭐ {stars} Stars to'lash",
    },
    "btn_crypto": {
        "ru": "₿ Криптовалюта", "en": "₿ Crypto",
        "ka": "₿ კრიპტოვალუტა", "tr": "₿ Kripto",
        "kk": "₿ Криптовалюта", "uz": "₿ Kriptovalyuta",
    },
    "btn_bank": {
        "ru": "💳 Банковский перевод", "en": "💳 Bank transfer",
        "ka": "💳 საბანკო გადარიცხვა", "tr": "💳 Banka havalesi",
        "kk": "💳 Банктік аударым", "uz": "💳 Bank o'tkazmasi",
    },
    "btn_back_pricing": {
        "ru": "← Назад к тарифам", "en": "← Back to pricing",
        "ka": "← ტარიფებზე დაბრუნება", "tr": "← Fiyatlara dön",
        "kk": "← Тарифтерге оралу", "uz": "← Narxlarga qaytish",
    },

    # ─── After payment ───
    "payment_success": {
        "ru": "🎉 Оплата прошла! {stars} ⭐ — спасибо!\n\nТеперь у тебя безлимит{period}. Пиши что угодно! 🚀",
        "en": "🎉 Payment successful! {stars} ⭐ — thank you!\n\nYou now have unlimited access{period}. Ask anything! 🚀",
        "ka": "🎉 გადახდა წარმატებულია! {stars} ⭐ — მადლობა!\n\nახლა შეუზღუდავი წვდომა გაქვთ{period}. დაწერეთ რაც გინდათ! 🚀",
        "tr": "🎉 Ödeme başarılı! {stars} ⭐ — teşekkürler!\n\nArtık sınırsız erişiminiz var{period}. İstediğinizi yazın! 🚀",
        "kk": "🎉 Төлем сәтті! {stars} ⭐ — рахмет!\n\nЕнді шексіз қолжетімділік{period}. Не қаласаңыз жазыңыз! 🚀",
        "uz": "🎉 To'lov muvaffaqiyatli! {stars} ⭐ — rahmat!\n\nEndi cheksiz foydalanish{period}. Xohlagan narsani yozing! 🚀",
    },

    # ─── Objection handler ───
    "ask_question": {
        "ru": "💬 <b>Задайте любой вопрос!</b>\n\nНапример:\n• Подойдёт ли для моего бизнеса?\n• Чем отличается от обычного чат-бота?\n• Как быстро настраивается?\n• Можно ли попробовать бесплатно?\n\nПросто напишите — я отвечу 👇",
        "en": "💬 <b>Ask any question!</b>\n\nFor example:\n• Will it work for my business?\n• How is it different from a regular chatbot?\n• How fast is the setup?\n• Can I try it for free?\n\nJust type — I'll answer 👇",
        "ka": "💬 <b>დასვით ნებისმიერი კითხვა!</b>\n\nმაგალითად:\n• ჩემს ბიზნესს მოერგება?\n• რით განსხვავდება ჩვეულებრივი ჩატბოტისგან?\n• რამდენად სწრაფად ყენდება?\n• შეიძლება უფასოდ ვცადო?\n\nუბრალოდ დაწერეთ 👇",
        "tr": "💬 <b>Herhangi bir soru sorun!</b>\n\nÖrneğin:\n• İşletmem için uygun mu?\n• Normal chatbottan farkı ne?\n• Kurulum ne kadar sürer?\n• Ücretsiz deneyebilir miyim?\n\nYazmanız yeterli 👇",
        "kk": "💬 <b>Кез келген сұрақ қойыңыз!</b>\n\nМысалы:\n• Менің бизнесіме сәйкес пе?\n• Қарапайым чат-боттан қандай айырмашылығы бар?\n• Баптау қаншалықты тез?\n• Тегін байқап көруге бола ма?\n\nЖазыңыз 👇",
        "uz": "💬 <b>Istalgan savolni bering!</b>\n\nMasalan:\n• Biznesimga mos keladimi?\n• Oddiy chatbotdan farqi nima?\n• Sozlash qanchalik tez?\n• Bepul sinab ko'rish mumkinmi?\n\nYozing 👇",
    },
    "btn_more_question": {
        "ru": "❓ Ещё вопрос", "en": "❓ Another question",
        "ka": "❓ კიდევ კითხვა", "tr": "❓ Başka soru",
        "kk": "❓ Тағы сұрақ", "uz": "❓ Yana savol",
    },
}

# Helper
def t(lang: str, key: str, **kwargs) -> str:
    """Get translated text. Falls back to en, then ru."""
    texts = I18N.get(key, {})
    text = texts.get(lang, texts.get("en", texts.get("ru", key)))
    if kwargs:
        text = text.format(**kwargs)
    return text
