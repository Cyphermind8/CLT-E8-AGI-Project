import networkx as nx
import matplotlib.pyplot as plt

# Create a directed graph
G = nx.DiGraph()

# Define files (nodes)
files = [
    "ai_core.py", "api.py", "ai_memory.py", "ai_performance_log.json",
    "ai_recursive_intelligence.py", "ai_benchmarking.py", "ai_knowledge_expansion.py", "ai_self_monitoring.py",
    "ai_benchmark_results.json", "ai_continuous_evolution.py", "ai_self_modification.py", "ai_strategy.py",
    "ai_optimization.py", "ai_sandbox.py", "ai_self_debugging.py", "ai_intelligence_fusion.py",
    "ai_philosophical_reasoning.py", "ai_creative_innovation.py", "ai_scientific_discovery.py",
    "ai_quantum_cognition.py", "ai_reality_modeling.py", "ai_meta_learning.py", "ai_ethical_reasoning.py",
    "ai_multi_agent_collab.py", "ai_autonomous_engineering.py", "ai_neurosymbolic_engine.py",
    "ai_self_reflection.py", "ai_generalization.py", "ai_memory.json", "ai_knowledge_base.json",
    "ai_execution_manager.py", "ai_system_diagnostics.py", "ai_event_logger.py", "ai_security.py", "debug_mode.py"
]

G.add_nodes_from(files)

# Define file connections (edges)
connections = [
    ("ai_core.py", "api.py"), ("ai_core.py", "ai_memory.py"), ("ai_core.py", "ai_recursive_intelligence.py"),
    ("ai_core.py", "ai_continuous_evolution.py"), ("api.py", "ai_core.py"), ("ai_memory.py", "ai_memory.json"),
    ("ai_memory.py", "ai_performance_log.json"), ("ai_recursive_intelligence.py", "ai_memory.py"),
    ("ai_recursive_intelligence.py", "ai_benchmarking.py"), ("ai_benchmarking.py", "ai_benchmark_results.json"),
    ("ai_knowledge_expansion.py", "ai_memory.py"), ("ai_self_monitoring.py", "ai_benchmarking.py"),
    ("ai_continuous_evolution.py", "ai_core.py"), ("ai_continuous_evolution.py", "ai_self_modification.py"),
    ("ai_self_modification.py", "ai_core.py"), ("ai_strategy.py", "ai_self_modification.py"),
    ("ai_optimization.py", "ai_self_modification.py"), ("ai_sandbox.py", "ai_self_modification.py"),
    ("ai_self_debugging.py", "ai_self_modification.py"), ("ai_intelligence_fusion.py", "ai_core.py"),
    ("ai_intelligence_fusion.py", "ai_recursive_intelligence.py"), ("ai_philosophical_reasoning.py", "ai_intelligence_fusion.py"),
    ("ai_creative_innovation.py", "ai_intelligence_fusion.py"), ("ai_scientific_discovery.py", "ai_intelligence_fusion.py"),
    ("ai_quantum_cognition.py", "ai_intelligence_fusion.py"), ("ai_reality_modeling.py", "ai_intelligence_fusion.py"),
    ("ai_meta_learning.py", "ai_intelligence_fusion.py"), ("ai_ethical_reasoning.py", "ai_intelligence_fusion.py"),
    ("ai_multi_agent_collab.py", "ai_intelligence_fusion.py"), ("ai_autonomous_engineering.py", "ai_multi_agent_collab.py"),
    ("ai_neurosymbolic_engine.py", "ai_meta_learning.py"), ("ai_self_reflection.py", "ai_meta_learning.py"),
    ("ai_generalization.py", "ai_meta_learning.py"), ("ai_execution_manager.py", "ai_self_modification.py"),
    ("ai_system_diagnostics.py", "ai_core.py"), ("ai_event_logger.py", "ai_core.py"), ("ai_security.py", "ai_core.py"),
    ("debug_mode.py", "ai_core.py")
]

G.add_edges_from(connections)

# Generate positions for visualization
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42, k=0.3)  # Adjust for better spacing

# Draw graph
nx.draw(G, pos, with_labels=True, node_size=2500, node_color="lightblue",
        edge_color="gray", font_size=8, font_weight="bold", arrows=True)

# Save as SVG and PDF
plt.title("AI System Architecture - File Interconnections", fontsize=12)
plt.savefig("ai_system_architecture.svg", format="svg")
plt.savefig("ai_system_architecture.pdf", format="pdf")
plt.show()

print("✅ AI System Architecture Graph saved as 'ai_system_architecture.svg' and 'ai_system_architecture.pdf'.")
