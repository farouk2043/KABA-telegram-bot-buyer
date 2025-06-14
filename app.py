# -*- coding: utf-8 -*-
# هذا الكود هو لبوت تيليجرام مصمم لاستقبال طلبات المنتجات من المشترين لمشروع KABA Project.
# تم تحديثه بالكامل ليتوافق مع أحدث الإصدارات من مكتبة python-telegram-bot (الإصدار 21.x وما فوق).
# هذا الإصدار معد خصيصاً للاستضافة على Render.com.

# استيراد الوحدات اللازمة من مكتبة telegram.ext
# نستخدم Application بدلاً من Updater و Dispatcher في الإصدارات الأحدث.
from telegram.ext import Application, CommandHandler, MessageHandler
from telegram.ext import filters # استيراد وحدة الفلاتر
import logging # لتسجيل الأخطاء والرسائل
import re # لاستخدام التعبيرات النمطية للتحقق من رقم الهاتف
import os # لاستخدام متغيرات البيئة لقراءة التوكن وروابط الويب هوك

# تفعيل تسجيل الأخطاء والرسائل.
# هذا يساعد في رؤية ما يفعله البوت في سجلات Render.
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
# لتقليل رسائل التحذير التي قد تأتي من المكتبات الداخلية مثل httpx
logging.getLogger('httpx').setLevel(logging.WARNING) 

# قراءة توكن البوت من متغيرات البيئة لأغراض الأمان عند الاستضافة.
# يجب تعيين متغير البيئة 'TELEGRAM_BOT_TOKEN' في إعدادات Render.
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') 
if not TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set. Please set it in Render environment variables.")
    raise ValueError("Environment variable TELEGRAM_BOT_TOKEN is not set.")

# قاموس لتخزين معلومات المستخدم مؤقتاً ومرحلة المحادثة الحالية لكل مستخدم.
user_data = {}

# دالة التعامل مع أمر /start
# هذه الدالة تُستدعى عندما يرسل المستخدم الأمر /start. يجب أن تكون دالة غير متزامنة (async).
async def start(update, context):
    user_id = update.message.from_user.id
    # إعادة تعيين بيانات المستخدم ومرحلته عند بدء جديد.
    user_data[user_id] = {'stage': 'asking_product_name'} 
    
    await update.message.reply_text(
        'أهلاً بك في بوت KABA Project لطلبات الشراء! 🛍️ أنا هنا لمساعدتك في الحصول على منتجاتك العالمية بكل سهولة.\n'
        'للبدء، يرجى تزويدي بالمعلومات التالية عن المنتج الذي تبحث عنه.'
    )
    await update.message.reply_text('ما هو اسم المنتج الذي تبحث عنه؟ 📝')

