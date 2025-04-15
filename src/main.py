from pydantic_ai import Agent, RunContext
import logfire
from pydantic_ai.mcp import MCPServerStdio
import asyncio
from dotenv import load_dotenv

load_dotenv()

logfire.configure()
logfire.instrument_mcp()
logfire.instrument_pydantic_ai()

postgresql_mcp_server = MCPServerStdio(
    "npx",
    args=[
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:postgres@localhost:5432/dvdrental",
    ],
)

middleware_agent = Agent(
    "openai:o3-mini",
    instrument=True,
    system_prompt="You are a middleware AI agent responsible for analyzing and transforming user queries into safe, precise, read-only PostgreSQL commands that adhere to the dvdrental database schema, invoking the proper database tools as needed.",
)
postgresql_agent = Agent(
    "openai:o3-mini", mcp_servers=[postgresql_mcp_server], instrument=True
)


@middleware_agent.tool
async def contact_db(ctx: RunContext[None], query: str) -> str:
    r = await postgresql_agent.run(query)
    return r.data


async def main():
    async with postgresql_agent.run_mcp_servers():
        while True:
            command = input("You: ")
            if command.lower() in ("exit", "quit"):
                break
            agent_response = await middleware_agent.run(command)
            print(agent_response)


asyncio.run(main())
