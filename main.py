from scripts import load_data, preprocess, analysis, visualization, mapping

def main():
    data = load_data.load_all()
    clean = preprocess.clean_and_merge(data)
    indicators = analysis.compute_indicators(clean)
    visualization.generate_all(indicators)
    mapping.create_interactive_map(indicators)


