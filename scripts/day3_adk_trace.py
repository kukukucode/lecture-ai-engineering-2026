"""Day3: Google ADKのツール呼び出しを記録する。"""

import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import types

from adk_lecture_agent.agent import root_agent

QUESTION = "第2回の内容から確認問題を1問出して"


async def main():
    runner = InMemoryRunner(
        agent=root_agent,
        app_name="day3_adk_trace",
    )
    session = await runner.session_service.create_session(
        app_name=runner.app_name,
        user_id="day3",
    )

    called_tools = []
    print("[question]", QUESTION)

    async for event in runner.run_async(
        user_id="day3",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=QUESTION)],
        ),
    ):
        for call in event.get_function_calls():
            called_tools.append(call.name)
            print("[tool call]", call.name, call.args)

        for response in event.get_function_responses():
            print("[tool return]", response.name, str(response.response)[:300])

        if event.is_final_response() and event.content:
            for part in event.content.parts or []:
                if part.text:
                    print("[answer]", part.text)

    print("[tools used]", called_tools)


if __name__ == "__main__":
    asyncio.run(main())
