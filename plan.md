# Adaptive Batch Processing System - Implementation Prompt

## System Overview

You are implementing an intelligent batch processing system that dynamically allocates audio processing jobs between GPU and CPU based on:
1. Available VRAM capacity (auto-detected)
2. User-defined CPU parallelization limits
3. Learning from past job performance
4. Smart job sorting and allocation strategies

I already have a "--batchmode" argument made and in use, so we can conjoin it with that.

---

## Core Requirements

### 1. Hardware Detection & Capacity Calculation

**GPU Capacity (Automatic Detection):**
```python
def detect_gpu_capacity(model_size_gb=4.0, fallback_reserved_mb=500):
    """
    Auto-detect maximum GPU batch capacity
    
    Args:
        model_size_gb: Size of model per job in GB (default: 4.0)
        fallback_reserved_mb: Fallback OS reserved memory if detection fails (default: 500)
    
    Returns:
        int: Maximum number of concurrent GPU jobs
    """
    total_vram_gb = get_total_vram()  # e.g., 12 GB
    
    # Try to detect OS reserved memory
    try:
        reserved_gb = get_os_reserved_vram()  # e.g., 0.195 GB
    except:
        reserved_gb = fallback_reserved_mb / 1024  # Use fallback (0.5 GB)
    
    available_vram_gb = total_vram_gb - reserved_gb
    max_gpu_batches = floor(available_vram_gb / model_size_gb)
    
    return max(1, max_gpu_batches)  # At least 1 GPU job
```

**CPU Capacity (User-Defined with Smart Defaults):**
```python
def suggest_cpu_capacity():
    """
    Suggest CPU batch capacity based on system resources
    
    Returns:
        int: Suggested number of concurrent CPU jobs
    """
    available_ram_gb = get_system_ram()
    cpu_cores = get_cpu_count()
    
    # Smart defaults based on available RAM
    if available_ram_gb < 16:
        return 1  # Conservative for low RAM
    elif available_ram_gb < 32:
        return 2  # Moderate for medium RAM
    else:
        return 3  # Balanced for high RAM
```

---

### 2. Performance Learning System

**Track Job Performance:**
```python
class PerformanceTracker:
    def __init__(self):
        self.gpu_jobs = []  # List of (audio_length, processing_time)
        self.cpu_jobs = []  # List of (audio_length, processing_time)
    
    def record_job(self, audio_length_sec, processing_time_sec, device_type):
        """Record completed job for learning"""
        if device_type == "gpu":
            self.gpu_jobs.append((audio_length_sec, processing_time_sec))
        else:
            self.cpu_jobs.append((audio_length_sec, processing_time_sec))
    
    def predict_processing_time(self, audio_length_sec, device_type):
        """
        Predict processing time based on historical data
        
        Args:
            audio_length_sec: Length of audio segment in seconds
            device_type: "gpu" or "cpu"
        
        Returns:
            float: Predicted processing time in seconds
        """
        jobs = self.gpu_jobs if device_type == "gpu" else self.cpu_jobs
        
        if len(jobs) < 3:
            # Not enough data, use rough estimates
            if device_type == "gpu":
                return audio_length_sec * 2.0  # Rough estimate: 2x audio length
            else:
                return audio_length_sec * 24.0  # Rough estimate: 24x audio length (12x slower than GPU)
        
        # Use linear regression or simple ratio from historical data
        avg_ratio = sum(time / length for length, time in jobs) / len(jobs)
        return audio_length_sec * avg_ratio
```

---

### 3. Smart Job Sorting & Allocation

**Job Sorting Strategy:**
```python
def sort_jobs_for_allocation(segments, performance_tracker):
    """
    Sort segments by predicted processing time
    Strategy: Longest jobs to GPU, shortest jobs to CPU
    
    Args:
        segments: List of audio segments with metadata
        performance_tracker: PerformanceTracker instance
    
    Returns:
        list: Sorted segments with predicted times
    """
    enriched_segments = []
    
    for segment in segments:
        gpu_time = performance_tracker.predict_processing_time(
            segment.duration_sec, "gpu"
        )
        cpu_time = performance_tracker.predict_processing_time(
            segment.duration_sec, "cpu"
        )
        
        enriched_segments.append({
            "segment": segment,
            "duration": segment.duration_sec,
            "predicted_gpu_time": gpu_time,
            "predicted_cpu_time": cpu_time,
            "gpu_benefit": cpu_time - gpu_time  # How much faster on GPU
        })
    
    # Sort by GPU benefit (descending) - jobs that benefit most from GPU go first
    return sorted(enriched_segments, key=lambda x: x["gpu_benefit"], reverse=True)
```

