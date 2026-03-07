from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from core.attribute_schema import DataType
from modules.interface.bot_interface.states import DynamicCollectorState
from modules.users.domain.organization import Organization
from ..logic.get_next_attribute import ask_next_attribute
from modules.catalog.infrastructure.s3_service import S3Service

router = Router()

@router.message(DynamicCollectorState.file_upload, F.document | F.photo)
async def process_file_upload(message: types.Message, state: FSMContext, bot) -> None:
    """
    Handles file/document and photo upload.
    Identifies the organization, initializes a tenant-specific S3Service,
    and uploads the file directly to MinIO.
    """
    data = await state.get_data()
    schema = data["schema"]
    index = data["attr_index"]
    field = schema[index]
    data_type = field.get("data_type", DataType.FILE)

    item_uuid = data["item_uuid"]
    org_id = data.get("organization_id")

    try:
        org = await Organization.objects.aget(id=org_id)
    except Organization.DoesNotExist:
        await message.answer("❌ Помилка: Організацію не знайдено.")
        return

    if message.document:
        file_id = message.document.file_id
        original_name = message.document.file_name or "file"
    elif message.photo:
        file_id = message.photo[-1].file_id
        original_name = f"photo_{file_id[:8]}.jpg"
    else:
        return

    file_info = await bot.get_file(file_id)
    file_content = await bot.download_file(file_info.file_path)

    s3_service = S3Service(org=org)

    s3_key = f"products/{item_uuid}/{field['key']}_{original_name}"

    s3_path = await sync_to_async(s3_service.upload_fileobj)(
        file_data=file_content,
        s3_key=s3_key
    )

    collected = data.get("collected", {})

    if data_type == DataType.FILE_ARRAY:
        file_uploads = data.get("file_uploads", [])
        file_uploads.append(s3_path)
        await state.update_data(file_uploads=file_uploads)

        await message.answer(
            f"📎 Файл «{original_name}» додано.\n"
            f"Всього завантажено: {len(file_uploads)}",
            reply_markup=message.reply_markup
        )
    else:
        collected[field["key"]] = s3_path
        await state.update_data(collected=collected, attr_index=index + 1)

        await message.answer(f"✅ Файл «{original_name}» збережено.")
        await ask_next_attribute(message, state)


@router.callback_query(DynamicCollectorState.file_upload, F.data == "finish_files")
async def finish_files(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Finalizes the FILE_ARRAY collection and moves to the next attribute.
    """
    data = await state.get_data()
    schema = data["schema"]
    index = data["attr_index"]
    field = schema[index]

    files = data.get("file_uploads", [])
    collected = data.get("collected", {})

    collected[field["key"]] = files

    await state.update_data(
        collected=collected,
        attr_index=index + 1,
        file_uploads=[]
    )

    await callback.answer()
    await callback.message.answer(f"✅ Додано файлів: {len(files)}")
    await ask_next_attribute(callback.message, state)
