import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from collections import Counter
import pandas as pd
import os

# Bot tokeni va admin ID
API_TOKEN = '7601300058:AAGIUezJ7-JcD-BzlIAA_0npTVfruHi1YEk'
ADMIN_ID = 6148272773

# Bot va Dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

# Test holatlari uchun FSM
class TestState(StatesGroup):
    waiting_for_answer = State()
    finished = State()

# Foydalanuvchilar ma'lumotlari uchun dictionary
users_data = {}

# Excel fayl nomi
EXCEL_FILE = "test_results.xlsx"

# Test 1 savollari: “O‘zingni ta’riflang”
test1_questions = [
    {
        "question": "O‘zingizni qanday shaxs sifatida ta’riflaysiz?",
        "options": {
            "a": "Yangi odamlar bilan tezda do‘stlashadigan va jamoada faol ishtirok etadigan odam.",
            "b": "O‘zimni ko‘proq yolg‘iz yoki kichik doiradagi odam sifatida his qilaman.",
            "c": "Doimiy ravishda o‘zimni rivojlantirishga harakat qiladigan va o‘zgarishlarga tayyor odam.",
            "d": "O‘z fikrlarimga qat’iyan sodiq bo‘lib, boshqalar bilan kamroq muloqot qiladigan odam."
        }
    },
    {
        "question": "O‘zingizni qanday baholaysiz?",
        "options": {
            "a": "O‘zimni juda muvaffaqiyatli va o‘zimga ishonchim komil deb hisoblayman.",
            "b": "O‘zimni ba’zan muvaffaqiyatli, ba’zan esa noaniq his qilaman.",
            "c": "O‘zimni ko‘proq o‘rganish va rivojlanish zarurligini his qilaman.",
            "d": "O‘zimni ko‘proq kamchiliklarimni to‘g‘rilashim kerak deb hisoblayman."
        }
    },
    {
        "question": "Qanday holatlarda o‘zingizni baxtli his qilasiz?",
        "options": {
            "a": "Yangi narsalarni o‘rganish va boshqalar bilan vaqt o‘tkazish.",
            "b": "Yolg‘iz vaqt o‘tkazish va o‘zimni o‘rganish.",
            "c": "Maqsadlarimga erishganimda yoki muvaffaqiyatni qo‘lga kiritganimda.",
            "d": "Oila yoki do‘stlarim bilan o‘zaro yaqin munosabatlarda bo‘lganimda."
        }
    },
    {
        "question": "Stressli vaziyatlarda qanday harakat qilasiz?",
        "options": {
            "a": "Tezda yechim topishga harakat qilaman va muammoni hal qilish uchun amaliyotga o‘taman.",
            "b": "Stressdan qochishga harakat qilaman yoki vaqtincha barchani unuta olishni istayman.",
            "c": "Vaziyatni tahlil qilib, boshqarishga va uni yengishga harakat qilaman.",
            "d": "O‘zini yo‘qotib, qandaydir muddat stressda qolaman, lekin keyinchalik o‘zimni qayta tiklayman."
        }
    },
    {
        "question": "Boshqalar bilan munosabatlaringizni qanday tasvirlaysiz?",
        "options": {
            "a": "Yangi odamlar bilan tezda do‘stlashish va ko‘p odamlar bilan aloqada bo‘lishni yaxshi ko‘raman.",
            "b": "Boshqalar bilan munosabatlarimda ehtiyotkor va nozikman.",
            "c": "Men ba’zan boshqalarga ko‘p ochilmayman, lekin yaqin kishilar bilan mustahkam aloqada bo‘laman.",
            "d": "Men o‘zimni boshqalardan kamroq ajratib turadigan va o‘z fikrlarimga ko‘proq ishonadigan odam sifatida ko‘raman."
        }
    },
    {
        "question": "O‘zingizni qanday o‘zgarishga tayyor deb bilasiz?",
        "options": {
            "a": "Men har doim yangi o‘zgarishlarga tayyorman va ular orqali o‘zgarishni kutaman.",
            "b": "Men o‘zgarishga tayyorman, lekin bir oz vaqt kerak bo'ladi.",
            "c": "O‘zgartirishlarni baholashga tayyorman, lekin ba’zi o‘zgarishlarga qarshi turaman.",
            "d": "Men o‘zgarishga ehtiyotkorlik bilan yondashaman va faqat zarurat tug‘ilganda o‘zgarishga tayyor bo‘laman."
        }
    },
    {
        "question": "O‘zingizni qanday baholashni istaysiz?",
        "options": {
            "a": "O‘zimni juda mustahkam va ishonchli odam sifatida ko‘raman.",
            "b": "O‘zimni ba’zan o‘ziga ishonchli, ba’zan esa noaniq deb his qilaman.",
            "c": "O‘zimni hali o‘ziga ishonch hosil qilmagan, ammo rivojlanishga tayyor deb bilaman.",
            "d": "O‘zimga ishonchim past, va men o‘z ishonchimni oshirish uchun ko‘p ishlashim kerak deb o‘ylayman."
        }
    },
    {
        "question": "Kelajakda qanday o‘zgarishlarni kutyapsiz?",
        "options": {
            "a": "Hayotimdagi har bir sohada ijobiy o‘zgarishlar kutyapman.",
            "b": "Ba’zi o‘zgarishlar men uchun kerakli, lekin ba’zan ularni o‘ylab ko‘rishga vaqtim yo‘q.",
            "c": "Ba’zi o‘zgarishlar muhim, lekin hayotimda ularga tayyor emasman.",
            "d": "Men hayotimda katta o‘zgarishlarni kutmayman, lekin kichik, muhim o‘zgarishlar kerak deb o‘ylayman."
        }
    },
    {
        "question": "O‘zingizni qanday vaziyatda ko‘rasiz?",
        "options": {
            "a": "O‘zimni yuqori darajada muvaffaqiyatga erishgan va o‘z yo‘lini topgan odam sifatida ko‘raman.",
            "b": "O‘zimni o‘z maqsadlarimga erishgan, lekin ba’zi narsalarda hal qilishim kerak bo‘lgan odam sifatida ko‘raman.",
            "c": "O‘zimni kelajakda muvaffaqiyatga erishishga intilayotgan, lekin ba’zan o‘ziga ishonchsiz odam sifatida ko‘raman.",
            "d": "O‘zimni hali kelajakda katta o‘zgarishlar va rivojlanish kutayotgan, lekin ko‘plab savollarim bor odam sifatida ko‘raman."
        }
    },
    {
        "question": "O‘z-o‘zini anglashdagi yondashuvingiz qanday?",
        "options": {
            "a": "Men o‘zimni yaxshi tushunaman va o‘zimga har doim ishonaman.",
            "b": "O‘zimni ba’zan yaxshi tushunaman, lekin ba’zan shubhalarim bo‘ladi.",
            "c": "O‘zimni hali to‘liq tushunmayapman, lekin o‘rganishga tayyorman.",
            "d": "Men o‘zimni to‘liq tushunmayman va ko‘p savollarim bor."
        }
    }
]

