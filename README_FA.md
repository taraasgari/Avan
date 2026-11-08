# AVAN Stage 20 — Visual + Studio Hotfix V2

این نسخه مشکل خراب‌شدن متن فارسی در Hotfix قبلی را رفع می‌کند.

علت نسخه قبلی: Windows PowerShell خروجی UTF-8 دستور `git show` را با Code Page کنسول Decode کرده بود و بعد همان متن خراب را دوباره داخل `base.html` و `home.html` نوشته بود. نتیجه همان حروفی مثل `Ã` و `Ø` و متن ناخوانا بود.

V2 فایل‌های ظاهر قبل از Stage 20 را با `git checkout <commit> -- <file>` مستقیم از Blob گیت برمی‌گرداند، بنابراین هیچ Decode/Encode میانی روی متن فارسی انجام نمی‌شود.

همچنین Studio حرفه‌ای‌تر Hotfix حفظ می‌شود: نمای واقعی لباس، Front/Back/Sleeves/Neck Label، جابه‌جایی آزاد لایه‌ها، Undo/Redo، Resize/Rotate، Duplicate، Flip، Lock/Hide، Layer ordering، Text controls، Grid/Zoom و Sticker library.

## نصب
از ریشه پروژه:

```powershell
cd C:\Users\Tara\Desktop\avan-starter
powershell -ExecutionPolicy Bypass -File "C:\Users\Tara\Desktop\avan-stage20-visual-studio-hotfix-v2\apply_hotfix_v2.ps1"
docker compose -f docker-compose.yml -f docker-compose.dev.yml restart web
```

سپس در مرورگر `Ctrl + F5`.

این Hotfix Migration ندارد و Backend مربوط به Tracking/Support را دست نمی‌زند.
