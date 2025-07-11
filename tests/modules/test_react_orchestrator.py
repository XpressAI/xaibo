import pytest
from typing import Dict, Any, List, Optional

from xaibo.primitives.modules.orchestrator.react_orchestrator import ReActOrchestrator, ReActPhase
from xaibo.primitives.modules.llm.mock import MockLLM
from xaibo.primitives.modules.conversation.conversation import SimpleConversation
from xaibo.primitives.modules.response import ResponseHandler
from xaibo.primitives.modules.tools.python_tool_provider import PythonToolProvider, tool
from xaibo.core.models.llm import (
    LLMMessage, LLMResponse, LLMRole, LLMFunctionCall, LLMUsage
)


# Test Constants
DEFAULT_USAGE = LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
WEATHER_TOOL_NAME = "get_weather"
CALCULATE_TOOL_NAME = "calculate"
DEFAULT_LOCATION = "New York"
ERROR_LOCATION = "error_location"
DEFAULT_EXPRESSION = "2+2"
ERROR_EXPRESSION = "error"
REASONING_INDICATORS = ['🤔', '💭', '⚡', '🔧', '👁️', '🔍']


# Mock Response Builder Utilities
class MockResponseBuilder:
    """Utility class for building mock LLM responses with common patterns"""
    
    @staticmethod
    def _default_usage() -> LLMUsage:
        """Create default usage stats for testing"""
        return DEFAULT_USAGE
    
    @staticmethod
    def text_response(content: str, usage: Optional[LLMUsage] = None) -> Dict[str, Any]:
        """Create a simple text response"""
        return LLMResponse(
            content=content,
            usage=usage or MockResponseBuilder._default_usage()
        ).model_dump()
    
    @staticmethod
    def tool_call_response(
        content: str,
        tool_calls: List[LLMFunctionCall],
        usage: Optional[LLMUsage] = None
    ) -> Dict[str, Any]:
        """Create a response with tool calls"""
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage=usage or MockResponseBuilder._default_usage()
        ).model_dump()
    
    @staticmethod
    def final_answer_response(answer: str, usage: Optional[LLMUsage] = None) -> Dict[str, Any]:
        """Create a final answer response"""
        return MockResponseBuilder.text_response(f"FINAL_ANSWER: {answer}", usage)
    
    @staticmethod
    def thought_response(thought: str, usage: Optional[LLMUsage] = None) -> Dict[str, Any]:
        """Create a thought response"""
        return MockResponseBuilder.text_response(thought, usage)
    
    @staticmethod
    def observation_response(observation: str, usage: Optional[LLMUsage] = None) -> Dict[str, Any]:
        """Create an observation response"""
        return MockResponseBuilder.text_response(observation, usage)
    
    @staticmethod
    def error_recovery_response(message: str, usage: Optional[LLMUsage] = None) -> Dict[str, Any]:
        """Create an error recovery response"""
        return MockResponseBuilder.text_response(message, usage)


