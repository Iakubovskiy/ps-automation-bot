from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from modules.users.domain.user import User as PlatformUser
from modules.catalog.infrastructure.category_repository import CategoryRepository
from modules.interface.bot_interface.keyboards.keyboards import get_category_keyboard
from services.file_manager import generate_item_uuid
from modules.interface.bot_interface.states import DynamicCollectorState

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    user = await PlatformUser.objects.filter(telegram_id=message.from_user.id, is_active=True).select_related(
        "organization").afirst()

    if not user:
        await message.answer("⚠️ Вас не зареєстровано.")
        return

    org_id = str(user.organization_id)
    categories = await CategoryRepository.afind_by_organization(org_id)

    await state.update_data(item_uuid=generate_item_uuid(), photos=[], collected={}, organization_id=org_id,
                            user_id=str(user.id))
    await message.answer(f"Привіт! Оберіть категорію:",
                         reply_markup=get_category_keyboard([{"id": c.id, "name": c.name} for c in categories]))
    await state.set_state(DynamicCollectorState.category_select)
