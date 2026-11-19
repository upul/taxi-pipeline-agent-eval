import json

from openai import OpenAI
from openinference.instrumentation.openai import OpenAIInstrumentor
from opentelemetry import trace
from phoenix.otel import register

from taxi_agent.agent.tool_schemas import tools
from taxi_agent.agent.tools import get_monthly_statistics, get_trip_breakdown
from taxi_agent.config import get_env

tracer = trace.get_tracer(__name__)

api_key = get_env("OPENROUTER_API_KEY")
model_id = get_env("OPENROUTER_MODEL")

tracer_provider = register(
    project_name="taxi-pipeline-agent",
    endpoint="http://127.0.0.1:6006/v1/traces",
    batch=False,
)

OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

tool_registry = {
    "get_monthly_statistics": get_monthly_statistics,
    "get_trip_breakdown": get_trip_breakdown,
}


def run_agent(
    user_question: str,
    max_iterations: int = 5,
) -> str:
    with tracer.start_as_current_span("run_agent") as agent_span:
        agent_span.set_attribute("openinference.span.kind", "AGENT")
        agent_span.set_attribute("input.value", user_question)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful data engineering assistant.",
            },
            {
                "role": "user",
                "content": user_question,
            },
        ]

        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model=model_id,
                messages=messages,
                temperature=0.3,
                tools=tools,
                tool_choice="auto",
            )

            message = response.choices[0].message
            if not message.tool_calls:
                if message.content:
                    agent_span.set_attribute("output.value", message.content)
                    return message.content

                raise ValueError("LLM returns an empty message")

            messages.append(message)
            for call in message.tool_calls:
                print(f"Executing tool: {call.function.name}")
                print(f"Arguments: {call.function.arguments}")

                if call.function.name in tool_registry:
                    with tracer.start_as_current_span(call.function.name) as tool_span:
                        tool_span.set_attribute("openinference.span.kind", "TOOL")

                        args = json.loads(call.function.arguments)
                        tool_span.set_attribute("input.value", json.dumps(args))

                        result = tool_registry[call.function.name](**args)
                        tool_span.set_attribute("output.value", json.dumps(result))

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call.id,
                                "content": json.dumps(result),
                            }
                        )
                else:
                    raise ValueError(f"Unsupported tool: {call.function.name}")

        raise ValueError(f"Max iterations: {max_iterations} without success")


if __name__ == "__main__":
    result = run_agent(
        user_question="What was the average taxi trip cost in January 2025?",
        max_iterations=5,
    )
    print(result)
    print("----------------")

    result = run_agent(
        user_question="Compare the average taxi trip costs in December 2024 and January 2025. Calculate the percentage change and explain whether the average increased or decreased.",
        max_iterations=5,
    )
    print(result)
    print("----------------")

    result = run_agent(
        user_question="Why did average taxi trip costs decrease between December 2024 and January 2025? Investigate whether changes in trip-distance distribution could help explain the decrease.",
        max_iterations=5,
    )
    print(result)
