from langgraph.graph import StateGraph, START, END
from core.state import AgenticState
from core.market import AutomatedMarketMaker
from graph.nodes import get_operative_node, get_evaluator_node, get_broker_node, get_devops_node, bankruptcy_node
from graph.edges import router_broker_or_devops, router_continue

def build_aem_graph(amm: AutomatedMarketMaker) -> StateGraph:
    """
    Construye y compila el StateGraph para la simulación AEM,
    inyectando la instancia de AMM. (Sin base de datos, 100% cliente HTTP).
    """
    graph = StateGraph(AgenticState)
    
    # Inyectar dependencias a los nodos mediante factories
    operative = get_operative_node(amm)
    evaluator = get_evaluator_node()
    broker = get_broker_node(amm)
    devops = get_devops_node()
    
    # Añadiendo nodos
    graph.add_node("operative", operative)
    graph.add_node("evaluator", evaluator)
    graph.add_node("broker", broker)
    graph.add_node("devops", devops)
    graph.add_node("bankruptcy", bankruptcy_node)
    
    # Flujo general: Start -> Operative -> Evaluator -> Router -> (Broker/DevOps/Bankruptcy)
    graph.add_edge(START, "operative")
    graph.add_edge("operative", "evaluator")
    
    # Enrutamiento basado en billetera y performance post-evaluador
    graph.add_conditional_edges(
        "evaluator",
        router_broker_or_devops,
        {
            "bancarrota": "bankruptcy",
            "devops": "devops",
            "broker": "broker"
        }
    )
    
    # La bancarrota conduce al final del ciclo de vida del agente
    graph.add_edge("bankruptcy", END)
    
    # DevOps redirige siempre al broker para actualizar mercado antes de seguir
    graph.add_edge("devops", "broker")
    
    # El broker decide si hacer la siguiente tarea o terminar la simulación
    graph.add_conditional_edges(
        "broker",
        router_continue,
        {
            "siguiente_tarea": "operative",
            "fin": END
        }
    )
    
    return graph.compile()