# Test 2 savollari: “Aslida qanday insonsiz?”
test2_questions = [
    {
        "question": "Boshqalar bilan tanishishda qanday xulq-atvoringiz bor?",
        "options": {
            "a": "Yangi odamlar bilan tezda tanishaman va ular bilan ijtimoiy aloqalarni o‘rnatishni yaxshi ko‘raman.",
            "b": "Boshqalar bilan tanishishdan oldin bir oz ehtiyotkor bo‘laman, lekin bir necha marta suhbat qilganimdan keyin o‘zimni qulay his qilaman.",
            "c": "Men o‘zimni kamdan-kam yangi odamlar bilan tanishtiraman, ko‘proq yaqin do‘stlar bilan vaqt o‘tkazishni afzal ko‘raman.",
            "d": "Men yangi odamlar bilan muloqot qilishdan qochaman va faqat zarurat tug‘ilganda suhbatlashaman."
        }
    },
    {
        "question": "O‘z hayotingizda qanday qarorlar qabul qilishni afzal ko‘rasiz?",
        "options": {
            "a": "Tez va o‘zgaruvchan qarorlar qabul qilishni yaxshi ko‘raman.",
            "b": "Qarorlar qabul qilishdan oldin barcha imkoniyatlarni baholashga harakat qilaman.",
            "c": "Boshqalarning fikrlarini ko‘proq tinglab, ularning maslahatlariga tayanaman.",
            "d": "Men ko‘proq boshqalar tomonidan qabul qilingan qarorlar asosida harakat qilaman."
        }
    },
    {
        "question": "Sizning uchun do‘stlik qanday ahamiyatga ega?",
        "options": {
            "a": "Do‘stlarim mening eng yaqin odamlarimdir, ular bilan har doim vaqt o‘tkazishdan zavqlanaman.",
            "b": "Do‘stlarimni qadrlayman, lekin ko‘proq yolg‘iz vaqt o‘tkazishni ham yaxshi ko‘raman.",
            "c": "Men ko‘p do‘stlarga ega bo‘lishni istamayman, lekin bir nechta yaqin va sodiq do‘stlarim bo'lishini afzal ko'raman.",
            "d": "Men ko‘proq yolg‘iz bo‘lishni afzal ko‘raman va do‘stlarimni kamdan-kam uchrataman."
        }
    },
    {
        "question": "Sizni qanday stressli vaziyatlarda eng ko‘p ta’sirlanasiz?",
        "options": {
            "a": "O‘zimni tezda yig‘ib olib, vaziyatni tezda hal qilishga harakat qilaman.",
            "b": "Stressni o‘zimda yutib, ba’zan do‘stlarimdan yoki oilamdan yordam so‘rayman.",
            "c": "Stressli vaziyatda menda ko‘p vaqt kerak bo‘ladi, ammo oxir-oqibat qaror qabul qilishga harakat qilaman.",
            "d": "Stressli vaziyatlar meni qiynaydi va uzoq vaqt davomida o‘zimni tinchlantira olmayman."
        }
    },
    {
        "question": "O‘z xatolaringizni qanday qabul qilasiz?",
        "options": {
            "a": "O‘z xatolarimni tezda tan olib, ulardan o‘rganishim kerakligini bilaman.",
            "b": "Xatolarimni tan olishda ba’zan qiynalaman, ammo ularni to‘g‘irlash uchun harakat qilaman.",
            "c": "O‘z xatolarimni tan olishdan yiroqman, lekin vaqt o‘tishi bilan ular haqida o‘ylayman.",
            "d": "Xatolarimni qabul qilish juda qiyin va ba’zan ularni yashirishga harakat qilaman."
        }
    },
    {
        "question": "O‘zgarishlarga qanday qaraysiz?",
        "options": {
            "a": "O‘zgarishlarga tezda moslashishga tayyorman va yangiliklarni kutaman.",
            "b": "O‘zgarishlarni ehtiyotkorlik bilan ko‘rib chiqaman, lekin ular hayotimda zarur bo‘lsa, ularga tayyor bo‘laman.",
            "c": "O‘zgarishlarga qarshi turaman, lekin ba’zida ularni qabul qilishim kerak bo‘ladi.",
            "d": "O‘zgarishlarni qabul qilishda juda qiynalaman va ular meni asabiylashtiradi."
        }
    },
    {
        "question": "Kelajakda qanday odam bo‘lishni xohlaysiz?",
        "options": {
            "a": "O‘zimni muvaffaqiyatga erishgan, o‘z maqsadlariga erishgan va baxtli odam sifatida ko‘raman.",
            "b": "Kelajakda barqaror va baxtli hayotga ega bo‘lishni, lekin ba’zi vaziyatlarda o‘zgarishlarga tayyor bo‘lishni xohlayman.",
            "c": "Men kelajakda ko‘proq o‘ziga ishonadigan va boshqalar bilan yaxshiroq munosabatda bo‘lishni istagan odam bo‘lishni orzu qilaman.",
            "d": "Men kelajakda oddiy hayotga ega bo‘lishni, ortiqcha tashvishlardan saqlanishni va tinch hayot kechirishni xohlayman."
        }
    },
    {
        "question": "Boshqalar bilan bo‘lgan munosabatlar haqida qanday fikrdasiz?",
        "options": {
            "a": "Boshqalar bilan yaqin munosabatlar o‘rnatish va ularga yordam berish men uchun juda muhim.",
            "b": "Men boshqalar bilan munosabatlarimni ehtiyotkorlik bilan tartibga solaman va ularga ko‘proq vaqt ajratishga harakat qilaman.",
            "c": "Boshqalar bilan munosabatlarimni cheklashni afzal ko‘raman, faqat yaqin odamlar bilan vaqt o‘tkazishni xohlayman.",
            "d": "Men boshqalar bilan minimal munosabatda bo‘lishni afzal ko‘raman va odatda yolg‘iz vaqt o‘tkazaman."
        }
    },
    {
        "question": "O‘zingizni qanday odam sifatida ko‘rasiz?",
        "options": {
            "a": "Yangi narsalarni o‘rganishga ochiq, jamoada faol va boshqalarga yordam berishga tayyor odam.",
            "b": "O‘zimni tinch va o‘zimga ishonadigan odam sifatida ko‘raman, lekin ijtimoiy muhitda ehtiyotkor bo‘laman.",
            "c": "O‘zimni ko‘proq o‘z-o‘zini o‘ylaydigan va o‘z fikrlariga sodiq odam sifatida ko‘raman.",
            "d": "O‘zimni ba’zan befarq va ba’zan o‘zini izlab yashovchi odam sifatida ko‘raman."
        }
    },
    {
        "question": "Hissiyotlaringizni boshqarishda qanday yondashasiz?",
        "options": {
            "a": "Hissiyotlarimni tezda anglab, ularga qarshi turishga harakat qilaman.",
            "b": "Hissiyotlarimni boshqarishga harakat qilaman, lekin ba’zida ularga qarshi chiqish qiyin bo‘ladi.",
            "c": "Hissiyotlarimni ko‘proq boshqalar bilan baham ko‘raman, lekin ularga qarshi turishga ba’zan qiynalaman.",
            "d": "Hissiyotlarimni boshqarish juda qiyin va ko‘pincha ularni yashiraman."
        }
    }
]

