"""FSM states for the dynamic product collector.

Replaces the old hardcoded CollectorState with dynamic attribute stepping.
Current attribute index and schema are tracked in FSM data, not in state names.
"""
from aiogram.fsm.state import State, StatesGroup


class DynamicCollectorState(StatesGroup):
    """States for the dynamic data collection flow.

    The bot progresses through these states:
      1. category_select — user picks a product category
      2. attribute_step — iterates through attribute_schema fields dynamically
                          (current index tracked via FSM data 'attr_index')
      3. media_photos — collect product photos
      4. media_video — optionally upload video or skip
      5. youtube_link — optionally provide YouTube link or skip
    """

    category_select = State()
    attribute_step = State()
    media_photos = State()
    media_video = State()
    youtube_link = State()
