from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import firebase_admin
from firebase_admin import credentials, firestore

# =============================
# 1️⃣ اتصال به Firebase
# =============================
cred = credentials.Certificate("serviceAccount.json")  # کلید سرویس فایربیست
firebase_admin.initialize_app(cred)
db = firestore.client()

# =============================
# 2️⃣ ثبت شروع ربات
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.full_name
    args = context.args  # اینجا payload لینک
    referrer_id = args[0] if args else None

    # ایجاد کاربر اگر وجود نداشت
    user_ref = db.collection("users").document(user_id)
    if not user_ref.get().exists:
        user_ref.set({"name": user_name, "referrals": [], "spins": 0})

    # ثبت زیرمجموعه برای معرف
    if referrer_id and referrer_id != user_id:
        ref_ref = db.collection("users").document(referrer_id)
        ref_snap = ref_ref.get()
        if ref_snap.exists:
            ref_ref.update({"referrals": firestore.ArrayUnion([{"id": user_id, "name": user_name}])})
            await update.message.reply_text(f"✅ شما به عنوان زیرمجموعه برای {referrer_id} ثبت شدید!")

    # لینک دعوت اختصاصی برای خود کاربر
    invite_link = f"https://t.me/BaNaNa_Rowbot?start={user_id}"
    await update.message.reply_text(
        f"سلام {user_name} 👋\nلینک دعوت شما:\n{invite_link}"
    )

# =============================
# 3️⃣ نمایش وضعیت زیرمجموعه‌ها
# =============================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_ref = db.collection("users").document(user_id)
    snap = user_ref.get()
    if not snap.exists:
        await update.message.reply_text("ابتدا /start را بزنید!")
        return
    data = snap.to_dict()
    referrals = data.get("referrals", [])
    spins = data.get("spins", 0)
    msg = f"👥 تعداد زیرمجموعه‌ها: {len(referrals)}\n🎡 چرخش‌های رایگان: {spins}\n"
    for r in referrals:
        msg += f"- {r['name']}\n"
    await update.message.reply_text(msg)

# =============================
# 4️⃣ محاسبه چرخش رایگان
# =============================
async def check_spins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_ref = db.collection("users").document(user_id)
    snap = user_ref.get()
    if not snap.exists:
        await update.message.reply_text("ابتدا /start را بزنید!")
        return
    data = snap.to_dict()
    referrals = data.get("referrals", [])
    spins = referrals_count_to_spins(len(referrals))
    user_ref.update({"spins": spins})
    await update.message.reply_text(f"🎡 چرخش‌های رایگان شما: {spins}")

def referrals_count_to_spins(count):
    # هر 5 زیرمجموعه = 1 چرخش
    return count // 5

# =============================
# 5️⃣ اجرای ربات
# =============================
app = ApplicationBuilder().token("8371304652:AAFgG4KJL1IvZ7jyVvDwH2XV5YKm-UJMpBE").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("check_spins", check_spins))

print("Bot is running...")
app.run_polling()
