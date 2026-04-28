import operator
from typing import Annotated, Literal, Sequence, TypedDict

from langchain_core.utils.function_calling import convert_to_openai_tool
from langgraph.constants import Send
from langgraph.graph import END, START, StateGraph
from langgraph.pregel import Pregel
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.configs import Settings
from src.custom_logger import setup_logger
from src.models import (
    AgentResult,
    Plan,
    ReflectionResult,
    SearchOutput,
    Subtask,
    ToolResult
)
from src.prompts import HelpDeskAgentPrompts

MAX_CHALENGE_COUNT = 3

logger = setup_logger(__file__)

class AgentState(TypedDict):
    question: str
    plan: list[str]
    current_step: int
    substack_results: Annotated[Sequence[Subtask], operator.add]
    last_answer: str

class AgentSubGraphState(TypedDict):
    question: str
    plan: list[str]
    substack: str
    is_completed: bool
    messages: list[ChatCompletionMessageParam]
    challenge_count: int
    tool_results: Annotated[Sequence[Sequence[SearchOutput]], operator.add]
    refrection_results: Annotated[Sequence[ReflectionResult], operator.add]
    substack_answer: str

class HelpDeskAgent:

    def __init__(
            self, 
            settings: Settings, 
            tools: list = [], 
            prompts: HelpDeskAgentPrompts = HelpDeskAgentPrompts()
        ) -> None:
        self.settings = settings
        self.tools = tools
        self.tool_map = {tool.name: tool for tool in tools}
        self.prompts = prompts
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def create_plan(self, state: AgentState) -> dict:
        logger.info("Starting plan generation process...")

        system_prompt = self.prompts.planner_system_prompt

        user_prompt = self.prompts.planner_user_prompt.format(
            question=state["question"]
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        logger.debug(f"Final prompt messages: {messages}")

        try:
            logger.info("Sending request to OpenAI...")
            response = self.client.beta.chat.completions.parse(
                model=self.settings.openai_model,
                messages=messages,
                response_format=Plan,
                seed=0
            )
            logger.info("Successfully received response from OpenAI")
        except Exception as e:
            logger.error(f"Error during OpenAI request: {e}")
            raise

        plan = response.choices[0].message.parsed

        logger.info("Plan generation complete")

        return {"plan": plan.substacks}
    
    def select_tools(self, state: AgentSubGraphState) -> dict:
        logger.info("Starting tool selection process...")

        logger.debug("Converting tools for OpenAI format...")
        openai_tools = [convert_to_openai_tool(tool) for tool in self.tools]

        if state["challenge_count"] == 0:
            logger.debug("Creating user prompt for tool selection...")
            user_prompt = self.prompts.subtask_tool_selection_user_prompt.format(
                question=state["question"],
                plan=state["plan"],
                subtask=state["subtask"]
            )

            messages = [
                {"role": "system", "content": self.prompts.subtask_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        else:
            logger.debug("Creating user prompt for tool retry...")

            messages: list = state["messages"]

            messages = [message for message in messages if message["role"] != "tool" or "tool_calls" not in message]

            user_retry_prompt = self.prompts.subtask_retry_answer_user_prompt
            user_message = {"role": "user", "content": user_retry_prompt}
            messages.append(user_message)
        
        try:
            logger.info("Sending request to OpenAI...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                tools=openai_tools,
                seed=0
            )
            logger.info("Successfully received response from OpenAI")
        except Exception as e:
            logger.error(f"Error during OpenAI request: {e}")
            raise

        if response.choices[0].message.tool_calls is None:
            raise ValueError("Tool calls are None")
        
        ai_messages = {
            "role": "assistant",
            "tool_calls": [tool_call.model_dump() for tool_call in response.choices[0].message.tool_calls]
        }

        logger.info("Tool selecting complete!")
        messages.append(ai_messages)

        return {"messages": messages}
    
    def execute_tools(self, state: AgentSubGraphState) -> dict:
        logger.info("Starting tool execution process...")
        messages = state["messages"]

        tool_calls = messages[-1]["tool_calls"]

        if tool_calls is None:
            logger.error("Tool calls are None")
            logger.error(f"Messages: {messages}")
            raise ValueError("Tool calls are None")
        
        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = tool_call["function"]["arguments"]

            tool = self.tool_map[tool_name]
            tool_result: list[SearchOutput] = tool.invoke(tool_args)

            tool_results.append(
                ToolResult(
                    tool_name=tool_name,
                    args=tool_args,
                    results=tool_result
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "content": str(tool_result),
                    "tool_call_id": tool_call["id"]
                }
            )

        logger.info("Tool execution complete!")
        return {"messages": messages, "tool_results": [tool_results]}
    
    def create_subtask_answer(self, state: AgentSubGraphState) -> dict:
        logger.info("Starting subtask answer creation process...")
        messages = state["messages"]

        try:
            logger.info("Sending request to OpenAI...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                seed=0
            )
            logger.info("Successfully received response from OpenAI")
        except Exception as e:
            logger.error(f"Error during OpenAI request: {e}")
            raise

        subtask_answer = response.choices[0].message.content

        ai_message = {"role": "assistant", "content": subtask_answer}
        messages.append(ai_message)

        logger.info("Subtask answer creation complete!")

        return {
            "messages": messages,
            "subtask_answer": subtask_answer
        }
    
    def reflect_subtask(self, state: AgentSubGraphState) -> dict:
        logger.info("Starting refrection process...")
        messages = state["messages"]

        user_prompt = self.prompts.subtask_reflection_user_prompt

        messages.append({"role": "user", "content": user_prompt})

        try:
            logger.info("Sending request to OpenAI...")
            response = self.client.beta.chat.completions.parse(
                model=self.settings.openai_model,
                messages=messages,
                response_format=ReflectionResult,
                seed=0
            )
            logger.info("Successfully received response from OpenAI")
        except Exception as e:
            logger.error(f"Error during OpenAI request: {e}")
            raise

        reflection_result = response.choices[0].message.parsed
        if reflection_result is None:
            raise ValueError("Reflection result is None")
        
        messages.append(
            {
                "role": "assistant",
                "content": reflection_result.model_dump_json()
            }
        )

        update_state = {
            "messages": messages,
            "reflection_results": [reflection_result],
            "challenge_count": state["challenge_count"] + 1,
            "is_completed": reflection_result.is_compiled
        }

        if update_state["challenge_count"] >= MAX_CHALENGE_COUNT and not reflection_result.is_compiled:
            update_state["subtask_answer"] = f"{state["subtask"]}の回答が見つかりませんでした"
        
        logger.info("Reflection complete!")
        return update_state
    
    def create_answer(self, state: AgentState) -> dict:
        logger.info("Starting final answer creation process...")
        system_prompt = self.prompts.create_last_answer_system_prompt

        subtask_results = [(result.task_name, result.subtask_answer) for result in state["subtask_results"]]
        user_prompt = self.prompts.create_last_answer_user_prompt.format(
            question=state["question"],
            plan=state["plan"],
            subtask_results=str(subtask_results)
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            logger.info("Sending request to OpenAI...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                seed=0
            )
            logger.info("Successfully received response from OpenAI")
        except Exception as e:
            logger.info(f"Error during OpenAI request: {e}")
            raise

        logger.info("Final answer creation complete!")

        return {"last_answer": response.choices[0].message.content}
    
    def _execute_subgraph(self, state: AgentState):
        subgraph = self._create_subgraph()

        result = subgraph.invoke(
            {
                "question": state["question"],
                "plan": state["plan"],
                "subtask": state["plan"][state["current_step"]],
                "current_step": state["current_step"],
                "is_compiled": False,
                "challenge_count": 0,
            }
        )

        subtask_result = Subtask(
            task_name=result["subtask"],
            tool_result=result["tool_results"],
            reflection_results=result["reflection_results"],
            is_completed=result["subtask_answer"],
            challenge_count=result["challenge_count"]
        )

        return {"subtask_results": [subtask_result]}
    
    def _should_continue_exec_subtasks(self, state: AgentState) -> list:
        return [
            Send(
                "execute_subtasks",
                {
                    "question": state["question"],
                    "plan": state["plan"],
                    "current_step": idx
                }
            ) for idx, _ in enumerate(state["plan"])
        ]
    
    def _should_continue_exec_subtask_flow(self, state: AgentSubGraphState) -> Literal["end", "continue"]:
        if state["is_completed"] or state["challenge_count"] >= MAX_CHALENGE_COUNT:
            return "end"
        else:
            return "continue"
    
    def _create_subgraph(self) -> Pregel:

        workflow = StateGraph(AgentSubGraphState)

        workflow.add_node("select_tools", self.select_tools)

        workflow.add_node("execute_tools", self.execute_tools)

        workflow.add_node("create_subtask_answer", self.create_subtask_answer)

        workflow.add_node("reflect_subtask", self.reflect_subtask)

        workflow.add_edge(START, "select_tools")

        workflow.add_edge("select_tools", "execute_tools")
        workflow.add_edge("execute_tools", "create_subtask_answer")
        workflow.add_edge("create_subtask_answer", "reflect_subtask")

        workflow.add_conditional_edges(
            "reflect_subtask",
            self._should_continue_exec_subtask_flow,
            {"continue": "select_tools", "end": END}
        )

        app = workflow.compile()

        return app
    
    def create_graph(self) -> Pregel:
        workflow = StateGraph(AgentState)

        workflow.add_node("create_plan", self.create_plan)

        workflow.add_node("execute_subtasks", self._execute_subgraph)

        workflow.add_node("create answer", self.create_answer)

        workflow.add_edge(START, "create_plan")

        workflow.add_conditional_edges(
            "create_plan",
            self._should_continue_exec_subtasks
        )

        workflow.add_edge("execute_subtasks", "create_answer")

        workflow.set_finish_point("create_answer")

        app = workflow.compile()

        return app
    
    def run_agent(self, question: str) -> AgentResult:
        app = self.create_graph()
        result = app.invoke(
            {
                "question": question,
                "current_step": 0
            }
        )
        return AgentResult(
            question=question,
            plan=Plan(substacks=result["plan"]),
            subtasks=result["subtask_results"],
            answer=result["last_answer"]
        )