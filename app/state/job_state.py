import time
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from app.domain.enums import AnalysisStatus


@dataclass
class JobState:
    """
    Holds runtime state, log history, and progress tracking for an active analysis job.
    """
    analysis_id: str
    product_url: str
    user_id: Optional[str] = None
    status: str = AnalysisStatus.PENDING.value
    current_step: str = "Initializing analysis..."
    current_page: int = 1
    total_pages: int = 1
    reviews_collected: int = 0
    progress_percent: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    stop_requested: bool = False
    log_entries: List[str] = field(default_factory=list)
    product_preview: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def add_log(self, category: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{category.upper()}] {message}"
        self.log_entries.append(log_line)

    def get_elapsed_time_str(self) -> str:
        if self.status in (AnalysisStatus.COMPLETED.value, AnalysisStatus.FAILED.value) and self.end_time is None:
            self.end_time = time.time()

        current = self.end_time if self.end_time is not None else time.time()
        elapsed_seconds = max(0, int(current - self.start_time))
        minutes, seconds = divmod(elapsed_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class JobStateManager:
    """
    Central manager storing active analysis jobs in runtime memory with thread locks and TTL cleanup.
    """
    def __init__(self):
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create_job(self, product_url: str, user_id: Optional[str] = None) -> JobState:
        analysis_id = f"anl_{uuid.uuid4().hex[:12]}"
        job = JobState(analysis_id=analysis_id, product_url=product_url, user_id=user_id)
        job.add_log("SYSTEM", f"Created analysis job [{analysis_id}] for URL: {product_url} (User: {user_id or 'Anonymous'})")
        with self._lock:
            self._jobs[analysis_id] = job
        return job

    def get_job(self, analysis_id: str, user_id: Optional[str] = None) -> Optional[JobState]:
        with self._lock:
            job = self._jobs.get(analysis_id)
            if job and user_id is not None and job.user_id and job.user_id != str(user_id):
                return None
            return job

    def request_stop(self, analysis_id: str, user_id: Optional[str] = None) -> bool:
        job = self.get_job(analysis_id, user_id=user_id)
        if job:
            job.stop_requested = True
            job.add_log("USER", "Finish Scraping signal requested by user ('Q' key equivalent).")
            if job.status == "SCRAPING":
                job.current_step = "Finish Scraping requested. Finishing current page..."
            return True
        return False

    def cleanup_expired_jobs(self, ttl_seconds: int = 3600, max_jobs: int = 100):
        """
        Prunes completed or failed jobs older than ttl_seconds or enforces max_jobs limit.
        """
        now = time.time()
        with self._lock:
            if len(self._jobs) <= max_jobs:
                return

            to_remove = []
            for job_id, job in self._jobs.items():
                if job.status in (AnalysisStatus.COMPLETED.value, AnalysisStatus.FAILED.value):
                    job_end = job.end_time or now
                    if (now - job_end) > ttl_seconds:
                        to_remove.append(job_id)

            for jid in to_remove:
                self._jobs.pop(jid, None)

            if len(self._jobs) > max_jobs:
                sorted_jobs = sorted(
                    [j for j in self._jobs.values() if j.status in (AnalysisStatus.COMPLETED.value, AnalysisStatus.FAILED.value)],
                    key=lambda j: j.start_time
                )
                excess = len(self._jobs) - max_jobs
                for j in sorted_jobs[:excess]:
                    self._jobs.pop(j.analysis_id, None)


job_state_manager = JobStateManager()
