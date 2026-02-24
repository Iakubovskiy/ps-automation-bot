"""
Module for FSM (Finite State Machine) states definition.
"""
from aiogram.fsm.state import State, StatesGroup

# pylint: disable=too-few-public-methods
class CollectorState(StatesGroup):
    """
    States for the knife content collection process.
    """
    name = State()
    price = State()
    sheath_color = State()
    blade_engravings = State()
    sheath_engravings = State()
    accessories = State()
    mount_type = State()
    steel = State()
    handle_material = State()
    media_photos = State()
    media_video = State()
    youtube_link = State()
