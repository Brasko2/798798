"""
Инициализация обработчиков команд
"""

from aiogram import Router
from .admin import router as admin_router
from .start import router as start_router
from .buy import router as buy_router
from .profile import router as profile_router
from .server import router as server_router
from .support import router as support_router
from .referral import router as referral_router
from .instructions import router as instructions_router
from .bonus import router as bonus_router
from .trial import router as trial_router
from .subscriptions import router as subscriptions_router

router = Router()

# Порядок важен! Сначала обработчики админа
router.include_router(admin_router)
router.include_router(start_router)
router.include_router(buy_router)
router.include_router(profile_router)
router.include_router(server_router)
router.include_router(support_router)
router.include_router(referral_router)
router.include_router(instructions_router)
router.include_router(bonus_router)
router.include_router(trial_router)
router.include_router(subscriptions_router)

__all__ = ["router"] 