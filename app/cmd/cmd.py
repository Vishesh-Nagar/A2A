import asyncclick as click
import asyncio

from uuid import uuid4
from client.client import A2AClient
from models.task import Task


@click.command()
@click.option(
    "--agent", default="http://localhost:10002", help="Base URL of the A2A agent server"
)
@click.option("--session", default=0, help="Session ID (use 0 to generate a new one)")
@click.option(
    "--history", is_flag=True, help="Print full task history after receiving a response"
)
async def cli(agent: str, session: str, history: bool):
    """
    CLI to send user messages to an A2A agent and display the response.

    Args:
        agent (str): The base URL of the A2A agent server (e.g., http://localhost:10002)
        session (str): Either a string session ID or 0 to generate one
        history (bool): If true, prints the full task history
    """

    client = A2AClient(url=f"{agent}")
    session_id = uuid4().hex if str(session) == "0" else str(session)

    while True:

        prompt = await click.prompt(
            "\nWhat do you want to send to the agent? (type ':q' or 'quit' to exit)"
        )

        if prompt.strip().lower() in [":q", "quit"]:
            break

        payload = {
            "id": uuid4().hex,
            "sessionId": session_id,
            "message": {"role": "user", "parts": [{"type": "text", "text": prompt}]},
        }

        try:

            task: Task = await client.send_task(payload)

            if task.history and len(task.history) > 1:
                reply = task.history[-1]
                print("\nAgent says:", reply.parts[0].text)
            else:
                print("\nNo response received.")

            if history:
                print("\n========= Conversation History =========")
                for msg in task.history:
                    print(f"[{msg.role}] {msg.parts[0].text}")

        except Exception as e:
            import traceback

            traceback.print_exc()

            print(f"\n❌ Error while sending task: {e}")


if __name__ == "__main__":

    asyncio.run(cli())
