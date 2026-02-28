import requests
from dotenv import load_dotenv
from dataclasses import dataclass
load_dotenv()

from langchain.chat_models import init_chat_model
# from langchain.messages import SystemMessage, HumanMessage, AIMessage
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver



# conversation = [
#     SystemMessage("You are a helpful assistant for questions regarding programming"),
#     HumanMessage("What is Python?"),
#     AIMessage("Python is a high-level, interpreted programming language known for its readability and versatility. It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms, including procedural, object-oriented, and functional programming. It has a large standard library and a vibrant ecosystem of third-party packages, making it popular for web development, data analysis, artificial intelligence, scientific computing, and more."),
#     HumanMessage("When was it created?")
# ]

# response = model.invoke(conversation)
# print(response.content)

@dataclass
class Context:
    user_id: str

@dataclass
class ResponseFormat:
    summary: str
    temperature_celsius: float
    temperature_fahrenheit: float
    humidity: float

@tool('getweather', description="Return weather information for a given city", return_direct=False)
def get_weather(city: str):
    response = requests.get(f"https://wttr.in/{city}?format=j1")
    return response.json()

@tool('locate_user', description="Look up a user's city based on the context", return_direct=False)
def locate_user(runtime: ToolRuntime[Context]):
    match runtime.context.user_id:
        case "ABC123":
            return "New York"
        case "XYZ456":
            return "San Francisco"
        case _:
            return "Unknown"
        
# model = init_chat_model('gemini-2.5-flash', temperature=0.1)
model = init_chat_model('gpt-3.5-turbo', temperature=0.1)

checkpointer = InMemorySaver()


agent = create_agent(
    model=model,
    tools=[get_weather, locate_user],
    system_prompt="You are a helpful assistant that provides weather information, who always cracks jokes and is humurous in nature.",
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

config = {'configurable': {'thread_id': 1}}

response = agent.invoke({
    'messages': [
        {"role": "user", "content": "What is the capital of India?"}
    ]},
    config=config, # type: ignore
    context=Context(user_id="ABC123")
)

print(response['structured_response'].summary)
print(response['structured_response'].temperature_celsius)
print(response['structured_response'].temperature_fahrenheit)
print(response['structured_response'].humidity)