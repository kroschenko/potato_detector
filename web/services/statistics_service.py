from datetime import datetime


class StatisticsService:
    def __init__(self):
        self.start_time = datetime.now()
        self.total_potatoes_detected = 0
        self.prev_total_objects_count = 0

    def update_counts(self, current_objects_total_count: int) -> None:
        if current_objects_total_count > self.prev_total_objects_count:
            self.total_potatoes_detected += 1
            self.prev_total_objects_count = current_objects_total_count

    def build_statistics(self, total_defects_detected: int) -> dict:
        elapsed_time_minutes = (datetime.now() - self.start_time).total_seconds() / 60
        potatoes_per_minute = self.total_potatoes_detected / elapsed_time_minutes if elapsed_time_minutes > 0 else 0
        defect_rate_percent = (total_defects_detected / self.total_potatoes_detected * 100) if self.total_potatoes_detected > 0 else 0
        return {
            'total_potatoes': self.total_potatoes_detected,
            'defected_potatoes': total_defects_detected,
            'defect_rate': round(defect_rate_percent, 2),
            'potatoes_per_minute': round(potatoes_per_minute, 2),
            'elapsed_time': round(elapsed_time_minutes, 2),
        }


