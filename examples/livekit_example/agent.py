from __future__ import annotations

import logging
from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    Agent,
    AgentSession
)
from livekit.plugins import openai


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

from livekit.plugins import openai
from livekit.plugins import silero

from xaibo.integrations.livekit import XaiboAgentLoader

# Load agents from YAML configs with debug logging
loader = XaiboAgentLoader()
loader.load_agents_from_directory("./agents")
loader.enable_debug_logging()

# Get LLM for use in LiveKit VoiceAssistant
llm = loader.get_llm("example")

# Use in LiveKit agent
assistant = Agent(
        instructions="",
   vad=silero.VAD.load(),
   stt=openai.STT(),
   llm=llm,  # Xaibo agent as LLM
   tts=openai.TTS(),
)

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    session = AgentSession()

    await session.start(
        agent=assistant,
        room=ctx.room,
    )
    
    logger.info("agent started")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
