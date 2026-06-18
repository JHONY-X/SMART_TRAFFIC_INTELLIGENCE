class SyncController:
    """
    Advanced: Synchronization Module
    Coordinates multiple intersections for a Green wave system.
    """
    def __init__(self, intersections):
        self.intersections = intersections

    def sync_green_wave(self, primary_direction):
        """
        Forces consecutive lights to turn green for the primary direction.
        """
        # This is a basic implementation for the "green wave" concept.
        # In a real system, time offsets based on distance would be calculated.
        sync_actions = []
        for intersection in self.intersections:
            sync_actions.append({
                "intersection_id": intersection.id,
                "target_lane": primary_direction
            })
        return sync_actions