# Inline keyboard yaratish funksiyasi
def create_options_keyboard(test_type, question_index):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    questions = test1_questions if test_type == "O‘zingni ta’riflang" else test2_questions
    options = questions[question_index]["options"]
    for key in options.keys():
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=key.upper(), callback_data=f"{test_type}_{question_index}_{key}")
        ])
    return keyboard

# Ma'lumotlarni Excel faylga saqlash
def save_to_excel():
    user_answers_data = []
    stats_data = []
    for user_id, user_info in users_data.items():
        # User Answers varaq uchun
        row_answers = {
            "User_ID": user_id,
            "Username": user_info["info"].get("username", "Noma'lum"),
            "First_Name": user_info["info"].get("first_name", "Noma'lum"),
            "Last_Name": user_info["info"].get("last_name", "Noma'lum"),
            "Status": user_info.get("status", "not_started")
        }
        test1_answers = user_info["answers"].get("O‘zingni ta’riflang", [])
        for i, ans in enumerate(test1_answers, 1):
            row_answers[f"Test1_Q{i}"] = ans
        test2_answers = user_info["answers"].get("Aslida qanday insonsiz?", [])
        for i, ans in enumerate(test2_answers, 1):
            row_answers[f"Test2_Q{i}"] = ans
        user_answers_data.append(row_answers)

        # Stats varaq uchun
        row_stats = {
            "User_ID": user_id,
            "Username": user_info["info"].get("username", "Noma'lum"),
            "First_Name": user_info["info"].get("first_name", "Noma'lum"),
            "Last_Name": user_info["info"].get("last_name", "Noma'lum"),
        }
        test1_result = ",".join(sorted(user_info["top_answers"].get("O‘zingni ta’riflang", [])))
        for combo in ["a", "b", "c", "d", "a,b", "a,c", "a,d", "b,c", "b,d", "c,d", "a,b,c", "a,b,d", "a,c,d", "b,c,d", "a,b,c,d"]:
            row_stats[f"Test1_{combo}"] = 1 if test1_result == combo else 0
        test2_result = ",".join(sorted(user_info["top_answers"].get("Aslida qanday insonsiz?", [])))
        for combo in ["a", "b", "c", "d", "a,b", "a,c", "a,d", "b,c", "b,d", "c,d", "a,b,c", "a,b,d", "a,c,d", "b,c,d", "a,b,c,d"]:
            row_stats[f"Test2_{combo}"] = 1 if test2_result == combo else 0
        stats_data.append(row_stats)

    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        pd.DataFrame(user_answers_data).to_excel(writer, sheet_name="User_Answers", index=False)
        pd.DataFrame(stats_data).to_excel(writer, sheet_name="Stats", index=False)

