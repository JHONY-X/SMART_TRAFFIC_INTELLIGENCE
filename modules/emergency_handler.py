class EmergencyHandler:
    @staticmethod
    def check_emergencies(analysis_data):
        """
        Returns a list of lanes that have emergencies.
        """
        emergencies = []
        for int_id, lanes in analysis_data.items():
            for lane_name, metrics in lanes.items():
                if metrics.get('has_emergency', False):
                    emergencies.append((int_id, lane_name))
        return emergencies
