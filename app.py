# -*- coding: utf-8 -*-
# هذا الكود هو لبوت تيليجرام مصمم لاستقبال طلبات المنتجات من المشترين لمشروع KABA Project.
# تم تحديثه بالكامل ليتوافق مع أحدث الإصدارات من مكتبة python-telegram-bot (الإصدار 20.x وما فوق).
# يرجى نسخ هذا الكود بالكامل ولصقه في ملف app.py الخاص بك على Hugging Face Spaces.

# استيراد الوحدات اللازمة من مكتبة telegram.ext
# في الإصدارات الجديدة، نستخدم Application بدلاً من Updater و Dispatcher.
# كما أن 'filters' تُستورد كوحدة منفصلة.
from telegram.ext import Application, CommandHandler, MessageHandler
from telegram.ext import filters # <--- هذا السطر صحيح للاستيراد
import logging # لتسجيل الأخطاء والرسائل (مفيد جداً للتصحيح)
import re # لاستخدام التعبيرات النمطية للتحقق من رقم الهاتف
import os # لاستخدام متغيرات البيئة لقراءة التوكن ورابط الـ Webhook

# تفعيل تسجيل الأخطاء والرسائل.
# هذا يساعدك في رؤية ما يفعله البوت في الطرفية (Terminal) وأي أخطاء قد تحدث.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
# لتقليل رسائل التحذير التي قد تأتي من المكتبات الداخلية (مثل httpx)
logging.getLogger('httpx').setLevel(logging.WARNING) 

# 1. ضع التوكن الخاص ببوتك هنا (استبدل 'YOUR_BOT_TOKEN' بالتوكن الحقيقي الذي حصلت عليه من BotFather)
# هذا التوكن هو المفتاح الذي يربط الكود الخاص بك بالبوت على تيليجرام.
# نقوم بقراءة التوكن من متغيرات البيئة لأغراض الأمان عند الاستضافة.
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') 
if not TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set.")
    raise ValueError("Environment variable TELEGRAM_BOT_TOKEN is not set. Please set it in Hugging Face Space secrets.")

# قاموس لتخزين معلومات المستخدم مؤقتاً ومرحلة المحادثة الحالية لكل مستخدم.
# هذا يستخدم لتتبع حالة المحادثة لكل مستخدم بشكل منفصل عبر المراحل المختلفة.
# ملاحظة هامة: في تطبيق حقيقي (للإنتاج)، يجب استخدام قاعدة بيانات (مثل SQLite, PostgreSQL, MongoDB)
# لتخزين هذه البيانات بشكل دائم وآمن، بدلاً من تخزينها في الذاكرة (التي تُمسح عند إيقاف البوت).
user_data = {}

# دالة التعامل مع أمر /start
# هذه الدالة تُستدعى عندما يرسل المستخدم الأمر /start إلى البوت.
# في الإصدارات الجديدة، يجب أن تكون دوال المعالجة (handlers) غير متزامنة (async).
async def start(update, context):
    user_id = update.message.from_user.id
    # إعادة تعيين بيانات المستخدم ومرحلته عند بدء جديد، لضمان محادثة نظيفة.
    user_data[user_id] = {'stage': 'asking_product_name'} 
    
    await update.message.reply_text( # <--- يجب استخدام 'await' مع الدوال غير المتزامنة
        'أهلاً بك في بوت KABA Project لطلبات الشراء! 🛍️ أنا هنا لمساعدتك في الحصول على منتجاتك العالمية بكل سهولة.\n'
        'للبدء، يرجى تزويدي بالمعلومات التالية عن المنتج الذي تبحث عنه.'
    )
    await update.message.reply_text('ما هو اسم المنتج الذي تبحث عنه؟ 📝') # <--- استخدام 'await' هنا أيضاً

# دالة للتعامل مع رسائل المستخدم (النصية والصور)
# هذه الدالة هي القلب النابض للبوت، حيث تعالج جميع رسائل المستخدم بناءً على مرحلته الحالية.
# يجب أن تكون هذه الدالة أيضاً غير متزامنة (async).
async def handle_message(update, context):
    user_id = update.message.from_user.id
    
    if user_id not in user_data:
        # إذا لم يكن المستخدم قد بدأ محادثة بعد، نطلب منه البدء لتجنب الأخطاء.
        await update.message.reply_text('الرجاء البدء باستخدام أمر /start أولاً.')
        return

    current_stage = user_data[user_id]['stage']

    # معالجة إجابات المستخدم بناءً على المرحلة الحالية
    if current_stage == 'asking_product_name':
        # التحقق إذا كانت الرسالة نصية قبل حفظها.
        if update.message.text:
            user_data[user_id]['product_name'] = update.message.text
            user_data[user_id]['stage'] = 'asking_price'
            await update.message.reply_text('كم هو سعر المنتج؟ (يمكنك كتابة السعر التقريبي أو النطاق) 💰')
        else:
            await update.message.reply_text('عذراً، يرجى إدخال اسم المنتج كنص.')
    
    elif current_stage == 'asking_price':
        if update.message.text:
            user_data[user_id]['product_price'] = update.message.text
            user_data[user_id]['stage'] = 'asking_dimensions'
            await update.message.reply_text(
                'هل لديك أي معلومات حول أبعاد المنتج (الطول، العرض، الارتفاع) أو وزنه التقريبي؟ '
                '(هذا يساعدنا في تقدير تكلفة الشحن بشكل أفضل). '
                '(يمكنك الإجابة بـ "لا" إذا لم تكن تعرف). 📦'
            )
        else:
            await update.message.reply_text('عذراً، يرجى إدخال السعر كنص.')
    
    elif current_stage == 'asking_dimensions':
        if update.message.text:
            user_data[user_id]['product_dimensions'] = update.message.text
            user_data[user_id]['stage'] = 'asking_delivery_method'
            await update.message.reply_text(
                'هل ستلتقي مع المسافر في مكان ما لأخذ منتجك (خيار 1) أم تريد أن يتم إيصال المنتج لمنزلك (خيار 2)؟ '
                'الرجاء كتابة رقم خيار واحد فقط.'
            )
        else:
            await update.message.reply_text('عذراً، يرجى إدخال معلومات الأبعاد كنص.')

    elif current_stage == 'asking_delivery_method':
        if update.message.text:
            user_response = update.message.text.lower().strip() # تحويل الإجابة إلى حروف صغيرة وإزالة المسافات
            
            if user_response in ['2', 'خيار 2', 'اثنين', 'خيار اثنين']:
                user_data[user_id]['delivery_method'] = 'delivery_to_home'
                user_data[user_id]['stage'] = 'asking_city'
                await update.message.reply_text('يرجى إخبارنا في أي مدينة/منطقة في الجزائر أنت مقيم؟ 🏘️')
            elif user_response in ['1', 'خيار 1', 'واحد', 'خيار واحد']:
                user_data[user_id]['delivery_method'] = 'meet_traveler'
                # تخطي سؤال المدينة والانتقال مباشرة للسؤال التالي
                user_data[user_id]['stage'] = 'asking_additional_notes' 
                await update.message.reply_text(
                    'هل لديك أي ملاحظات إضافية أو تفضيلات خاصة بخصوص طلبك؟ '
                    '(مثل: لون المنتج، تغليف خاص، إلخ.) '
                    'يمكنك أيضاً إرفاق صورة أو رابط للمنتج هنا. 📝'
                )
            else:
                await update.message.reply_text('عذراً، لم أفهم اختيارك. يرجى كتابة "1" للخيار الأول أو "2" للخيار الثاني.')
        else:
            await update.message.reply_text('عذراً، يرجى إدخال رقم الخيار كنص.')
    
    elif current_stage == 'asking_city':
        if update.message.text:
            user_data[user_id]['delivery_city'] = update.message.text
            user_data[user_id]['stage'] = 'asking_additional_notes'
            await update.message.reply_text(
                'هل لديك أي ملاحظات إضافية أو تفضيلات خاصة بخصوص طلبك؟ '
                '(مثل: لون المنتج، تغليف خاص، إلخ.) '
                'يمكنك أيضاً إرفاق صورة أو رابط للمنتج هنا. 📝'
            )
        else:
            await update.message.reply_text('عذراً، يرجى إدخال المدينة/المنطقة كنص.')

    elif current_stage == 'asking_additional_notes':
        # إذا أرسل المستخدم صورة في هذه المرحلة
        if update.message.photo:
            user_data[user_id]['additional_notes'] = update.message.caption if update.message.caption else "صورة مرفقة"
            user_data[user_id]['product_image_id'] = update.message.photo[-1].file_id # حفظ ID الصورة لأغراض لاحقة
            user_data[user_id]['stage'] = 'asking_more_info_after_photo'
            await update.message.reply_text('شكراً على الصورة! هل من معلومات إضافية أخرى؟')
        # إذا أرسل المستخدم نصاً (ملاحظات أو رابط)
        elif update.message.text:
            user_data[user_id]['additional_notes'] = update.message.text
            user_data[user_id]['stage'] = 'asking_for_photo'
            await update.message.reply_text('هل تريد إرفاق بصورة؟ 🖼️')
        else:
            # إذا لم يرسل نصاً ولا صورة (مثلاً ملصق أو ملف غير مدعوم)
            user_data[user_id]['additional_notes'] = "لا يوجد ملاحظات إضافية"
            user_data[user_id]['stage'] = 'asking_for_photo'
            await update.message.reply_text('عذراً، لم أفهم. يرجى إرسال صورة أو كتابة ملاحظاتك. هل تريد إرفاق بصورة؟ 🖼️')

    elif current_stage == 'asking_more_info_after_photo':
        if update.message.text:
            user_data[user_id]['more_info_after_photo'] = update.message.text
        else:
            user_data[user_id]['more_info_after_photo'] = "لا توجد معلومات إضافية"
        # الانتقال إلى مرحلة طلب اسم المستخدم
        user_data[user_id]['stage'] = 'asking_username' 
        await update.message.reply_text('يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
    
    elif current_stage == 'asking_for_photo':
        # المستخدم يرسل صورة رداً على سؤال "هل تريد إرفاق بصورة؟"
        if update.message.photo:
            user_data[user_id]['product_image_id'] = update.message.photo[-1].file_id # حفظ ID الصورة
            # الانتقال إلى مرحلة طلب اسم المستخدم بعد الصورة
            user_data[user_id]['stage'] = 'asking_username' 
            await update.message.reply_text('شكراً على الصورة! يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
        # المستخدم يرسل نصاً (مثلاً "لا أريد صورة" أو "لا")
        elif update.message.text:
            if update.message.text.lower().strip() in ['لا', 'لا أريد صورة', 'لا لا', 'no']:
                user_data[user_id]['product_image_id'] = 'لم يتم إرفاق صورة'
            else:
                user_data[user_id]['product_image_id'] = f"نص بدلاً من صورة: {update.message.text}"
            # الانتقال إلى مرحلة طلب اسم المستخدم بعد النص
            user_data[user_id]['stage'] = 'asking_username' 
            await update.message.reply_text('حسناً. يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
        else:
            # إذا لم يرسل نصاً ولا صورة (مثلاً ملصق)
            await update.message.reply_text('عذراً، لم أفهم. يرجى إرسال صورة أو كتابة "لا" إذا كنت لا تريد إرفاق صورة.')
            # نبقى في نفس المرحلة حتى يتم إرسال إجابة صالحة
            return 

    elif current_stage == 'asking_username': # <--- مرحلة جديدة لطلب اسم المستخدم
        if update.message.text:
            username = update.message.text.strip()
            # يمكن إضافة تحقق بسيط هنا أن الاسم يبدأ بـ '@' إذا أردت
            if username.startswith('@') and len(username) > 1: # إضافة تحقق بسيط على طول الاسم
                user_data[user_id]['telegram_username'] = username
                user_data[user_id]['stage'] = 'asking_phone_number' # الانتقال للمرحلة التالية (رقم الهاتف)
                await update.message.reply_text('شكراً! يرجى تزويدنا برقم هاتفك للتواصل معك بشأن طلبك. 📞 (مثال: 07xxxxxxx)')
            else:
                await update.message.reply_text('يرجى إدخال اسم المستخدم الصحيح (يجب أن يبدأ بـ "@" ولا يكون فارغاً). 👤')
                return # البقاء في نفس المرحلة حتى يتم إدخال اسم مستخدم صحيح
        else:
            await update.message.reply_text('عذراً، يرجى إدخال اسم المستخدم كنص.')
            return

    elif current_stage == 'asking_phone_number':
        if update.message.text:
            phone_number = update.message.text.strip()
            # التحقق من أن رقم الهاتف يتكون من 10 أرقام فقط (مثال جزائري)
            if re.fullmatch(r'\d{10}', phone_number): # `\d{10}` تعني 10 أرقام بالضبط
                user_data[user_id]['phone_number'] = phone_number
                user_data[user_id]['stage'] = 'completed' # انتهاء مراحل السؤال
                
                # بناء رسالة التأكيد النهائية بملخص الطلب
                summary = (
                    f"شكراً لك! لقد تلقينا طلبك للمنتج:\n"
                    f"🔗 اسم المنتج: {user_data[user_id].get('product_name', 'غير متوفر')}\n"
                    f"💰 السعر التقريبي: {user_data[user_id].get('product_price', 'غير متوفر')}\n"
                    f"📦 الأبعاد/الوزن: {user_data[user_id].get('product_dimensions', 'غير متوفر')}\n"
                )
                # إضافة طريقة الاستلام ومعلومات المدينة إذا اختار التوصيل للمنزل
                if user_data[user_id].get('delivery_method') == 'delivery_to_home':
                    summary += f"🏠 طريقة الاستلام: توصيل للمنزل\n"
                    summary += f"📍 مدينة الاستلام: {user_data[user_id].get('delivery_city', 'غير متوفر')}\n"
                else:
                    summary += f"🤝 طريقة الاستلام: لقاء مع المسافر\n"
                
                summary += (
                    f"📝 ملاحظات إضافية: {user_data[user_id].get('additional_notes', 'غير متوفر')}\n"
                )
                
                # إضافة معلومات الصورة بناءً على ما تم جمعه
                if user_data[user_id].get('product_image_id') == 'لم يتم إرفاق صورة':
                     summary += f"🖼️ صورة المنتج: لم يتم إرفاق صورة\n"
                elif user_data[user_id].get('product_image_id') and user_data[user_id].get('product_image_id').startswith("نص بدلاً من صورة:"):
                     summary += f"🖼️ صورة المنتج: {user_data[user_id].get('product_image_id')}\n"
                elif user_data[user_id].get('product_image_id'):
                     summary += f"🖼️ صورة المنتج: تم إرفاق صورة (ID: {user_data[user_id].get('product_image_id')})\n"
                else:
                     summary += f"🖼️ صورة المنتج: غير متوفرة\n"

                # إضافة اسم المستخدم الجديد
                summary += f"👤 اسم المستخدم تيليجرام: {user_data[user_id].get('telegram_username', 'غير متوفر')}\n" 

                summary += (
                    f"📞 رقم الهاتف: {user_data[user_id].get('phone_number', 'غير متوفر')}\n\n"
                    f"سيتم مراجعة طلبك والتواصل معك قريباً لتوفير تفاصيل التوصيل. ترقب الجديد مع KABA Project! ✨"
                )
                
                await update.message.reply_text(summary)
                
                # --- حفظ البيانات في ملف نصي (لأغراض البروتوتايب فقط) ---
                # في تطبيق حقيقي، ستستخدم قاعدة بيانات (SQLite, PostgreSQL, MongoDB) لتخزين البيانات بشكل دائم وآمن.
                try:
                    with open('buyer_requests.txt', 'a', encoding='utf-8') as f:
                        f.write(f"--- طلب جديد من المستخدم {user_id} ---\n")
                        for key, value in user_data[user_id].items():
                            if key != 'stage': # لا نحتاج لحفظ مرحلة المستخدم في الملف
                                f.write(f"{key}: {value}\n")
                        f.write("---\n\n")
                except IOError as e:
                    logging.error(f"فشل حفظ البيانات في الملف: {e}")
                    await update.message.reply_text("عذراً، حدث خطأ أثناء حفظ طلبك. يرجى المحاولة لاحقاً.")

                # مسح بيانات المستخدم من الذاكرة بعد اكتمال الطلب (للسماح بطلب جديد نظيف للمستخدم نفسه لاحقاً)
                del user_data[user_id] 

            else:
                await update.message.reply_text('يرجى كتابة رقم هاتفك بالطريقة الصحيحة (10 أرقام فقط). 🚫📞')
                # البقاء في نفس المرحلة لكي يكرر المستخدم إدخال الرقم الصحيح
                return # هام جداً لكي لا ينتقل البوت إلى مرحلة أخرى بالخطأ
        else:
            await update.message.reply_text('عذراً، يرجى إدخال رقم هاتفك كنص.')
    
    else:
        # رسالة افتراضية إذا لم يتم التعرف على المرحلة (مثلاً إذا أرسل المستخدم شيئاً غير متوقع في مرحلة غير متوقعة)
        await update.message.reply_text('عذراً، لم أفهم طلبك. يرجى البدء من جديد باستخدام أمر /start.')


# دالة رئيسية لتشغيل البوت
def main():
    # 2. إنشاء كائن Application وإدخال التوكن الخاص بك.
    # Application هو البديل الحديث لـ Updater و Dispatcher في الإصدارات الأحدث.
    application = Application.builder().token(TOKEN).build()

    # 3. تسجيل معالجات الأوامر والرسائل
    # معالج لأمر /start
    application.add_handler(CommandHandler("start", start)) 
    
    # معالج للرسائل النصية التي ليست أوامر AND للصور
    # نستخدم filters.TEXT للمسجات النصية و filters.PHOTO للمسجات التي تحوي صور
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    # 4. بدء تشغيل البوت (Webhooks) - الطريقة المفضلة للاستضافة
    # يجب تعيين متغير البيئة HF_SPACE_HOST في Hugging Face Space secrets.
    WEBHOOK_URL = os.environ.get('HF_SPACE_HOST')

    if not WEBHOOK_URL:
        logging.error("HF_SPACE_HOST environment variable not set. Webhook might not work correctly.")
        raise ValueError("Environment variable HF_SPACE_HOST is not set. Please set it in Hugging Face Space secrets to your Space URL.")

    PORT = int(os.environ.get("PORT", "8080")) # Hugging Face Spaces يوفر متغير بيئة PORT


    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/", # المسار الذي يستقبل عليه البوت تحديثات الويب هو المسار الرئيسي
        webhook_url=f"{WEBHOOK_URL}" # هنا نستخدم WEBHOOK_URL مباشرة
    )


# تشغيل الدالة الرئيسية عند بدء تشغيل السكربت (أمر شائع في Python)
if __name__ == '__main__':
    main()

