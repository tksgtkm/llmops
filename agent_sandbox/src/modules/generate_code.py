from src.llms.apis import openai
from src.llms.models import LLMResponse
from src.llms.utils import load_template
from src.models import DataThread, Program

def generate_code(
    data_info: str,
    user_request: str,
    remote_save_dir: str = "output/process_id/id",
    previous_thread: DataThread | None = None,
    model: str = "gpt-6.1-terra",
    template_file: str = "src/prompts/generate_code.jinja"
) -> LLMResponse:
    template = load_template(template_file)
    system_message = template.render(
        data_info=data_info,
        remote_save_dir=remote_save_dir
    )
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"タスク要求: {user_request}"},
    ]
    if previous_thread:
        messages.append({"role": "assistant", "content": previous_thread.code})
        if previous_thread.stdout and previous_thread.stderr:
            messages.extend(
                [
                    {"role": "system", "content": f"stdout: {previous_thread.stdout}"},
                    {"role": "system", "content": f"stderr: {previous_thread.stderr}"},
                ],
            )
        if previous_thread.observation:
            messages.append(
                {
                    "role": "user",
                    "content": f"以下を参考にして、ユーザー要求を満たすコードを再生成してください: {previous_thread.observation}",
                },
            )
    return openai.generate_response(
        messages,
        model=model,
        response_format=Program
    )