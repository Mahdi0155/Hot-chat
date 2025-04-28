from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loader import dp

# تعریف مراحل ثبت پروفایل
class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_purpose = State()
    waiting_for_photo = State()

# هندلر دکمه "ایجاد پروفایل"
@dp.message_handler(text="ایجاد پروفایل")
async def start_create_profile(message: types.Message):
    await message.answer("لطفا اسم خود را وارد کنید:")
    await ProfileStates.waiting_for_name.set()

# دریافت اسم کاربر
@dp.message_handler(state=ProfileStates.waiting_for_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(types.InlineKeyboardButton(text="پسر", callback_data="gender_boy"),
                 types.InlineKeyboardButton(text="دختر", callback_data="gender_girl"))
    await message.answer("جنسیت خود را انتخاب کنید:", reply_markup=keyboard)
    await ProfileStates.waiting_for_gender.set()
  # دریافت جنسیت کاربر
@dp.callback_query_handler(lambda c: c.data.startswith('gender_'), state=ProfileStates.waiting_for_gender)
async def get_gender(callback_query: types.CallbackQuery, state: FSMContext):
    gender = callback_query.data.split("_")[1]
    await state.update_data(gender=gender)
    await callback_query.message.answer("سن خود را به صورت عددی وارد کنید (بین 10 تا 99):")
    await ProfileStates.waiting_for_age.set()
    await callback_query.answer()

# دریافت سن کاربر
@dp.message_handler(state=ProfileStates.waiting_for_age)
async def get_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("سن باید به صورت عددی باشد. لطفا دوباره تلاش کنید:")
        return
    age = int(message.text)
    if age < 10 or age > 99:
        await message.answer("سن باید بین 10 تا 99 باشد. لطفا دوباره وارد کنید:")
        return
    await state.update_data(age=age)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="فقط چت", callback_data="purpose_chat"),
        types.InlineKeyboardButton(text="رابطه عاطفی", callback_data="purpose_love"),
        types.InlineKeyboardButton(text="عاطفی و جنسی", callback_data="purpose_both")
    )
    await message.answer("هدف خود از ارتباط را انتخاب کنید:", reply_markup=keyboard)
    await ProfileStates.waiting_for_purpose.set()
  # دریافت هدف کاربر
@dp.callback_query_handler(lambda c: c.data.startswith('purpose_'), state=ProfileStates.waiting_for_purpose)
async def get_purpose(callback_query: types.CallbackQuery, state: FSMContext):
    purpose = callback_query.data.split("_")[1]
    await state.update_data(purpose=purpose)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="ارسال عکس پروفایل", callback_data="send_photo"),
        types.InlineKeyboardButton(text="رد کردن و ادامه", callback_data="skip_photo")
    )
    await callback_query.message.answer("می‌خواهید عکس پروفایل ارسال کنید یا رد کنید؟", reply_markup=keyboard)
    await ProfileStates.waiting_for_photo_decision.set()
    await callback_query.answer()

# تصمیم درباره عکس پروفایل
@dp.callback_query_handler(lambda c: c.data in ['send_photo', 'skip_photo'], state=ProfileStates.waiting_for_photo_decision)
async def photo_decision(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "send_photo":
        await callback_query.message.answer("لطفاً عکس پروفایل خود را ارسال کنید:")
        await ProfileStates.waiting_for_photo.set()
    else:
        await state.update_data(photo=None)
        await finish_profile(callback_query.message, state)
    await callback_query.answer()

# دریافت عکس پروفایل
@dp.message_handler(content_types=types.ContentType.PHOTO, state=ProfileStates.waiting_for_photo)
async def get_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await finish_profile(message, state)
  # اتمام ثبت پروفایل
async def finish_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    user_profiles[user_id] = {
        "name": data.get("name"),
        "gender": data.get("gender"),
        "age": data.get("age"),
        "purpose": data.get("purpose"),
        "photo": data.get("photo")
    }
    await message.answer("پروفایل شما با موفقیت ایجاد شد!")
    await state.finish()

# مشاهده پروفایل
@dp.message_handler(lambda message: message.text == "مشاهده پروفایل")
async def view_profile(message: types.Message):
    user_id = message.from_user.id
    profile = user_profiles.get(user_id)
    if not profile:
        await message.answer("شما هنوز پروفایلی ایجاد نکرده‌اید. لطفاً ابتدا پروفایل بسازید.")
        return

    profile_text = (
        f"نام: {profile['name']}\n"
        f"جنسیت: {profile['gender']}\n"
        f"سن: {profile['age']}\n"
        f"هدف: {profile['purpose']}"
    )

    if profile.get('photo'):
        await message.answer_photo(profile['photo'], caption=profile_text)
    else:
        await message.answer(profile_text)
      # هندل خطا برای ورودی های غیرمجاز هنگام ثبت پروفایل
@dp.message_handler(state=ProfileStates.name)
async def process_name_error(message: types.Message):
    await message.answer("لطفاً فقط اسم خود را وارد کنید.")

@dp.message_handler(state=ProfileStates.age)
async def process_age_error(message: types.Message):
    await message.answer("لطفاً سن معتبر وارد کنید (فقط عدد بین 10 تا 99).")

# جلوگیری از کلیک روی دکمه‌های دیگر بدون پروفایل
@dp.message_handler(lambda message: message.text in ["مشاهده پروفایل", "استارت چت", "دعوت دوستان", "درخواست اسپانسر شدن"])
async def handle_buttons_without_profile(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_profiles:
        await message.answer("لطفاً ابتدا پروفایل خود را ایجاد کنید.")
    else:
        await message.answer(f"این بخش در حال توسعه است... لطفاً منتظر بمانید.")
