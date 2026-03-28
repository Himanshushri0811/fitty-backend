import json
import asyncio
import logging
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from .ai_service import get_fitty_ai_response

logger = logging.getLogger(__name__)

class FittyState:
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"

class VoiceConsumer(AsyncWebsocketConsumer):
    """
    MASTER VOICE CONSUMER (v7.0 - SYNCED & STABILIZED)
    Tasks: 
    - Full State Machine transitions (IDLE, LISTENING, PROCESSING, SPEAKING).
    - Sync AI response to Chat UI (Task 4).
    - Handle Barge-In (Interrupt) during TTS (Task 2 & 3).
    - Performance Tuning (<2s target) (Task 5).
    """

    async def connect(self):
        self.state = FittyState.IDLE
        self.current_task = None
        await self.accept()
        print(f"DEBUG: 🔌 Fitty Voice Connected | INITIAL STATE: {self.state}")
        # Task 5: Initialize in LISTENING
        await self.set_state(FittyState.LISTENING)

    async def disconnect(self, close_code):
        print(f"DEBUG: 💀 WebSocket Disconnected: {close_code} | RESETTING STATE")
        if self.current_task:
            self.current_task.cancel()
        self.state = FittyState.IDLE

    async def set_state(self, new_state):
        """Strict State Machine (Task 3)."""
        if self.state == new_state:
            return
            
        print(f"STATE: {self.state} → {new_state}")
        self.state = new_state
        await self.send(json.dumps({
            "type": "state",
            "state": self.state
        }))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except Exception:
            return

        msg_type = data.get("type")

        # 🛑 Task 2: Handle Interrupt (Barge-In)
        if msg_type == "interrupt":
            print("INTERRUPT SIGNAL RECEIVED!")
            if self.current_task:
                self.current_task.cancel()
                self.current_task = None
            # Immediate transition back to listening
            await self.set_state(FittyState.LISTENING)
            return

        # 🎤 Task 5: Performance - Immediate trigger on Query
        if msg_type == "query":
            user_query = data.get("query", "").strip()
            if not user_query: return

            print(f"INCOMING VOICE QUERY: '{user_query}'")
            
            # Prevent race conditions
            if self.state == FittyState.PROCESSING:
                return

            if self.current_task:
                self.current_task.cancel()

            # Task 3: PROCESSING state transition
            await self.set_state(FittyState.PROCESSING)
            self.current_task = asyncio.create_task(self.process_query(user_query))

    async def process_query(self, query):
        try:
            # Task 4 & 7: Optimized system instruction
            voice_instruction = (
                "You are Fitty, a professional Indian Fitness Coach. "
                "Structure your reply with Headings (#) and Bullets (-). "
                "Voice style: Energetic, motivating, Champ!"
            )

            # Task 5: Fast logic execution
            response_text = await get_fitty_ai_response(query, voice_instruction)

            if asyncio.current_task().cancelled():
                return

            # Task 1: 📤 Sync full structured text to frontend (Chat bubble)
            await self.send(json.dumps({
                "type": "ai_response",
                "message": response_text
            }))

            # Task 3: SPEAKING state transition
            await self.set_state(FittyState.SPEAKING)

            # Task 5: Chunked streaming to Voice components
            sentences = re.split(r'(?<=[.?!])\s+', response_text.strip())
            for sentence in sentences:
                if not sentence.strip(): continue
                # Sanitized for voice (Removing '#' and '-' for clearer TTS)
                clean_voice = re.sub(r'[#\-*]', '', sentence).strip()
                
                print(f"OUTGOING SPEECH CHUNK: {clean_voice}")
                await self.send(json.dumps({
                    "type": "response",
                    "message": clean_voice
                }))
                
                if asyncio.current_task().cancelled(): return

            # Brief pause for playback
            await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            print("STATE: Interrupted during processing.")
        except Exception as e:
            print(f"STATE ERROR: {e}")
        finally:
            # Task 3 & 5: GOTO LISTENING
            if self.state != FittyState.IDLE:
                await self.set_state(FittyState.LISTENING)
            self.current_task = None
