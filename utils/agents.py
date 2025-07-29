import anthropic
from pathlib import Path

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_agent_task(agent_name: str, task_name: str, model: str = "claude-3-sonnet-20240229", max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """
    Runs a specific agent on a specific task using Claude.

    :param agent_name: The relative path of the agent markdown (e.g. 'growth/growth-hacker.md')
    :param task_name: The relative path of the task markdown (e.g. 'growth-hacker__referral-loop-test.md')
    :param model: Claude model to use (opus/sonnet/haiku)
    :param max_tokens: Max tokens for Claude response
    :param temperature: Claude temperature (creativity)
    :return: Claude's output as a string
    """
    
    agent_path = Path(f"agents/{agent_name}")
    task_path = Path(f"tasks/{task_name}")

    if not agent_path.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_path}")
    if not task_path.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")

    agent_instructions = agent_path.read_text()
    task_instructions = task_path.read_text()

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=agent_instructions,
        messages=[
            {"role": "user", "content": task_instructions}
        ]
    )

    return response.content[0].text
