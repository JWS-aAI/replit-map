from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You talk like a pirate. Answer all questions to the best of your ability.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)



model = ChatOpenAI(model="gpt-3.5-turbo")

# Async function for node:
def call_model(state: MessagesState):
    chain = prompt | model

    response = chain.invoke(state["messages"])
    return {"messages": response}


# Define graph as before:
workflow = StateGraph(state_schema=MessagesState)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
app = workflow.compile(checkpointer=MemorySaver())

config = {"configurable": {"thread_id": "abc123"}}

def call_agent(query: str):
    # print("test")

    input_messages = [HumanMessage(query)]
    output = app.invoke({"messages": input_messages}, config)
    
    # output["messages"][-1].pretty_print()  # output contains all messages in state
    return output["messages"][-1].content