**Dynamic Job Allocation:**
```python
class JobScheduler:
    def __init__(self, max_gpu_slots, max_cpu_slots, max_cpu_time_sec=300, stop_cpu_at_progress=0.8):
        self.max_gpu_slots = max_gpu_slots
        self.max_cpu_slots = max_cpu_slots
        self.max_cpu_time_sec = max_cpu_time_sec  # 5 minutes default
        self.stop_cpu_at_progress = stop_cpu_at_progress  # 80% default
        
        self.gpu_slots = []  # Currently running GPU jobs
        self.cpu_slots = []  # Currently running CPU jobs
        self.queue = []      # Waiting jobs
        self.completed = []  # Completed jobs
    
    def allocate_job(self, job, performance_tracker, total_jobs):
        """
        Decide where to allocate a job: GPU or CPU
        
        Args:
            job: Job to allocate
            performance_tracker: PerformanceTracker instance
            total_jobs: Total number of jobs for progress calculation
        
        Returns:
            str: "gpu", "cpu", or "wait"
        """
        progress = len(self.completed) / total_jobs
        
        # Near completion? Stop using CPU
        if progress >= self.stop_cpu_at_progress:
            if len(self.gpu_slots) < self.max_gpu_slots:
                return "gpu"
            else:
                return "wait"  # Wait for GPU slot
        
        # Check if CPU time would exceed max limit
        predicted_cpu_time = performance_tracker.predict_processing_time(
            job.duration_sec, "cpu"
        )
        
        # Priority 1: Fill GPU slots with long jobs
        if len(self.gpu_slots) < self.max_gpu_slots:
            return "gpu"
        
        # Priority 2: Use CPU for short jobs (if within time limit)
        if len(self.cpu_slots) < self.max_cpu_slots:
            if predicted_cpu_time <= self.max_cpu_time_sec:
                return "cpu"
            else:
                return "wait"  # Job too long for CPU, wait for GPU
        
        # All slots full
        return "wait"
    
    def process_batch(self, segments, performance_tracker):
        """
        Main processing loop - allocate and manage jobs
        """
        sorted_jobs = sort_jobs_for_allocation(segments, performance_tracker)
        self.queue = sorted_jobs
        total_jobs = len(sorted_jobs)
        
        while self.queue or self.gpu_slots or self.cpu_slots:
            # Try to allocate waiting jobs
            while self.queue:
                job = self.queue[0]
                allocation = self.allocate_job(job, performance_tracker, total_jobs)
                
                if allocation == "gpu":
                    self.queue.pop(0)
                    self.start_job_on_gpu(job)
                elif allocation == "cpu":
                    self.queue.pop(0)
                    self.start_job_on_cpu(job)
                else:  # wait
                    break
            
            # Check for completed jobs
            self.check_completed_jobs(performance_tracker)
            
            # Small sleep to prevent busy waiting
            time.sleep(0.1)
```

---

### 4. User Configuration Interface

**Configuration Parameters:**
```python
class BatchConfig:
    def __init__(self):
        # Auto-detected
        self.max_gpu_batches = detect_gpu_capacity()
        
        # User-configurable
        self.max_cpu_batches = suggest_cpu_capacity()  # Default suggestion
        self.max_cpu_time_per_job = 300  # 5 minutes in seconds
        self.stop_cpu_at_progress = 0.8  # Stop CPU at 80% completion
        self.model_size_gb = 4.0
        self.fallback_reserved_mb = 500
    
    def update_from_user(self, cpu_batches=None, max_cpu_time=None, stop_cpu_at=None):
        """Update configuration with user preferences"""
        if cpu_batches is not None:
            self.max_cpu_batches = cpu_batches
        if max_cpu_time is not None:
            self.max_cpu_time_per_job = max_cpu_time
        if stop_cpu_at is not None:
            self.stop_cpu_at_progress = stop_cpu_at
    
    def display_config(self):
        """Display current configuration"""
        return f"""
        Batch Processing Configuration:
        ═══════════════════════════════
        GPU Batches (Auto): {self.max_gpu_batches}
        CPU Batches (User): {self.max_cpu_batches}
        Total Concurrent: {self.max_gpu_batches + self.max_cpu_batches}
        
        Max CPU Time: {self.max_cpu_time_per_job}s ({self.max_cpu_time_per_job/60:.1f} min)
        Stop CPU At: {self.stop_cpu_at_progress*100:.0f}% completion
        """
```

---

### 5. Optimization Suggestions

**Dynamic Suggestion System:**
```python
class OptimizationSuggester:
    def __init__(self, config, performance_tracker):
        self.config = config
        self.performance_tracker = performance_tracker
    
    def analyze_and_suggest(self):
        """
        Analyze performance and suggest optimizations
        
        Returns:
            dict: Suggestions with reasoning
        """
        suggestions = []
        
        # Check if CPU jobs are finishing quickly
        if len(self.performance_tracker.cpu_jobs) >= 5:
            avg_cpu_time = sum(t for _, t in self.performance_tracker.cpu_jobs[-5:]) / 5
            
            if avg_cpu_time < 60:  # Less than 1 minute average
                suggestions.append({
                    "type": "increase_cpu_batches",
                    "current": self.config.max_cpu_batches,
                    "suggested": self.config.max_cpu_batches + 1,
                    "reason": "CPU jobs finishing quickly, can handle more",
                    "estimated_time_saved": "~1-2 minutes"
                })
        
        # Check if jobs are frequently waiting
        # (Implementation depends on your job queue monitoring)
        
        return suggestions
```

