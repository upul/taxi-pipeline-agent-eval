import json

from openai import OpenAI

from taxi_agent.agent.tool_schemas import tools
from taxi_agent.agent.tools import get_monthly_statistics
from taxi_agent.config import get_env

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=get_env("OPENROUTER_API_KEY"),
)

if __name__ == "__main__":
    messages = [
        {
            "role": "system",
            "content": "You are a helpful data engineering assistant.",
        },
        {
            "role": "user",
            "content": "What was the average taxi trip cost in January 2025?",
        },
    ]

    response = client.chat.completions.create(
        model=get_env("OPENROUTER_MODEL"),
        messages=messages,
        temperature=0.3,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message
    # Append your current message
    messages.append(message)

    # Process all tool calls requested by the model
    if message.tool_calls:
        for call in message.tool_calls:
            print(f"Function: {call.function.name}")
            print(f"Arguments: {call.function.arguments}")
            print(f"Tool call ID: {call.id}")

            if call.function.name == "get_monthly_statistics":
                # Parse JSON string arguments into a Python dictionary
                args = json.loads(call.function.arguments)
                result = get_monthly_statistics(**args)
                print("Tool Result:", result)

                # 3. Append the tool execution response back to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result),
                    }
                )
            else:
                raise ValueError(f"Unsupported tool: {call.function.name}")

        # 4. Send the updated conversation history back to the model for the final answer
        final_response = client.chat.completions.create(
            model=get_env("OPENROUTER_MODEL"), messages=messages, temperature=0.3
        )

        print("\nFinal Model Response:")
        print(final_response.choices[0].message.content)
    else:
        print("Model responded directly without calling tools:")
        print(message.content)
