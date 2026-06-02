"""Tests for the sister-bot voice-leakage guard in the Telegram Platform Adapter."""

import os
import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from gateway.config import Platform, PlatformConfig
from gateway.platforms.telegram import TelegramAdapter

class TestTelegramSisterBotGuard:

    def _make_adapter(self, sister_usernames=""):
        adapter = object.__new__(TelegramAdapter)
        adapter.platform = Platform.TELEGRAM
        adapter.config = PlatformConfig(enabled=True, token="***")
        adapter._bot = SimpleNamespace(id=999, username="hermes_bot")
        adapter._mention_patterns = adapter._compile_mention_patterns()
        
        # Stub configuration helpers
        adapter._telegram_allowed_topics = lambda: set()
        adapter._telegram_ignored_threads = lambda: set()
        adapter._telegram_exclusive_bot_mentions = lambda: False
        adapter._telegram_allowed_chats = lambda: set()
        adapter._telegram_free_response_chats = lambda: set()
        adapter._telegram_require_mention = lambda: True
        adapter._is_callback_user_authorized = lambda *_a, **_kw: True
        
        return adapter

    def _make_mention_entity(self, offset, length, entity_type="mention"):
        return SimpleNamespace(
            type=entity_type,
            offset=offset,
            length=length,
            user=None
        )

    def test_sister_bot_not_configured(self):
        """When HERMES_SISTER_BOT_USERNAMES is not set, no leakage guard applies."""
        adapter = self._make_adapter()
        
        # Create message mentioning @EdgeOmniraBot
        entity = self._make_mention_entity(0, 15)
        msg = SimpleNamespace(
            text="@EdgeOmniraBot hello",
            caption=None,
            entities=[entity],
            caption_entities=[],
            message_thread_id=None,
            chat=SimpleNamespace(id=-100, type="group"),
            from_user=SimpleNamespace(id=111),
            reply_to_message=None,
        )
        
        with patch.dict(os.environ, {"HERMES_SISTER_BOT_USERNAMES": ""}):
            assert adapter._message_mentions_sister_bot(msg) is False

    def test_sister_bot_mentions_detected(self):
        """When HERMES_SISTER_BOT_USERNAMES is set, mentions are correctly matched."""
        adapter = self._make_adapter()
        
        entity = self._make_mention_entity(0, 15)
        msg = SimpleNamespace(
            text="@EdgeOmniraBot hello",
            caption=None,
            entities=[entity],
            caption_entities=[],
            message_thread_id=None,
            chat=SimpleNamespace(id=-100, type="group"),
            from_user=SimpleNamespace(id=111),
            reply_to_message=None,
        )
        
        # Set env var
        with patch.dict(os.environ, {"HERMES_SISTER_BOT_USERNAMES": "EdgeOmniraBot, EvoOmniraBot"}):
            assert adapter._message_mentions_sister_bot(msg) is True

    def test_sister_bot_with_hermes_mention_ignored(self):
        """If Hermes itself is also mentioned, it is not treated as leakage (Hermes should process)."""
        adapter = self._make_adapter()
        
        # Hermes mention at 0, Sister bot mention at 12
        e1 = self._make_mention_entity(0, 11)  # @hermes_bot
        e2 = self._make_mention_entity(12, 15) # @EdgeOmniraBot
        msg = SimpleNamespace(
            text="@hermes_bot @EdgeOmniraBot hello",
            caption=None,
            entities=[e1, e2],
            caption_entities=[],
            message_thread_id=None,
            chat=SimpleNamespace(id=-100, type="group"),
            from_user=SimpleNamespace(id=111),
            reply_to_message=None,
        )
        
        with patch.dict(os.environ, {"HERMES_SISTER_BOT_USERNAMES": "EdgeOmniraBot, EvoOmniraBot"}):
            assert adapter._message_mentions_sister_bot(msg) is False

    def test_should_process_message_filters_sister_bot(self):
        """Verify that _should_process_message returns False when a sister bot is mentioned."""
        adapter = self._make_adapter()
        
        entity = self._make_mention_entity(0, 15)
        msg = SimpleNamespace(
            text="@EdgeOmniraBot hello",
            caption=None,
            entities=[entity],
            caption_entities=[],
            message_thread_id=None,
            chat=SimpleNamespace(id=-100, type="group"),
            from_user=SimpleNamespace(id=111),
            reply_to_message=None,
        )
        
        with patch.dict(os.environ, {"HERMES_SISTER_BOT_USERNAMES": "EdgeOmniraBot, EvoOmniraBot"}):
            # Sister bot mentioned -> should NOT process
            assert adapter._should_process_message(msg) is False

        with patch.dict(os.environ, {"HERMES_SISTER_BOT_USERNAMES": ""}):
            # Sister bot not configured -> falls back to require_mention check (which would be False unless Hermes is mentioned)
            assert adapter._should_process_message(msg) is False
