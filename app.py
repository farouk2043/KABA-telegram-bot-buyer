    # -*- coding: utf-8 -*-
    # هذا الكود هو لبوت تيليجرام مصمم لاستقبال طلبات المنتجات من المشترين لمشروع KABA Project.
    # تم تحديثه بالكامل ليتوافق مع أحدث الإصدارات من مكتبة python-telegram-bot (الإصدار 21.x وما فوق).
    # تم إعداده خصيصًا للاستضافة على Replit باستخدام Webhooks.

    # استيراد الوحدات اللازمة من مكتبة telegram.ext
    from telegram.ext import Application, CommandHandler, MessageHandler
    from telegram.ext import filters
    import logging
    import re
    import os # لاستخدام متغيرات البيئة لقراءة التوكن ورابط الـ Webhook

    # تفعيل تسجيل الأخطاء والرسائل.
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)

    # 1. ضع التوكن الخاص ببوتك هنا
    # نقوم بقراءة التوكن من متغيرات البيئة لأغراض الأمان عند الاستضافة.
    TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN environment variable not set.")
        raise ValueError("Environment variable TELEGRAM_BOT_TOKEN is not set. Please set it in your hosting platform's secrets/environment variables.")

    # قاموس لتخزين معلومات المستخدم مؤقتًا ومرحلة المحادثة الحالية لكل مستخدم.
    user_data = {}

    # دالة التعامل مع أمر /start
    async def start(update, context):
        user_id = update.message.from_user.id
        user_data[user_id] = {'stage': 'asking_product_name'}
        
        await update.message.reply_text(
            'أهلاً بك في بوت KABA Project لطلبات الشراء! 🛍️ أنا هنا لمساعدتك في الحصول على منتجاتك العالمية بكل سهولة.\n'
            'للبدء، يرجى تزويدي بالمعلومات التالية عن المنتج الذي تبحث عنه.'
        )
        await update.message.reply_text('ما هو اسم المنتج الذي تبحث عنه؟ 📝')

    # دالة للتعامل مع رسائل المستخدم (النصية والصور)
    async def handle_message(update, context):
        user_id = update.message.from_user.id
        
        if user_id not in user_data:
            await update.message.reply_text('الرجاء البدء باستخدام أمر /start أولاً.')
            return

        current_stage = user_data[user_id]['stage']

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
            await update.message.reply_text('يرجى إدخال اسم المستخدم الخاص بك على تيليجرام (يبدأ بـ @). 👤')
        
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
                    
                    try:
                        with open('buyer_requests.txt', 'a', encoding='utf-8') as f:
                            f.write(f"--- طلب جديد من المستخدم {user_id} ---\n")
                            for key, value in user_data[user_id].items():
                                if key != 'stage':
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
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start)) 
        application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

        # Replit provides the PORT environment variable
        PORT = int(os.environ.get("PORT", 8080))
        
        # Replit Deployments provide the external URL as 'REPL_SLUG.REPL_OWNER.repl.co' or as a custom domain
        # For Deployments, Replit provides a dedicated URL (e.g., https://[deployment-id].replit.app)
        # We will set the full WEBHOOK_URL as an environment variable in Replit Deployments
        WEBHOOK_URL = os.environ.get('WEBHOOK_URL')

        if not WEBHOOK_URL:
            logging.error("WEBHOOK_URL environment variable not set.")
            raise ValueError("Environment variable WEBHOOK_URL is not set. Please set it in Replit Deployment environment variables.")

        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="", # Replit's webhook will hit the root path directly
            webhook_url=WEBHOOK_URL
        )

    if __name__ == '__main__':
        main()
    