# دالة للتعامل مع رسائل المستخدم (النصية والصور)
# هذه الدالة هي القلب النابض للبوت، حيث تعالج جميع رسائل المستخدم بناءً على مرحلته الحالية.
async def handle_message(update, context):
    user_id = update.message.from_user.id
    
    if user_id not in user_data:
        await update.message.reply_text('الرجاء البدء باستخدام أمر /start أولاً.')
        return

    current_stage = user_data[user_id]['stage']

    # معالجة إجابات المستخدم بناءً على المرحلة الحالية
    if current_stage == 'asking_product_name':
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
            user_response = update.message.text.lower().strip() 
            
            if user_response in ['2', 'خيار 2', 'اثنين', 'خيار اثنين']:
                user_data[user_id]['delivery_method'] = 'delivery_to_home'
                user_data[user_id]['stage'] = 'asking_city'
                await update.message.reply_text('يرجى إخبارنا في أي مدينة/منطقة في الجزائر أنت مقيم؟ 🏘️')
            elif user_response in ['1', 'خيار 1', 'واحد', 'خيار واحد']:
                user_data[user_id]['delivery_method'] = 'meet_traveler'
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
        if update.message.photo:
            user_data[user_id]['additional_notes'] = update.message.caption if update.message.caption else "صورة مرفقة"
            user_data[user_id]['product_image_id'] = update.message.photo[-1].file_id 
            user_data[user_id]['stage'] = 'asking_more_info_after_photo'
            await update.message.reply_text('شكراً على الصورة! هل من معلومات إضافية أخرى؟')
        elif update.message.text:
            user_data[user_id]['additional_notes'] = update.message.text
            user_data[user_id]['stage'] = 'asking_for_photo'
            await update.message.reply_text('هل تريد إرفاق بصورة؟ 🖼️')
        else:
            user_data[user_id]['additional_notes'] = "لا يوجد ملاحظات إضافية"
            user_data[user_id]['stage'] = 'asking_for_photo'
            await update.message.reply_text('عذراً، لم أفهم. يرجى إرسال صورة أو كتابة ملاحظاتك. هل تريد إرفاق بصورة؟ 🖼️')

    elif current_stage == 'asking_more_info_after_photo':
        if update.message.text:
            user_data[user_id]['more_info_after_photo'] = update.message.text
        else:
            user_data[user_id]['more_info_after_photo'] = "لا توجد معلومات إضافية"
        user_data[user_id]['stage'] = 'asking_username' 
        await update.message.reply_text('يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). �')
    
    elif current_stage == 'asking_for_photo':
        if update.message.photo:
            user_data[user_id]['product_image_id'] = update.message.photo[-1].file_id 
            user_data[user_id]['stage'] = 'asking_username' 
            await update.message.reply_text('شكراً على الصورة! يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
        elif update.message.text:
            if update.message.text.lower().strip() in ['لا', 'لا أريد صورة', 'لا لا', 'no']:
                user_data[user_id]['product_image_id'] = 'لم يتم إرفاق صورة'
            else:
                user_data[user_id]['product_image_id'] = f"نص بدلاً من صورة: {update.message.text}"
            user_data[user_id]['stage'] = 'asking_username' 
            await update.message.reply_text('حسناً. يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
        else:
            await update.message.reply_text('عذراً، لم أفهم. يرجى إرسال صورة أو كتابة "لا" إذا كنت لا تريد إرفاق صورة.')
            return 

    elif current_stage == 'asking_username':
        if update.message.text:
            username = update.message.text.strip()
            if username.startswith('@') and len(username) > 1:
                user_data[user_id]['telegram_username'] = username
                user_data[user_id]['stage'] = 'asking_phone_number' 
                await update.message.reply_text('شكراً! يرجى تزويدنا برقم هاتفك للتواصل معك بشأن طلبك. 📞 (مثال: 07xxxxxxx)')
            else:
                await update.message.reply_text('يرجى إدخال اسم المستخدم الصحيح (يجب أن يبدأ بـ "@" ولا يكون فارغاً). 👤')
                return 
        else:
            await update.message.reply_text('عذراً، يرجى إدخال اسم المستخدم كنص.')
            return

    elif current_stage == 'asking_phone_number':
        if update.message.text:
            phone_number = update.message.text.strip()
            if re.fullmatch(r'\d{10}', phone_number):
                user_data[user_id]['phone_number'] = phone_number
                user_data[user_id]['stage'] = 'completed' 
                
                summary = (
                    f"شكراً لك! لقد تلقينا طلبك للمنتج:\n"
                    f"🔗 اسم المنتج: {user_data[user_id].get('product_name', 'غير متوفر')}\n"
                    f"💰 السعر التقريبي: {user_data[user_id].get('product_price', 'غير متوفر')}\n"
                    f"📦 الأبعاد/الوزن: {user_data[user_id].get('product_dimensions', 'غير متوفر')}\n"
                )
                if user_data[user_id].get('delivery_method') == 'delivery_to_home':
                    summary += f"🏠 طريقة الاستلام: توصيل للمنزل\n"
                    summary += f"📍 مدينة الاستلام: {user_data[user_id].get('delivery_city', 'غير متوفر')}\n"
                else:
                    summary += f"🤝 طريقة الاستلام: لقاء مع المسافر\n"
                
                summary += (
                    f"📝 ملاحظات إضافية: {user_data[user_id].get('additional_notes', 'غير متوفر')}\n"
                )
                
                if user_data[user_id].get('product_image_id') == 'لم يتم إرفاق صورة':
                     summary += f"🖼️ صورة المنتج: لم يتم إرفاق صورة\n"
                elif user_data[user_id].get('product_image_id') and user_data[user_id].get('product_image_id').startswith("نص بدلاً من صورة:"):
                     summary += f"🖼️ صورة المنتج: {user_data[user_id].get('product_image_id')}\n"
                elif user_data[user_id].get('product_image_id'):
                     summary += f"🖼️ صورة المنتج: تم إرفاق صورة (ID: {user_data[user_id].get('product_image_id')})\n"
                else:
                     summary += f"🖼️ صورة المنتج: غير متوفرة\n"

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

                del user_data[user_id] 

            else:
                await update.message.reply_text('يرجى كتابة رقم هاتفك بالطريقة الصحيحة (10 أرقام فقط). 🚫📞')
                return
        else:
            await update.message.reply_text('عذراً، يرجى إدخال رقم هاتفك كنص.')
    
    else:
        await update.message.reply_text('عذراً، لم أفهم طلبك. يرجى البدء من جديد باستخدام أمر /start.')


# دالة رئيسية لتشغيل البوت
def main():
    # 2. إنشاء كائن Application وإدخال التوكن الخاص بك.
    application = Application.builder().token(TOKEN).build()

    # 3. تسجيل معالجات الأوامر والرسائل
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    # 4. بدء تشغيل البوت (Webhooks) - الطريقة المفضلة للاستضافة على Render.com
    # Render يوفر متغير البيئة RENDER_EXTERNAL_URL الذي يحتوي على رابط خدمة الويب الخاصة بك.
    WEBHOOK_URL = os.environ.get('RENDER_EXTERNAL_URL') 
    
    if not WEBHOOK_URL:
        logging.error("RENDER_EXTERNAL_URL environment variable not set. Webhook might not work correctly.")
        raise ValueError("Environment variable RENDER_EXTERNAL_URL is not set. Please ensure it's set on Render.")

    PORT = int(os.environ.get("PORT", "8080")) # Render يوفر متغير بيئة PORT


    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/", # المسار الذي يستقبل عليه البوت تحديثات الويب هو المسار الرئيسي
        webhook_url=f"{WEBHOOK_URL}" # هنا نستخدم WEBHOOK_URL مباشرة
    )


# تشغيل الدالة الرئيسية عند بدء تشغيل السكربت (أمر شائع في Python)
if __name__ == '__main__':
    main()
�
