(() => {
  "use strict";

  const root = document.documentElement;
  const currentLanguage = () => (root.dataset.avanLanguage || root.lang || "en").toLowerCase().startsWith("fa") ? "fa" : "en";

  function setTheme(theme) {
    const normalized = theme === "dark" ? "dark" : "light";
    root.dataset.theme = normalized;
    try { localStorage.setItem("avan_theme", normalized); } catch (_) {}
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
      window.location.reload();
    });
  });

  // Exact UI-label translation for legacy Stage 1–7 templates.
  // Product names, creator text, addresses and user-generated content are intentionally untouched.
  const FA = {
    "HOME": "خانه", "SHOP": "فروشگاه", "DESIGN": "طراحی", "EXPLORE": "کاوش", "FOR YOU": "برای شما",
    "DROPS": "دراپ‌ها", "CHALLENGES": "چالش‌ها", "SEARCH": "جستجو", "SIGN IN": "ورود", "SIGN OUT": "خروج",
    "BAG": "سبد", "MY AVAN": "آوان من", "OVERVIEW": "نمای کلی", "ORDERS": "سفارش‌ها", "SAVED": "ذخیره‌شده‌ها",
    "MY DESIGNS": "طرح‌های من", "MY OUTFITS": "استایل‌های من", "SIZE PASSPORT": "پروفایل سایز", "ACCOUNT": "حساب",
    "PRODUCTS": "محصولات", "WAREHOUSE": "انبار", "CUSTOMERS": "مشتریان", "DESIGNS": "طرح‌ها", "CREATORS": "طراحان",
    "MARKETING": "بازاریابی", "FINANCE": "مالی", "STAFF": "کارمندان", "REPORTS": "گزارش‌ها", "SETTINGS": "تنظیمات",
    "OPERATIONS": "عملیات", "SHIPPING": "ارسال", "RETURNS": "مرجوعی", "PRODUCTION": "تولید", "ADDRESSES": "آدرس‌ها",
    "FOLLOWING": "دنبال‌شده‌ها", "FOLLOWING FEED": "فید دنبال‌شده‌ها", "CREATOR WALLET": "کیف پول طراح",
    "NOTIFICATIONS": "اعلان‌ها", "ALERTS": "اعلان‌ها", "PROFILE": "پروفایل", "REWARDS": "پاداش‌ها", "POINTS": "امتیاز",
    "SAVE": "ذخیره", "CANCEL": "انصراف", "DELETE": "حذف", "EDIT": "ویرایش", "REMOVE": "حذف", "VIEW ALL": "مشاهده همه",
    "CREATE ACCOUNT": "ساخت حساب", "EMAIL": "ایمیل", "PASSWORD": "رمز عبور", "USERNAME": "نام کاربری", "DISPLAY NAME": "نام نمایشی",
    "CHECKOUT": "تسویه حساب", "TOTAL": "مجموع", "SUBTOTAL": "جمع جزء", "DISCOUNT": "تخفیف", "DELIVERY": "تحویل",
    "CUSTOMER": "مشتری", "STATUS": "وضعیت", "DATE": "تاریخ", "COLOR": "رنگ", "SIZE": "سایز", "PRICE": "قیمت",
    "NEWEST": "جدیدترین", "POPULAR": "محبوب‌ترین", "LIKE": "پسند", "SAVE DESIGN": "ذخیره طرح", "PUBLISH": "انتشار",
    "ADD TO BAG": "افزودن به سبد", "ADD CUSTOM DESIGN TO BAG": "افزودن طرح سفارشی به سبد", "VIEW BAG": "مشاهده سبد",
    "EMPTY BAG": "سبد خالی", "YOUR BAG IS EMPTY.": "سبد شما خالی است.", "CONTINUE SHOPPING": "ادامه خرید",
    "NO ORDERS YET.": "هنوز سفارشی ندارید.", "NOTHING SAVED YET.": "هنوز چیزی ذخیره نشده است.",
    "NO RESULTS.": "نتیجه‌ای پیدا نشد.", "NO RESULTS FOUND.": "نتیجه‌ای پیدا نشد.", "NO NOTIFICATIONS.": "اعلانی وجود ندارد.",
    "LIGHT": "روشن", "DARK": "تیره", "DAY": "روز", "NIGHT": "شب", "OWNER": "مالک", "OWNER CONSOLE": "پنل مالک",
    "OPEN STORE": "باز کردن فروشگاه", "DJANGO ADMIN": "ادمین جنگو", "INVENTORY HISTORY": "گردش موجودی",
    "SAVE ADDRESS": "ذخیره آدرس", "MAKE DEFAULT": "پیش‌فرض", "DELIVERY ADDRESS": "آدرس تحویل", "YOUR ADDRESSES": "آدرس‌های شما",
    "RETURN REQUESTS": "درخواست‌های مرجوعی", "SUBMIT REQUEST": "ثبت درخواست", "FULFILLMENT": "آماده‌سازی سفارش",
    "TRACKING": "رهگیری", "CARRIER": "حامل", "SUPPLIER": "تأمین‌کننده", "SUPPLIERS": "تأمین‌کنندگان"
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
      if (FA[p]) el.setAttribute("placeholder", FA[p]);
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
