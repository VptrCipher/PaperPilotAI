from langchain_core.messages import HumanMessage, SystemMessage

from prompts.templates import AGENTS, EVALUATOR, RETRIEVAL, ROUTER


def roles(template):
    names = [type(m).__name__.lower() for m in template.messages]
    return ["system" if "system" in n else "human" if "human" in n else "ai" for n in names]


def test_every_template_has_a_system_and_a_user_prompt():
    for template in [ROUTER, RETRIEVAL, EVALUATOR, *AGENTS.values()]:
        kinds = roles(template)
        assert kinds[0] == "system" and kinds[-1] == "human"


def test_routing_and_retrieval_are_few_shot_and_agents_are_zero_shot():
    for template in (ROUTER, RETRIEVAL):
        assert len(template.messages) > 3
    for template in AGENTS.values():
        assert len(template.messages) == 2


def test_templates_render_with_their_variables():
    rendered = ROUTER.format_messages(
        user_request="Summarize it", conversation_context="none", format_feedback="",
    )
    assert isinstance(rendered[0], SystemMessage) and isinstance(rendered[-1], HumanMessage)
    assert "Summarize it" in rendered[-1].content
