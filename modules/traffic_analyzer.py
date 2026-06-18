from utils.constants import Constants

class TrafficAnalyzer:
    @staticmethod
    def classify_density(density):
        """
        density = cars / lane_capacity
        Classifies as Low, Medium, High.
        Here density is a float between 0 and 1.
        """
        # Convert back to absolute numbers for thresholds if preferred, 
        # or use percentage thresholds. Let's use percentage.
        if density <= 0.2:
            return Constants.TRAFFIC_LOW
        elif density <= 0.6:
            return Constants.TRAFFIC_MEDIUM
        else:
            return Constants.TRAFFIC_HIGH

    @staticmethod
    def analyze(traffic_data):
        """
        Analyzes the clean data.
        """
        analysis = {}
        for int_id, lanes in traffic_data.items():
            analysis[int_id] = {}
            for lane_name, metrics in lanes.items():
                classification = TrafficAnalyzer.classify_density(metrics['density'])
                analysis[int_id][lane_name] = {
                    **metrics,
                    "classification": classification
                }
        return analysis