---

### 6. Safety & Edge Cases

**Important Considerations:**

1. **Segment Splitting for Long Jobs:**
```python
def handle_long_cpu_job(segment, max_cpu_time, performance_tracker):
    """
    If a segment would take too long on CPU, reduce it or wait for GPU
    
    Args:
        segment: Audio segment
        max_cpu_time: Maximum allowed CPU processing time
        performance_tracker: PerformanceTracker instance
    
    Returns:
        str: "wait_for_gpu" or "reduce_and_process"
    """
    predicted_time = performance_tracker.predict_processing_time(
        segment.duration_sec, "cpu"
    )
    
    if predicted_time > max_cpu_time:
        # Option 1: Wait for GPU slot
        # Option 2: Reduce segment by 10% and retry
        reduction_factor = 0.9
        reduced_duration = segment.duration_sec * reduction_factor
        
        new_predicted = performance_tracker.predict_processing_time(
            reduced_duration, "cpu"
        )
        
        if new_predicted <= max_cpu_time:
            return "reduce_and_process"
        else:
            return "wait_for_gpu"
    
    return "process_normally"
```

2. **Endgame Strategy (80% Rule):**
```python
def should_use_cpu(progress_percent, config):
    """
    Decide if CPU should still be used based on progress
    
    Args:
        progress_percent: Current completion progress (0-1)
        config: BatchConfig instance
    
    Returns:
        bool: True if CPU can be used
    """
    return progress_percent < config.stop_cpu_at_progress
```

3. **Error Handling:**
```python
def handle_job_failure(job, device_type, retry_count=0, max_retries=3):
    """
    Handle failed jobs with retry logic
    
    Args:
        job: Failed job
        device_type: Where it failed ("gpu" or "cpu")
        retry_count: Current retry attempt
        max_retries: Maximum retry attempts
    
    Returns:
        str: "retry_same", "retry_other", or "skip"
    """
    if retry_count >= max_retries:
        return "skip"  # Give up after 3 attempts
    
    if device_type == "gpu":
        return "retry_cpu"  # Try CPU if GPU failed
    else:
        return "retry_same"  # Retry CPU
```

---

## Implementation Checklist

- [ ] Implement GPU VRAM detection with fallback
- [ ] Implement CPU capacity detection and user override
- [ ] Create PerformanceTracker class for learning
- [ ] Implement job sorting algorithm
- [ ] Create JobScheduler for dynamic allocation
- [ ] Add user configuration interface
- [ ] Implement 80% endgame strategy (stop CPU)
- [ ] Add max CPU time limits per job
- [ ] Create optimization suggestion system
- [ ] Add error handling and retry logic
- [ ] Implement progress tracking and reporting
- [ ] Add logging for debugging and monitoring

---

## Usage Example

```python
# Initialize system
config = BatchConfig()
config.update_from_user(cpu_batches=3, max_cpu_time=300)

tracker = PerformanceTracker()
scheduler = JobScheduler(
    max_gpu_slots=config.max_gpu_batches,
    max_cpu_slots=config.max_cpu_batches,
    max_cpu_time_sec=config.max_cpu_time_per_job,
    stop_cpu_at_progress=config.stop_cpu_at_progress
)

# Process segments
segments = load_audio_segments()  # Your segment loading logic
scheduler.process_batch(segments, tracker)

# Get optimization suggestions
suggester = OptimizationSuggester(config, tracker)
suggestions = suggester.analyze_and_suggest()
print(suggestions)
```

---

## Expected Behavior

1. **First Batch (Learning Phase):**
   - Process 2-4 segments to learn performance characteristics
   - Track GPU and CPU processing times
   - Build prediction model

2. **Subsequent Batches (Optimized Phase):**
   - Sort jobs by GPU benefit
   - Allocate longest jobs to GPU
   - Allocate shortest jobs to CPU
   - Fill all available slots (2 GPU + 3 CPU in example)

3. **Endgame (80%+ Progress):**
   - Stop allocating new jobs to CPU
   - Process remaining jobs on GPU only
   - Ensures predictable finish time

4. **Continuous Learning:**
   - Update predictions after each job
   - Suggest configuration improvements
   - Adapt to actual system performance

---

## Performance Metrics to Track

- Average GPU job time
- Average CPU job time
- CPU/GPU speed ratio
- GPU utilization %
- CPU utilization %
- Total processing time
- Queue wait times
- Failed jobs and retries

---

## Notes

- The system learns over time, so first batch may not be optimal
- User can override all CPU-related settings
- GPU capacity is auto-detected but can be manually overridden if needed
- Safety limits prevent system overload
- Endgame strategy prevents last-minute slowdowns