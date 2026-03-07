from aiogram import Router
from .entrypoint import router as entry_router
from .handlers import (
    category_selection, boolean_input, static_ref_input,
    manual_text_input, file_upload, skip_attribute
)

router = Router()

router.include_router(entry_router)
router.include_router(category_selection.router)
router.include_router(boolean_input.router)
router.include_router(static_ref_input.router)
router.include_router(file_upload.router)
router.include_router(skip_attribute.router)
router.include_router(manual_text_input.router)
