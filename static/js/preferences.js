(() => {
  "use strict";

  const root = document.documentElement;
  const currentLanguage = () => (root.dataset.avanLanguage || root.lang || "fa").toLowerCase().startsWith("fa") ? "fa" : "en";

  function setTheme(theme) {
    const normalized = theme === "dark" ? "dark" : "light";
    root.dataset.theme = normalized;
    try { localStorage.setItem("avan_theme", normalized); } catch (_) {}
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const fa = currentLanguage() === "fa";
      const nextLabel = normalized === "dark" ? (fa ? "حالت روز" : "Switch to light mode") : (fa ? "حالت شب" : "Switch to dark mode");
      button.setAttribute("aria-label", nextLabel);
      button.setAttribute("title", nextLabel);
      button.setAttribute("aria-pressed", normalized === "dark" ? "true" : "false");
    });
    document.querySelectorAll("[data-theme-label]").forEach((node) => {
      const fa = currentLanguage() === "fa";
      node.textContent = normalized === "dark" ? (fa ? "روز" : "DAY") : (fa ? "شب" : "NIGHT");
    });
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = normalized === "dark" ? "#0d0d0f" : "#D50000";
  }

  document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
    button.addEventListener("click", () => setTheme(root.dataset.theme === "dark" ? "light" : "dark"));
  });
  setTheme(root.dataset.theme || "light");

  document.querySelectorAll("[data-language-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const next = currentLanguage() === "fa" ? "en" : "fa";
      document.cookie = `avan_language=${next}; Path=/; Max-Age=31536000; SameSite=Lax`;
      try { localStorage.setItem("avan_language", next); } catch (_) {}
      const url = new URL(window.location.href);
      url.searchParams.set("lang", next);
      window.location.assign(url.toString());
    });
  });

  // Legacy interface translation sweep. User-generated content is intentionally excluded.
  const FA = {
    "HOME":"خانه","SHOP":"فروشگاه","DESIGN":"طراحی","EXPLORE":"کاوش","FOR YOU":"برای شما","DROPS":"دراپ‌ها","CHALLENGES":"چالش‌ها","PLAY":"بازی‌ها","SEARCH":"جستجو","SIGN IN":"ورود","SIGN OUT":"خروج",
    "BAG":"سبد","MY AVAN":"آوان من","OVERVIEW":"نمای کلی","ORDERS":"سفارش‌ها","SAVED":"ذخیره‌شده‌ها","SAVED PRODUCTS":"محصولات ذخیره‌شده","SAVED DESIGNS":"طرح‌های ذخیره‌شده","MY DESIGNS":"طرح‌های من","MY OUTFITS":"استایل‌های من","SIZE PASSPORT":"پروفایل سایز","ACCOUNT":"حساب کاربری",
    "PRODUCTS":"محصولات","WAREHOUSE":"انبار","CUSTOMERS":"مشتریان","DESIGNS":"طرح‌ها","CREATORS":"طراحان","MARKETING":"بازاریابی","FINANCE":"مالی","STAFF":"ادمین‌ها","REPORTS":"گزارش‌ها","SETTINGS":"تنظیمات","OPERATIONS":"عملیات","SHIPPING":"ارسال","RETURNS":"مرجوعی","PRODUCTION":"تولید","SUPPORT":"پشتیبانی",
    "ADDRESSES":"آدرس‌ها","FOLLOWING":"دنبال‌شده‌ها","FOLLOWING FEED":"فید دنبال‌شده‌ها","CREATOR WALLET":"کیف پول طراح","NOTIFICATIONS":"اعلان‌ها","ALERTS":"اعلان‌ها","PROFILE":"پروفایل","REWARDS":"پاداش‌ها","POINTS":"امتیاز","ANALYTICS":"تحلیل‌ها","CREATOR ANALYTICS":"تحلیل طراح",
    "SAVE":"ذخیره","CANCEL":"انصراف","DELETE":"حذف","EDIT":"ویرایش","REMOVE":"حذف","VIEW ALL":"مشاهده همه","BACK":"بازگشت","NEXT":"بعدی","SUBMIT":"ثبت","CLOSE":"بستن","REOPEN":"باز کردن مجدد","FILTER":"فیلتر","RESET":"بازنشانی",
    "CREATE ACCOUNT":"ساخت حساب","EMAIL":"ایمیل","PASSWORD":"رمز عبور","USERNAME":"نام کاربری","DISPLAY NAME":"نام نمایشی","CHECKOUT":"تسویه حساب","TOTAL":"مجموع","SUBTOTAL":"جمع جزء","DISCOUNT":"تخفیف","DELIVERY":"تحویل","CUSTOMER":"مشتری","STATUS":"وضعیت","DATE":"تاریخ","COLOR":"رنگ","SIZE":"سایز","PRICE":"قیمت","CATEGORY":"دسته‌بندی",
    "NEWEST":"جدیدترین","POPULAR":"محبوب‌ترین","LIKE":"پسندیدن","SAVE DESIGN":"ذخیره طرح","PUBLISH":"انتشار","ADD TO BAG":"افزودن به سبد","ADD CUSTOM DESIGN TO BAG":"افزودن طرح سفارشی به سبد","VIEW BAG":"مشاهده سبد","CONTINUE SHOPPING":"ادامه خرید","START SHOPPING":"شروع خرید",
    "EMPTY BAG":"سبد خالی","YOUR BAG IS EMPTY.":"سبد شما خالی است.","NO ORDERS YET.":"هنوز سفارشی نداری.","NOTHING SAVED YET.":"هنوز چیزی ذخیره نشده است.","NO RESULTS.":"نتیجه‌ای پیدا نشد.","NO RESULTS FOUND.":"نتیجه‌ای پیدا نشد.","NO NOTIFICATIONS.":"اعلانی وجود ندارد.","NO PRODUCTS FOUND.":"محصولی پیدا نشد.","NO DESIGNS FOUND.":"طرحی پیدا نشد.","NO CREATORS FOUND.":"طراحی پیدا نشد.",
    "OWNER":"مالک","OWNER CONSOLE":"پنل مالک","OPEN STORE":"مشاهده فروشگاه","DJANGO ADMIN":"ادمین جنگو","INVENTORY HISTORY":"گردش موجودی","SAVE ADDRESS":"ذخیره آدرس","MAKE DEFAULT":"پیش‌فرض","DELIVERY ADDRESS":"آدرس تحویل","YOUR ADDRESSES":"آدرس‌های شما","RETURN REQUESTS":"درخواست‌های مرجوعی","SUBMIT REQUEST":"ثبت درخواست","FULFILLMENT":"آماده‌سازی سفارش","TRACKING":"رهگیری","CARRIER":"حامل","SUPPLIER":"تأمین‌کننده","SUPPLIERS":"تأمین‌کنندگان",
    "COLLECTIONS":"کالکشن‌ها","COLLECTION":"کالکشن","CONTENT":"محتوا","SEO":"سئو","SECURITY":"امنیت","MODERATION":"نظارت محتوا","CATALOG":"کاتالوگ","CATALOG MANAGER":"مدیریت کاتالوگ","SHIPPING METHODS":"روش‌های ارسال","MEDIA":"رسانه","VARIANTS":"تنوع‌ها","GROWTH / SEO":"رشد و سئو","QUICK ACCESS":"دسترسی سریع",
    "CREATE":"ساخت","STYLE":"استایل","FIT":"اندازه","FOLLOW":"دنبال کردن","PURCHASES":"خریدها","YOUR ORDERS":"سفارش‌های شما","RECENT":"اخیر","ACTIVE CHALLENGES":"چالش‌های فعال","ADDRESS BOOK":"دفترچه آدرس","OUTFIT BUILDER":"ساخت استایل","OPEN AVAN STUDIO":"باز کردن استودیو AVAN","YOUR CREATOR FEED":"فید طراحان شما",
    "START DESIGNING":"شروع طراحی","START":"شروع","PLAY AGAIN":"دوباره بازی کن","PERSONAL BEST":"بهترین رکورد","SCORE":"امتیاز","TIME":"زمان","PRESSURE":"فشار","SOUND ON":"صدا روشن","SOUND OFF":"صدا خاموش","RUN COMPLETE":"بازی تمام شد","MY REWARDS":"پاداش‌های من","HOW TO SURVIVE":"راهنمای بازی","KEYBOARD":"کیبورد","TOUCH":"لمسی",
    "SUPPORT DESK":"پشتیبانی کاربران","NEW REQUEST":"درخواست جدید","MY TICKETS":"گفتگوهای من","MESSAGE":"پیام","SUBJECT":"موضوع","ORDER NUMBER (OPTIONAL)":"شماره سفارش (اختیاری)","SEND REPLY":"ارسال پاسخ","CLOSE TICKET":"بستن گفتگو","SAVE PRIORITY":"ذخیره اولویت",
    "Order":"سفارش","Product":"محصول","Payment":"پرداخت","Return / Refund":"مرجوعی / بازپرداخت","Design Studio":"استودیو طراحی","Account":"حساب کاربری","Other":"سایر",
    "Open":"باز","Waiting for support":"در انتظار پشتیبانی","Waiting for user":"در انتظار پاسخ کاربر","Closed":"بسته","Normal":"عادی","High":"مهم","Urgent":"فوری",
    "Start a new garment design →":"یک طراحی جدید برای لباس شروع کن ←","Build a complete fit →":"یک استایل کامل بساز ←","Keep your private fit profile →":"پروفایل اندازه خصوصی خودت را نگه دار ←","New work from people you follow →":"طرح‌های جدید کسانی که دنبال می‌کنی ←","Likes, saves, remixes and paid wears →":"لایک، ذخیره، ریمیکس و فروش طرح‌ها ←","Save addresses for faster checkout →":"آدرس‌ها را برای خرید سریع‌تر ذخیره کن ←","Track return requests →":"درخواست‌های مرجوعی را پیگیری کن ←","Submit designs and win points →":"طرح بفرست و امتیاز بگیر ←","Talk directly with AVAN support →":"مستقیم با پشتیبانی AVAN گفتگو کن ←",
    "Your AVAN orders will appear here.":"سفارش‌های AVAN شما اینجا نمایش داده می‌شوند.","No notifications yet.":"هنوز اعلانی نداری.","UNREAD":"خوانده‌نشده","FOLLOWERS":"دنبال‌کننده‌ها","PAID WEARS":"خریدهای طرح","LIKES":"پسندها","SAVES":"ذخیره‌ها","REMIXES":"ریمیکس‌ها"
  };

  const PLACEHOLDERS = {
    "SEARCH AVAN...":"جستجو در AVAN...",
    "WHAT ARE YOU LOOKING FOR?":"دنبال چی می‌گردی؟",
    "Search products, designs and collections...":"محصول، طرح یا کالکشن را جستجو کن...",
    "Search products, designs, collections or creators...":"محصول، طرح، کالکشن یا طراح را جستجو کن..."
  };

  function translateTextNode(node) {
    if (currentLanguage() !== "fa") return;
    const parent = node.parentElement;
    if (!parent || parent.closest("[data-no-translate],script,style,textarea,code,pre")) return;
    const raw = node.nodeValue;
    const trimmed = raw.trim();
    if (!trimmed || !FA[trimmed]) return;
    node.nodeValue = raw.replace(trimmed, FA[trimmed]);
  }

  function translateElement(el) {
    if (currentLanguage() !== "fa" || !(el instanceof Element)) return;
    if (el.matches("input[placeholder],textarea[placeholder]")) {
      const p = el.getAttribute("placeholder");
      if (PLACEHOLDERS[p]) el.setAttribute("placeholder", PLACEHOLDERS[p]);
      else if (FA[p]) el.setAttribute("placeholder", FA[p]);
    }
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) translateTextNode(node);
  }

  if (currentLanguage() === "fa") {
    translateElement(document.body);
    const observer = new MutationObserver((records) => {
      for (const record of records) {
        record.addedNodes.forEach((node) => {
          if (node.nodeType === Node.TEXT_NODE) translateTextNode(node);
          else if (node.nodeType === Node.ELEMENT_NODE) translateElement(node);
        });
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