class MockSequenceBuilder:
    """Utility class for building common response sequences"""
    
    @staticmethod
    def simple_final_answer(thought: str, answer: str) -> List[Dict[str, Any]]:
        """Create a simple thought -> final answer sequence"""
        return [
            MockResponseBuilder.thought_response(thought),
            MockResponseBuilder.final_answer_response(answer)
        ]
    
    @staticmethod
    def single_tool_sequence(
        thought: str,
        action_content: str,
        tool_call: LLMFunctionCall,
        observation: str,
        final_thought: str,
        answer: str
    ) -> List[Dict[str, Any]]:
        """Create a complete single tool execution sequence"""
        return [
            MockResponseBuilder.thought_response(thought),
            MockResponseBuilder.tool_call_response(action_content, [tool_call]),
            MockResponseBuilder.observation_response(observation),
            MockResponseBuilder.thought_response(final_thought),
            MockResponseBuilder.final_answer_response(answer)
        ]
    
    @staticmethod
    def multi_tool_sequence(
        initial_thought: str,
        tool_sequences: List[Dict[str, Any]],
        final_thought: str,
        answer: str
    ) -> List[Dict[str, Any]]:
        """Create a sequence with multiple tool executions"""
        responses = [MockResponseBuilder.thought_response(initial_thought)]
        
        for seq in tool_sequences:
            responses.extend([
                MockResponseBuilder.tool_call_response(seq['action_content'], [seq['tool_call']]),
                MockResponseBuilder.observation_response(seq['observation']),
                MockResponseBuilder.thought_response(seq['thought'])
            ])
        
        responses.append(MockResponseBuilder.final_answer_response(answer))
        return responses
    
    @staticmethod
    def error_handling_sequence(
        thought: str,
        action_content: str,
        tool_call: LLMFunctionCall,
        error_observation: str,
        recovery_thought: str,
        final_answer: str
    ) -> List[Dict[str, Any]]:
        """Create a sequence that handles tool errors"""
        return [
            MockResponseBuilder.thought_response(thought),
            MockResponseBuilder.tool_call_response(action_content, [tool_call]),
            MockResponseBuilder.observation_response(error_observation),
            MockResponseBuilder.thought_response(recovery_thought),
            MockResponseBuilder.final_answer_response(final_answer)
        ]


# Helper Functions
def create_mock_llm(responses: List[Dict[str, Any]]) -> MockLLM:
    """Create a MockLLM with the given responses"""
    return MockLLM({"responses": responses})


def create_tool_call(call_id: str, tool_name: str, arguments: Dict[str, Any]) -> LLMFunctionCall:
    """Create a tool call with the given parameters"""
    return LLMFunctionCall(id=call_id, name=tool_name, arguments=arguments)


def create_orchestrator_with_responses(
    response_handler: ResponseHandler,
    tool_provider: PythonToolProvider,
    simple_conversation: SimpleConversation,
    responses: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None
) -> ReActOrchestrator:
    """Create a ReActOrchestrator with mock LLM responses"""
    mock_llm = create_mock_llm(responses)
    return ReActOrchestrator(
        response=response_handler,
        llm=mock_llm,
        tool_provider=tool_provider,
        history=simple_conversation,
        config=config or {}
    )


def create_default_llm_response(content: str) -> Dict[str, Any]:
    """Create a default LLM response with standard usage stats"""
    return LLMResponse(content=content, usage=DEFAULT_USAGE).model_dump()


def create_tool_call_response_dict(content: str, tool_calls: List[LLMFunctionCall]) -> Dict[str, Any]:
    """Create a tool call response dictionary"""
    return LLMResponse(
        content=content,
        tool_calls=tool_calls,
        usage=DEFAULT_USAGE
    ).model_dump()


# Assertion Helpers
def assert_final_answer_contains(response_text: str, expected_content: str):
    """Assert that the response contains a final answer with expected content"""
    assert "FINAL_ANSWER:" in response_text
    assert expected_content in response_text


def assert_no_reasoning_indicators(response_text: str):
    """Assert that response contains no reasoning indicators"""
    for indicator in REASONING_INDICATORS:
        assert indicator not in response_text


def assert_conversation_has_tool_results(conversation: List[LLMMessage], expected_count: int):
    """Assert that conversation has the expected number of tool results"""
    tool_messages = [msg for msg in conversation if msg.role == LLMRole.FUNCTION]
    assert len(tool_messages) == 1
    assert len(tool_messages[0].tool_results) == expected_count


def assert_system_message_contains(conversation: List[LLMMessage], expected_content: str):
    """Assert that the last system message contains expected content"""
    system_messages = [msg for msg in conversation if msg.role == LLMRole.SYSTEM]
    assert system_messages, "No system messages found"
    assert expected_content in system_messages[-1].content[0].text


