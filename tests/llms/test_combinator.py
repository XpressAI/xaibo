
import pytest

from xaibo.core.models.llm import LLMMessage, LLMOptions, LLMResponse, LLMRole, LLMMessageContent, \
    LLMMessageContentType, LLMUsage
from xaibo.primitives.modules.llm.combinator import LLMCombinator
from xaibo.primitives.modules.llm.mock import MockLLM



@pytest.fixture
def mock_llms():
    return [
        MockLLM({
            "responses": [LLMResponse(
                content="Response from LLM 1",
                usage=LLMUsage(
                    prompt_tokens=1,
                    completion_tokens=2,
                    total_tokens=3
                )
            ).model_dump()]
        }),
        MockLLM({
            "responses": [LLMResponse(
                content="Response from LLM 2",
                usage=LLMUsage(
                    prompt_tokens=1,
                    completion_tokens=2,
                    total_tokens=3
                )
            ).model_dump()]
        }),
        MockLLM({
            "responses": [LLMResponse(
                content="Response from LLM 3",
                usage=LLMUsage(
                    prompt_tokens=1,
                    completion_tokens=2,
                    total_tokens=3
                )
            ).model_dump()]
        })
    ]


@pytest.fixture
def prompts():
    return [
        "Specialized prompt for LLM 1",
        "Specialized prompt for LLM 2",
        "Specialized prompt for LLM 3"
    ]


@pytest.fixture
def input_messages():
    return [
        LLMMessage.system("Original system message"),
        LLMMessage.user("User message")
    ]

    
def test_init_validates_prompts_length( mock_llms):
    # Test with matching length
    config = {"prompts": ["Prompt 1", "Prompt 2", "Prompt 3"]}
    combinator = LLMCombinator(mock_llms, config)
    assert len(combinator.lmms) == len(combinator.prompts)
    
    # Test with mismatched length
    config = {"prompts": ["Prompt 1", "Prompt 2"]}
    with pytest.raises(ValueError, match=f"Number of prompts \(2\) does not match number of LLMs \(3\)"):
        LLMCombinator(mock_llms, config)

    with pytest.raises(ValueError, match=f"Number of prompts \(0\) does not match number of LLMs \(3\)"):
        LLMCombinator(mock_llms)

@pytest.mark.asyncio
async def test_generate( mock_llms, prompts, input_messages):
    # Setup
    config = {"prompts": prompts}
    combinator = LLMCombinator(mock_llms, config)
    options = LLMOptions(temperature=0.7)
    
    # Test
    response = await combinator.generate(input_messages, options)
    
    # Verify the final response is a merge of all responses
    assert "Response from LLM 1" in response.content
    assert "Response from LLM 2" in response.content
    assert "Response from LLM 3" in response.content

@pytest.mark.asyncio
async def test_generate_stream( mock_llms, prompts, input_messages):
    # Setup
    config = {"prompts": prompts}
    combinator = LLMCombinator(mock_llms, config)
    options = LLMOptions(temperature=0.7)
    
    # Test
    chunks = []
    async for chunk in combinator.generate_stream(input_messages, options):
        chunks.append(chunk)

    all_out = "".join(chunks)
    
    # Verify we got chunks from all LLMs
    assert "Response from LLM 1" in all_out
    assert "Response from LLM 2" in all_out
    assert "Response from LLM 3" in all_out

def test_adapt_system_prompt_with_existing_system( mock_llms, prompts):
    # Setup
    combinator = LLMCombinator(mock_llms, {"prompts": prompts})
    messages = [
        LLMMessage.system("Original system message"),
        LLMMessage.user("User message")
    ]
    intermediate_results = [LLMResponse(content="Previous result")]
    
    # Test
    result = combinator._adapt_system_prompt(messages, "Specialized prompt", intermediate_results)
    
    # Verify the system message was updated
    assert len(result) == 3  # Original messages + intermediate assistant message
    assert result[0].role == LLMRole.SYSTEM
    
    # Check that the system prompt was appended, not replaced
    system_content = result[0].content
    assert len(system_content) == 2
    assert system_content[0].text == "Original system message"
    assert system_content[1].text == "Specialized prompt"
    
    # Check that intermediate responses were added as assistant messages
    assert result[2].role == LLMRole.ASSISTANT
    assert result[2].content[0].text == "Previous result"

def test_adapt_system_prompt_without_existing_system( mock_llms, prompts):
    # Setup
    combinator = LLMCombinator(mock_llms, {"prompts": prompts})
    messages = [
        LLMMessage.user("User message")
    ]
    intermediate_results = [LLMResponse(content="Previous result")]
    
    # Test
    result = combinator._adapt_system_prompt(messages, "Specialized prompt", intermediate_results)
    
    # Verify a new system message was added at the beginning
    assert len(result) == 3  # New system + original user + intermediate assistant
    assert result[0].role == LLMRole.SYSTEM
    assert result[0].content[0].text == "Specialized prompt"
    
    # Original message preserved
    assert result[1].role == LLMRole.USER
    assert result[1].content[0].text == "User message"
    
    # Intermediate results added
    assert result[2].role == LLMRole.ASSISTANT
    assert result[2].content[0].text == "Previous result"