# Start komandasi
@dp.message(Command("start"))
async def send_welcome(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in users_data:
        status = users_data[user_id].get("status", "not_started")
        if status == "finished":
            results = users_data[user_id]["results"]
            response = "📊 *Sizning natijalaringiz:*\n\n"
            response += f"**“O‘zingni ta’riflang”:**\n{results['O‘zingni ta’riflang']}\n\n"
            response += f"**“Aslida qanday insonsiz?”:**\n{results['Aslida qanday insonsiz?']}"
            await message.reply(response, parse_mode="Markdown")
            return
        elif status == "test1_finished":
            await state.set_state(TestState.waiting_for_answer)
            await state.update_data(test_type="Aslida qanday insonsiz?", question_index=0, last_message_id=None)
            question = test2_questions[0]
            options_text = "\n".join([f"**{key.upper()}**: {value}" for key, value in question["options"].items()])
            keyboard = create_options_keyboard("Aslida qanday insonsiz?", 0)
            msg = await bot.send_message(
                message.chat.id,
                f"📝 *“Aslida qanday insonsiz?”*\n\n{question['question']}\n\n{options_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.update_data(last_message_id=msg.message_id)
            users_data[user_id]["status"] = "test2_in_progress"
            save_to_excel()
            await message.delete()
            return
        elif status in ["test1_in_progress", "test2_in_progress"]:
            await message.reply("Siz allaqachon testni boshlagansiz. Iltimos, davom eting!")
            return

    intro = "👋 Bu test o‘zingizni va haqiqiy xarakteringizni aniqlashga yordam beradi.\n" \
            "Test ikki qismdan iborat: *“O‘zingni ta’riflang”* va *“Aslida qanday insonsiz?”*\n" \
            "Tayyorlovchi: RTTM jamoasi.\n\nTest hozir boshlanadi!"
    await message.reply(intro, parse_mode="Markdown")
    await message.delete()

    if user_id not in users_data:
        users_data[user_id] = {
            "info": {
                "id": user_id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name
            },
            "answers": {"O‘zingni ta’riflang": [], "Aslida qanday insonsiz?": []},
            "results": {},
            "top_answers": {"O‘zingni ta’riflang": [], "Aslida qanday insonsiz?": []},
            "status": "test1_in_progress"
        }

    await state.set_state(TestState.waiting_for_answer)
    await state.update_data(test_type="O‘zingni ta’riflang", question_index=0, last_message_id=None)
    question = test1_questions[0]
    options_text = "\n".join([f"**{key.upper()}**: {value}" for key, value in question["options"].items()])
    keyboard = create_options_keyboard("O‘zingni ta’riflang", 0)
    msg = await bot.send_message(
        message.chat.id,
        f"📝 *“O‘zingni ta’riflang”*\n\n{question['question']}\n\n{options_text}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.update_data(last_message_id=msg.message_id)
    save_to_excel()

# Inline tugma bosilganda javobni qabul qilish
@dp.callback_query(TestState.waiting_for_answer)
async def process_callback_answer(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    test_type = data["test_type"]
    question_index = data["question_index"]
    last_message_id = data.get("last_message_id")

    # Callback datadan javobni olish
    _, _, user_answer = callback.data.split("_")

    questions = test1_questions if test_type == "O‘zingni ta’riflang" else test2_questions
    users_data[user_id]["answers"][test_type].append(user_answer)

    # Avvalgi xabarni o‘chirish
    if last_message_id:
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=last_message_id)

    next_question_index = question_index + 1
    if next_question_index < len(questions):
        await state.update_data(question_index=next_question_index)
        next_question = questions[next_question_index]
        options_text = "\n".join([f"**{key.upper()}**: {value}" for key, value in next_question["options"].items()])
        keyboard = create_options_keyboard(test_type, next_question_index)
        msg = await bot.send_message(
            callback.message.chat.id,
            f"📝 *{test_type}*\n\n{next_question['question']}\n\n{options_text}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await state.update_data(last_message_id=msg.message_id)
    else:
        result, top_answers = calculate_result(users_data[user_id]["answers"][test_type], test_type)
        users_data[user_id]["results"][test_type] = result
        users_data[user_id]["top_answers"][test_type] = top_answers
        if test_type == "O‘zingni ta’riflang":
            users_data[user_id]["status"] = "test1_finished"
        else:
            users_data[user_id]["status"] = "finished"
        save_to_excel()
        await bot.send_message(
            callback.message.chat.id,
            f"✅ *{test_type} tugadi!*\n\nNatijangiz:\n{result}",
            parse_mode="Markdown"
        )

        if test_type == "O‘zingni ta’riflang":
            await asyncio.sleep(2)
            await state.update_data(test_type="Aslida qanday insonsiz?", question_index=0)
            question = test2_questions[0]
            options_text = "\n".join([f"**{key.upper()}**: {value}" for key, value in question["options"].items()])
            keyboard = create_options_keyboard("Aslida qanday insonsiz?", 0)
            msg = await bot.send_message(
                callback.message.chat.id,
                f"📝 *“Aslida qanday insonsiz?”*\n\n{question['question']}\n\n{options_text}",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.update_data(last_message_id=msg.message_id)
            users_data[user_id]["status"] = "test2_in_progress"
            save_to_excel()
        else:
            await state.set_state(TestState.finished)

    await callback.answer()

# Natijani hisoblash
def calculate_result(answers, test_type):
    counts = Counter(answers)
    max_count = max(counts.values())
    top_answers = [key for key, value in counts.items() if value == max_count]

    descriptions = {
        "O‘zingni ta’riflang": {
            "a": "Siz o‘zingizni kuchli, ijtimoiy va o‘zgarishga tayyor deb bilasiz.",
            "b": "Siz ehtiyotkor va o‘zgarishga tayyor bo‘lsangiz-da, ba’zida noaniqlik mavjud.",
            "c": "Siz o‘zgarishga ochiq va rivojlanishga tayyor insansiz.",
            "d": "Siz o‘zgarishlarni ehtiyotkorlik bilan ko‘rib chiqasiz."
        },
        "Aslida qanday insonsiz?": {
            "a": "Siz ochiq, ijtimoiy va boshqalar bilan tezda aloqada bo‘lishni yaxshi ko‘rasiz.",
            "b": "Siz ehtiyotkor va o‘zgarishlarga tayyor bo‘lsangiz ham, ba’zan noaniqlikni his qilasiz.",
            "c": "Siz o‘z fikrlaringizga sodiq va ba’zan o‘zingizni cheklab qo‘yishingiz mumkin.",
            "d": "Siz ba’zan o‘z hissiyotlaringizni yashirasiz va boshqalardan uzoqroq bo‘lishni afzal ko‘rasiz."
        }
    }

    if len(top_answers) > 1:
        combined_desc = " ".join([descriptions[test_type][ans] for ans in top_answers])
        return f"Sizning javoblaringizda bir nechta jihatlar bir xil darajada ustun keldi ({', '.join(top_answers)}):\n{combined_desc}", top_answers
    else:
        return descriptions[test_type][top_answers[0]], top_answers

# Admin uchun statistika
@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Bu buyruq faqat admin uchun!")
        return

    if not os.path.exists(EXCEL_FILE):
        await message.reply("Hozircha ma'lumot yo‘q!")
        return

    df_stats = pd.read_excel(EXCEL_FILE, sheet_name="Stats")
    if df_stats.empty:
        await message.reply("Hozircha ma'lumot yo‘q!")
        return

    response = "📈 *Umumiy statistika:*\n\n"
    total_users = len(df_stats)

    response += "**“O‘zingni ta’riflang”:**\n"
    test1_cols = [col for col in df_stats.columns if col.startswith("Test1_")]
    for col in test1_cols:
        count = df_stats[col].sum()
        if count > 0:
            percentage = (count / total_users) * 100
            combo = col.replace("Test1_", "")
            response += f"{combo}: {count} ta ({percentage:.1f}%)\n"

    response += "\n**“Aslida qanday insonsiz?”:**\n"
    test2_cols = [col for col in df_stats.columns if col.startswith("Test2_")]
    for col in test2_cols:
        count = df_stats[col].sum()
        if count > 0:
            percentage = (count / total_users) * 100
            combo = col.replace("Test2_", "")
            response += f"{combo}: {count} ta ({percentage:.1f}%)\n"

    response += f"\n**Jami foydalanuvchilar:** {total_users}"
    await message.reply(response, parse_mode="Markdown")

# Admin uchun faylni yuklab olish
@dp.message(Command("download"))
async def download_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Bu buyruq faqat admin uchun!")
        return

    if not os.path.exists(EXCEL_FILE):
        await message.reply("Hozircha ma'lumot yo‘q, Excel fayl mavjud emas!")
        return

    file = FSInputFile(EXCEL_FILE)
    await bot.send_document(message.chat.id, file, caption="📊 Test natijalari Excel faylda")

# Botni ishga tushirish
async def main():
    if os.path.exists(EXCEL_FILE):
        df_answers = pd.read_excel(EXCEL_FILE, sheet_name="User_Answers")
        df_stats = pd.read_excel(EXCEL_FILE, sheet_name="Stats")
        for _, row in df_answers.iterrows():
            user_id = row["User_ID"]
            users_data[user_id] = {
                "info": {
                    "id": user_id,
                    "username": row["Username"],
                    "first_name": row["First_Name"],
                    "last_name": row["Last_Name"]
                },
                "answers": {
                    "O‘zingni ta’riflang": [row[f"Test1_Q{i}"] for i in range(1, 11) if f"Test1_Q{i}" in row and pd.notna(row[f"Test1_Q{i}"])],
                    "Aslida qanday insonsiz?": [row[f"Test2_Q{i}"] for i in range(1, 11) if f"Test2_Q{i}" in row and pd.notna(row[f"Test2_Q{i}"])]
                },
                "results": {},
                "top_answers": {
                    "O‘zingni ta’riflang": [],
                    "Aslida qanday insonsiz?": []
                },
                "status": row["Status"]
            }
        for _, row in df_stats.iterrows():
            user_id = row["User_ID"]
            if user_id in users_data:
                users_data[user_id]["top_answers"]["O‘zingni ta’riflang"] = [col.replace("Test1_", "") for col in df_stats.columns if col.startswith("Test1_") and row[col] == 1]
                users_data[user_id]["top_answers"]["Aslida qanday insonsiz?"] = [col.replace("Test2_", "") for col in df_stats.columns if col.startswith("Test2_") and row[col] == 1]
                if users_data[user_id]["answers"]["O‘zingni ta’riflang"]:
                    result, _ = calculate_result(users_data[user_id]["answers"]["O‘zingni ta’riflang"], "O‘zingni ta’riflang")
                    users_data[user_id]["results"]["O‘zingni ta’riflang"] = result
                if users_data[user_id]["answers"]["Aslida qanday insonsiz?"]:
                    result, _ = calculate_result(users_data[user_id]["answers"]["Aslida qanday insonsiz?"], "Aslida qanday insonsiz?")
                    users_data[user_id]["results"]["Aslida qanday insonsiz?"] = result
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())