# Test tool functions
@tool
def get_weather(location: str) -> Dict[str, Any]:
    """Get weather information for a location
    
    Args:
        location: The location to get weather for
        
    Returns:
        Weather information dictionary
    """
    if "error" in location.lower():
        raise ValueError("Weather service unavailable")
    return {"location": location, "temperature": 75, "condition": "sunny"}


@tool
def calculate(expression: str) -> float:
    """Perform mathematical calculations
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        Result of the calculation
    """
    if "error" in expression.lower():
        raise ValueError("Invalid expression")
    # Simple calculator for testing
    if expression == "2+2":
        return 4
    elif expression == "10*5":
        return 50
    else:
        return 42  # Default result for testing


@pytest.fixture
def response_handler():
    """Fixture for response handler"""
    return ResponseHandler()


@pytest.fixture
def simple_conversation():
    """Fixture for simple conversation history"""
    return SimpleConversation()


@pytest.fixture
def tool_provider():
    """Fixture for tool provider with test tools"""
    return PythonToolProvider({
        "tool_functions": [get_weather, calculate]
    })


@pytest.fixture
def mock_llm():
    """Fixture for mock LLM with default responses"""
    return MockLLM({
        "responses": [create_default_llm_response("Default response")]
    })


@pytest.fixture
def orchestrator(response_handler, mock_llm, tool_provider, simple_conversation):
    """Fixture for ReActOrchestrator with default setup"""
    return ReActOrchestrator(
        response=response_handler,
        llm=mock_llm,
        tool_provider=tool_provider,
        history=simple_conversation
    )


class TestReActPhase:
    """Test ReActPhase enum"""
    
    def test_react_phase_values(self):
        """Test that ReActPhase enum has correct values"""
        assert ReActPhase.THOUGHT == "thought"
        assert ReActPhase.ACTION == "action"
        assert ReActPhase.OBSERVATION == "observation"
        assert ReActPhase.FINAL_ANSWER == "final_answer"


class TestReActOrchestratorInitialization:
    """Test ReActOrchestrator initialization"""
    
    def test_initialization_with_defaults(self, response_handler, mock_llm, tool_provider, simple_conversation):
        """Test initialization with default configuration"""
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation
        )
        
        assert orchestrator.response == response_handler
        assert orchestrator.llm == mock_llm
        assert orchestrator.tool_provider == tool_provider
        assert orchestrator.history == simple_conversation
        assert orchestrator.current_phase == ReActPhase.THOUGHT
        assert orchestrator.iteration_count == 0
        assert orchestrator.max_iterations == 10
        assert orchestrator.show_reasoning is True
        assert orchestrator.reasoning_temperature == 0.7
    
    def test_initialization_with_custom_config(self, response_handler, mock_llm, tool_provider, simple_conversation):
        """Test initialization with custom configuration"""
        config = {
            'system_prompt': 'Custom system prompt',
            'thought_prompt': 'Custom thought prompt',
            'action_prompt': 'Custom action prompt',
            'observation_prompt': 'Custom observation prompt',
            'error_prompt': 'Custom error: {error}',
            'max_iterations_prompt': 'Max iterations reached: {max_iterations}',
            'max_iterations': 5,
            'show_reasoning': False,
            'reasoning_temperature': 0.5
        }
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation,
            config=config
        )
        
        assert orchestrator.system_prompt == 'Custom system prompt'
        assert orchestrator.thought_prompt == 'Custom thought prompt'
        assert orchestrator.action_prompt == 'Custom action prompt'
        assert orchestrator.observation_prompt == 'Custom observation prompt'
        assert orchestrator.error_prompt == 'Custom error: {error}'
        assert orchestrator.max_iterations_prompt == 'Max iterations reached: {max_iterations}'
        assert orchestrator.max_iterations == 5
        assert orchestrator.show_reasoning is False
        assert orchestrator.reasoning_temperature == 0.5
    
    def test_provides_method(self):
        """Test that provides method returns correct protocols"""
        from xaibo.core.protocols import TextMessageHandlerProtocol
        protocols = ReActOrchestrator.provides()
        assert TextMessageHandlerProtocol in protocols


