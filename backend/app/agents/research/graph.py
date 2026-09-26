"""The Research LangGraph graph.

    START -> plan_searches -> search_web -> read_pages
                  ^                             |  one Send per page (parallel)
                  |                             v
                  |                       extract_claims
                  |                             |
                  +--- keep_searching ----- review_round --- done ---> assemble_result -> END

"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Send

from app.agents.research import nodes
from app.agents.research.schemas import ResearchRequest, ResearchResult
from app.agents.research.state import PageTask, ResearchContext, ResearchState


def fan_out_pages(state: ResearchState) -> list[Send] | str:
    """Send each page to its own `extract_claims` branch, or skip ahead when there are none."""
    if not state["pages"]:
        return "review_round"

    titles = {hit.url: hit.title for hit in state["to_read"]}
    return [
        Send(
            "extract_claims",
            PageTask(request=state["request"], page=page, title=titles.get(page.url, "")),
        )
        for page in state["pages"]
    ]


def after_review(state: ResearchState) -> str:
    """Follow the decision `review_round` made."""
    return "plan_searches" if state["keep_searching"] else "assemble_result"


def build_research_graph() -> CompiledStateGraph:
    """Build and compile the graph"""
    builder = StateGraph(ResearchState, context_schema=ResearchContext)

    builder.add_node("plan_searches", nodes.plan_searches)
    builder.add_node("search_web", nodes.search_web)
    builder.add_node("read_pages", nodes.read_pages)
    builder.add_node("extract_claims", nodes.extract_claims)
    builder.add_node("review_round", nodes.review_round)
    builder.add_node("assemble_result", nodes.assemble_result)

    builder.add_edge(START, "plan_searches")
    builder.add_edge("plan_searches", "search_web")
    builder.add_edge("search_web", "read_pages")
    builder.add_conditional_edges("read_pages", fan_out_pages, ["extract_claims", "review_round"])
    builder.add_edge("extract_claims", "review_round")
    builder.add_conditional_edges("review_round", after_review, ["plan_searches", "assemble_result"])
    builder.add_edge("assemble_result", END)

    return builder.compile()


async def run_research(
    request: ResearchRequest,
    context: ResearchContext,
    graph: CompiledStateGraph | None = None,
) -> ResearchResult:
    """Research one course end to end"""
    graph = graph or build_research_graph()
    final_state = await graph.ainvoke({"request": request, "round_number": 0}, context=context)
    return final_state["result"]
