from core.state import AgenticState
from core.market import AutomatedMarketMaker
from graph.builder import build_aem_graph
from db.session import init_db, SessionLocal

def main():
    print("🚀 Iniciando Simulación AEM (Agentic Economic Market) con Ledger...")
    print("-" * 50)
    
    # 0. Inicializar Base de Datos (SQLAlchemy)
    print("📦 Inicializando base de datos SQLite...")
    init_db()

    # 1. Eliminar Global State e instanciar controladamente
    amm = AutomatedMarketMaker(
        base_prices={"GPT-3.5": 0.5, "GPT-4o": 5.0, "Refactor_DevOps_Resource": 15.0},
        capacities={"GPT-3.5": 100.0, "GPT-4o": 10.0, "Refactor_DevOps_Resource": 2.0}
    )

    # 2. Estado Inicial de prueba
    initial_state = AgenticState(
        agent_id="Agent_007",
        agent_wallet=35.0, # Fondos iniciales moderados
        skill_level=3.0,
        complexity=5.0, # Tarea relativamente compleja inicial
        current_task={"type": "presupuesto_concierge", "data": "Extraer variables financieras"},
        metrics={},
        market_ticker=amm.base_prices.copy(),
        history=["Inicio: Agente instanciado en el mercado."]
    )

    # 3. Construir grafo con Inyección de Dependencia (AMM + BD)
    app = build_aem_graph(amm, SessionLocal)
    
    # 4. Ejecutar la Simulación
    final_state = app.invoke(initial_state)
    
    # 5. Imprimir Resultados
    print("\n📈 Historial de Transacciones y Tareas:")
    for h in final_state["history"]:
        print(f" -> {h}")
        
    print("-" * 50)
    print("\n🏦 Estado Final:")
    print(f"Wallet: {final_state['agent_wallet']:.2f} Tk")
    print(f"Skill Final: {final_state['skill_level']:.2f}")
    print(f"Complexity Restante: {final_state['complexity']:.2f}")
    print(f"Precios Finales AMM:")
    for res, price in final_state['market_ticker'].items():
        print(f" - {res}: {price:.4f}")

    print("\n💾 Los registros han sido auditados en 'aem_ledger.db'.")


if __name__ == "__main__":
    main()