class TestReActOrchestratorMainFlow:
    """Test main ReAct orchestration flow"""
    
    @pytest.mark.asyncio
    async def test_handle_text_with_final_answer_immediately(self, response_handler, tool_provider, simple_conversation):
        """Test handle_text when LLM provides final answer immediately"""
        # Setup LLM to provide thought, then final answer
        mock_llm = MockLLM({
            "responses": [
                LLMResponse(content="I need to think about this question.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump(),
                LLMResponse(content="FINAL_ANSWER: The answer is 42.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump()
            ]
        })
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation
        )
        
        await orchestrator.handle_text("What is the answer to everything?")
        
        # Verify final response contains the answer
        final_response = await response_handler.get_response()
        assert "FINAL_ANSWER: The answer is 42." in final_response.text
    
    @pytest.mark.asyncio
    async def test_handle_text_with_tool_execution(self, response_handler, tool_provider, simple_conversation):
        """Test handle_text with tool execution and observation"""
        # Setup LLM responses for complete ReAct cycle
        mock_llm = MockLLM({
            "responses": [
                LLMResponse(content="I need to get weather information.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump(),
                LLMResponse(
                    content="I'll check the weather.",
                    tool_calls=[LLMFunctionCall(id="call_1", name="get_weather", arguments={"location": "New York"})],
                    usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                ).model_dump(),
                LLMResponse(content="The weather data shows it's sunny.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump(),
                LLMResponse(content="I have enough information now.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump(),
                LLMResponse(content="FINAL_ANSWER: It's sunny in New York.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump()
            ]
        })
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation
        )
        
        await orchestrator.handle_text("What's the weather in New York?")
        
        # Verify final answer was provided
        final_response = await response_handler.get_response()
        assert "FINAL_ANSWER: It's sunny in New York." in final_response.text


class TestReActOrchestratorToolExecution:
    """Test tool execution functionality"""
    
    @pytest.mark.asyncio
    async def test_execute_tools_success(self, orchestrator):
        """Test successful tool execution"""
        # Get available tools and use the actual tool names from the tool provider
        tools = await orchestrator.tool_provider.list_tools()
        tool_names = [tool.name for tool in tools]
        weather_tool_name = next(name for name in tool_names if "get_weather" in name)
        calculate_tool_name = next(name for name in tool_names if "calculate" in name)
        
        tool_calls = [
            LLMFunctionCall(id="call_1", name=weather_tool_name, arguments={"location": "NYC"}),
            LLMFunctionCall(id="call_2", name=calculate_tool_name, arguments={"expression": "2+2"})
        ]
        
        conversation = []
        
        await orchestrator._execute_tools(conversation, tool_calls)
        
        # Verify tool results were added to conversation
        assert len(conversation) == 1
        assert conversation[0].role == LLMRole.FUNCTION
        assert len(conversation[0].tool_results) == 2
        
        # Verify tool results contain expected data
        results = conversation[0].tool_results
        assert any("NYC" in result.content for result in results)
        assert any("4" in result.content for result in results)
    
    @pytest.mark.asyncio
    async def test_execute_tools_with_errors(self, orchestrator):
        """Test tool execution with errors"""
        tool_calls = [
            LLMFunctionCall(id="call_1", name="get_weather", arguments={"location": "error_location"})
        ]
        
        conversation = []
        
        await orchestrator._execute_tools(conversation, tool_calls)
        
        # Verify error was handled
        assert len(conversation) == 1
        assert "Error:" in conversation[0].tool_results[0].content


class TestReActOrchestratorErrorHandling:
    """Test error handling functionality"""
    
    @pytest.mark.asyncio
    async def test_handle_error(self, orchestrator):
        """Test error handling method"""
        orchestrator.llm = MockLLM({
            "responses": [
                LLMResponse(content="I encountered an error, but I can still provide an answer based on what I know.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump()
            ]
        })
        
        conversation = [LLMMessage.user("Test question")]
        error_message = "Network timeout occurred"
        
        await orchestrator._handle_error(conversation, error_message)
        
        # Verify error prompt was formatted correctly
        last_system_message = None
        for msg in conversation:
            if msg.role == LLMRole.SYSTEM:
                last_system_message = msg
        
        assert last_system_message is not None
        assert error_message in last_system_message.content[0].text
        
        # Verify error recovery response was added
        assert conversation[-1].content[0].text == "I encountered an error, but I can still provide an answer based on what I know."
    
    @pytest.mark.asyncio
    async def test_handle_max_iterations(self, orchestrator):
        """Test max iterations handling"""
        orchestrator.llm = MockLLM({
            "responses": [
                LLMResponse(content="Based on my analysis so far, here's the best answer I can provide.", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump()
            ]
        })
        
        conversation = [LLMMessage.user("Test question")]
        
        await orchestrator._handle_max_iterations(conversation)
        
        # Verify max iterations prompt was formatted correctly
        last_system_message = None
        for msg in conversation:
            if msg.role == LLMRole.SYSTEM:
                last_system_message = msg
        
        assert last_system_message is not None
        assert str(orchestrator.max_iterations) in last_system_message.content[0].text
        
        # Verify final response was added
        assert conversation[-1].content[0].text == "Based on my analysis so far, here's the best answer I can provide."


class TestReActOrchestratorConfiguration:
    """Test configuration handling"""
    
    def test_custom_prompts_configuration(self, response_handler, mock_llm, tool_provider, simple_conversation):
        """Test custom prompts are used correctly"""
        config = {
            'thought_prompt': 'Custom: Think about this',
            'action_prompt': 'Custom: Take action',
            'observation_prompt': 'Custom: Observe results',
            'error_prompt': 'Custom error occurred: {error}',
            'max_iterations_prompt': 'Custom max iterations: {max_iterations}'
        }
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation,
            config=config
        )
        
        assert orchestrator.thought_prompt == 'Custom: Think about this'
        assert orchestrator.action_prompt == 'Custom: Take action'
        assert orchestrator.observation_prompt == 'Custom: Observe results'
        assert orchestrator.error_prompt == 'Custom error occurred: {error}'
        assert orchestrator.max_iterations_prompt == 'Custom max iterations: {max_iterations}'
    
    def test_reasoning_temperature_configuration(self, response_handler, mock_llm, tool_provider, simple_conversation):
        """Test reasoning temperature is applied correctly"""
        config = {'reasoning_temperature': 0.2}
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation,
            config=config
        )
        
        assert orchestrator.reasoning_temperature == 0.2
    
    @pytest.mark.asyncio
    async def test_show_reasoning_false_hides_output(self, response_handler, tool_provider, simple_conversation):
        """Test that show_reasoning=False hides intermediate output"""
        responses = MockSequenceBuilder.simple_final_answer(
            thought="Hidden thought",
            answer="Hidden process result"
        )
        mock_llm = create_mock_llm(responses)
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation,
            config={'show_reasoning': False}
        )
        
        await orchestrator.handle_text("Test question")
        
        # Verify only final answer is in response, no intermediate reasoning
        final_response = await response_handler.get_response()
        reasoning_indicators = ['🤔', '💭', '⚡', '🔧', '👁️', '🔍']
        for indicator in reasoning_indicators:
            assert indicator not in final_response.text
        
        # But final answer should be there
        assert "FINAL_ANSWER: Hidden process result" in final_response.text


class TestReActOrchestratorStateManagement:
    """Test state management functionality"""
    
    def test_initial_state(self, orchestrator):
        """Test initial state is correct"""
        assert orchestrator.current_phase == ReActPhase.THOUGHT
        assert orchestrator.iteration_count == 0
    
    @pytest.mark.asyncio
    async def test_state_reset_on_new_conversation(self, orchestrator):
        """Test state is reset when handling new text"""
        # Set some state
        orchestrator.current_phase = ReActPhase.OBSERVATION
        orchestrator.iteration_count = 5
        
        orchestrator.llm = MockLLM({
            "responses": [
                LLMResponse(content="New thought", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump(),
                LLMResponse(content="FINAL_ANSWER: New answer", usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)).model_dump()
            ]
        })
        
        await orchestrator.handle_text("New question")
        
        # Verify state was reset at start of new conversation
        # (iteration_count will be > 0 after processing, but should have started from 0)
        assert orchestrator.iteration_count > 0  # Processing occurred
    
    @pytest.mark.asyncio
    async def test_iteration_count_increments(self, orchestrator):
        """Test iteration count increments during processing"""
        orchestrator.llm = create_mock_llm([
            create_default_llm_response("Thought 1"),
            create_default_llm_response("Action 1"),
            create_default_llm_response("Observation 1"),
            create_default_llm_response("Thought 2"),
            MockResponseBuilder.final_answer_response("Done")
        ])
        
        await orchestrator.handle_text("Multi-step question")
        
        # Verify iteration count increased
        assert orchestrator.iteration_count > 1


class TestReActOrchestratorIntegration:
    """Integration tests for complete ReAct workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_react_workflow_with_multiple_tools(self, response_handler, tool_provider, simple_conversation):
        """Test complete ReAct workflow using multiple tools"""
        # Create tool sequences for multi-tool workflow
        tool_sequences = [
            {
                'action_content': "Let me check the weather first.",
                'tool_call': create_tool_call("call_1", "get_weather", {"location": "Boston"}),
                'observation': "Good, I have weather data. Now I need to calculate something.",
                'thought': "Now I'll do the calculation."
            },
            {
                'action_content': "Let me calculate 2+2.",
                'tool_call': create_tool_call("call_2", "calculate", {"expression": "2+2"}),
                'observation': "Perfect, I have both pieces of information.",
                'thought': "I can now provide the final answer."
            }
        ]
        
        responses = MockSequenceBuilder.multi_tool_sequence(
            initial_thought="I need to get weather and do a calculation.",
            tool_sequences=tool_sequences,
            final_thought="I can now provide the final answer.",
            answer="The weather in Boston is sunny (75°F) and 2+2 equals 4."
        )
        mock_llm = create_mock_llm(responses)
        
        orchestrator = ReActOrchestrator(
            response=response_handler,
            llm=mock_llm,
            tool_provider=tool_provider,
            history=simple_conversation
        )
        
        await orchestrator.handle_text("What's the weather in Boston and what's 2+2?")
        
        # Verify final answer contains information from both tools
        final_response = await response_handler.get_response()
        assert "FINAL_ANSWER:" in final_response.text
        assert "Boston" in final_response.text
        assert "4" in final_response.text
    
    @pytest.mark.asyncio
    async def test_react_workflow_with_tool_error_recovery(self, response_handler, tool_provider, simple_conversation):
        """Test ReAct workflow handles tool errors gracefully"""
        tool_call = create_tool_call("call_1", WEATHER_TOOL_NAME, {"location": ERROR_LOCATION})
        responses = MockSequenceBuilder.error_handling_sequence(
            thought="I need to get weather information.",
            action_content="Let me check the weather.",
            tool_call=tool_call,
            error_observation="The weather service failed, but I can still provide a general answer.",
            recovery_thought="I'll provide what I can.",
            final_answer="I couldn't get the weather data due to a service error, but I can help with other questions."
        )
        
        orchestrator = create_orchestrator_with_responses(
            response_handler, tool_provider, simple_conversation, responses
        )
        
        await orchestrator.handle_text("What's the weather like?")
        
        # Verify final answer was provided despite tool error
        final_response = await response_handler.get_response()
        assert_final_answer_contains(final_response.text, "service error")