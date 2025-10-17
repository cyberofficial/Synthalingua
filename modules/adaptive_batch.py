"""
Adaptive Batch Processing Module

This module implements an intelligent batch processing system that dynamically allocates
audio processing jobs between GPU and CPU based on:
1. Available VRAM capacity (auto-detected)
2. User-defined CPU parallelization limits
3. Learning from past job performance
4. Smart job sorting and allocation strategies

Key Features:
- Automatic GPU VRAM detection and capacity calculation
- User-configurable CPU parallelization with smart defaults
- Performance tracking and prediction for optimal job allocation
- Dynamic job scheduling with GPU/CPU slot management
- Endgame strategy (80% rule) to prevent last-minute slowdowns
- Optimization suggestions based on runtime analysis
"""

import logging
import time
import psutil
import torch
import concurrent.futures
from math import floor
from typing import Dict, List, Tuple, Optional, Any, Callable
from colorama import Fore, Style

logger = logging.getLogger(__name__)


def detect_gpu_capacity(model_size_gb: float = 4.0, fallback_reserved_mb: int = 500) -> int:
    """
    Auto-detect maximum GPU batch capacity based on available VRAM.
    
    Args:
        model_size_gb: Size of model per job in GB (default: 4.0)
        fallback_reserved_mb: Fallback OS reserved memory if detection fails (default: 500)
    
    Returns:
        int: Maximum number of concurrent GPU jobs
    """
    if not torch.cuda.is_available():
        logger.info("CUDA not available, GPU batch capacity is 0")
        return 0
    
    try:
        # Get total VRAM in bytes
        total_vram_bytes = torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory
        total_vram_gb = total_vram_bytes / (1024 ** 3)
        
        # Try to get currently allocated memory to estimate OS reserved
        try:
            allocated_bytes = torch.cuda.memory_allocated(torch.cuda.current_device())
            reserved_bytes = torch.cuda.memory_reserved(torch.cuda.current_device())
            # OS reserved is the difference between what's reserved and what we know about
            os_reserved_gb = (reserved_bytes - allocated_bytes) / (1024 ** 3)
            
            # If estimation seems unreasonable, use fallback
            if os_reserved_gb < 0 or os_reserved_gb > 2.0:
                os_reserved_gb = fallback_reserved_mb / 1024
        except Exception:
            os_reserved_gb = fallback_reserved_mb / 1024
        
        available_vram_gb = total_vram_gb - os_reserved_gb
        max_gpu_batches = floor(available_vram_gb / model_size_gb)
        
        logger.info(f"GPU VRAM Detection: Total={total_vram_gb:.2f}GB, Reserved={os_reserved_gb:.2f}GB, "
                   f"Available={available_vram_gb:.2f}GB, Max Batches={max_gpu_batches}")
        
        return max(1, max_gpu_batches)  # At least 1 GPU job if CUDA is available
    
    except Exception as e:
        logger.error(f"Error detecting GPU capacity: {e}")
        return 0


def get_system_ram_gb() -> float:
    """
    Get total available system RAM in GB.
    
    Returns:
        float: Total RAM in GB
    """
    try:
        ram_bytes = psutil.virtual_memory().total
        ram_gb = ram_bytes / (1024 ** 3)
        return ram_gb
    except Exception as e:
        logger.error(f"Error detecting system RAM: {e}")
        return 16.0  # Safe fallback


def get_cpu_count() -> int:
    """
    Get number of CPU cores.
    
    Returns:
        int: Number of CPU cores
    """
    try:
        return psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 4
    except Exception:
        return 4  # Safe fallback


def suggest_cpu_capacity() -> int:
    """
    Suggest CPU batch capacity based on system resources.
    
    Returns:
        int: Suggested number of concurrent CPU jobs
    """
    available_ram_gb = get_system_ram_gb()
    
    # Smart defaults based on available RAM
    if available_ram_gb < 16:
        return 1  # Conservative for low RAM
    elif available_ram_gb < 32:
        return 2  # Moderate for medium RAM
    else:
        return 3  # Balanced for high RAM


class PerformanceTracker:
    """
    Tracks and predicts job performance based on historical data.
    
    This class maintains records of completed jobs and uses them to predict
    processing times for future jobs, enabling optimal job allocation.
    """
    
    def __init__(self):
        """Initialize performance tracker with empty job lists."""
        self.gpu_jobs: List[Tuple[float, float]] = []  # (audio_length, processing_time)
        self.cpu_jobs: List[Tuple[float, float]] = []  # (audio_length, processing_time)
    
    def record_job(self, audio_length_sec: float, processing_time_sec: float, device_type: str):
        """
        Record a completed job for learning.
        
        Args:
            audio_length_sec: Length of audio segment in seconds
            processing_time_sec: Time taken to process in seconds
            device_type: "gpu" or "cpu"
        """
        if device_type.lower() == "gpu":
            self.gpu_jobs.append((audio_length_sec, processing_time_sec))
            logger.debug(f"Recorded GPU job: {audio_length_sec}s audio took {processing_time_sec:.2f}s")
        else:
            self.cpu_jobs.append((audio_length_sec, processing_time_sec))
            logger.debug(f"Recorded CPU job: {audio_length_sec}s audio took {processing_time_sec:.2f}s")
    
    def predict_processing_time(self, audio_length_sec: float, device_type: str) -> float:
        """
        Predict processing time based on historical data.
        
        Args:
            audio_length_sec: Length of audio segment in seconds
            device_type: "gpu" or "cpu"
        
        Returns:
            float: Predicted processing time in seconds
        """
        jobs = self.gpu_jobs if device_type.lower() == "gpu" else self.cpu_jobs
        
        if len(jobs) < 3:
            # Not enough data, use rough estimates
            if device_type.lower() == "gpu":
                return audio_length_sec * 2.0  # Rough estimate: 2x audio length
            else:
                return audio_length_sec * 24.0  # Rough estimate: 24x audio length (12x slower than GPU)
        
        # Use average ratio from historical data
        avg_ratio = sum(time / length for length, time in jobs if length > 0) / len(jobs)
        predicted = audio_length_sec * avg_ratio
        
        logger.debug(f"Predicted {device_type} time for {audio_length_sec}s: {predicted:.2f}s (ratio: {avg_ratio:.2f})")
        return predicted
    
    def get_speed_ratio(self) -> float:
        """
        Get the CPU/GPU speed ratio.
        
        Returns:
            float: How many times slower CPU is compared to GPU
        """
        if len(self.gpu_jobs) < 2 or len(self.cpu_jobs) < 2:
            return 12.0  # Default estimate
        
        gpu_avg_ratio = sum(time / length for length, time in self.gpu_jobs if length > 0) / len(self.gpu_jobs)
        cpu_avg_ratio = sum(time / length for length, time in self.cpu_jobs if length > 0) / len(self.cpu_jobs)
        
        if gpu_avg_ratio > 0:
            return cpu_avg_ratio / gpu_avg_ratio
        return 12.0


def sort_jobs_for_allocation(segments: List[Dict[str, Any]], performance_tracker: PerformanceTracker) -> List[Dict[str, Any]]:
    """
    Sort segments by predicted processing time for optimal allocation.
    Strategy: Longest jobs to GPU, shortest jobs to CPU
    
    Args:
        segments: List of audio segments with metadata
        performance_tracker: PerformanceTracker instance
    
    Returns:
        list: Sorted segments with predicted times
    """
    enriched_segments = []
    
    for segment in segments:
        duration = segment.get('duration_sec', segment.get('end', 0) - segment.get('start', 0))
        
        gpu_time = performance_tracker.predict_processing_time(duration, "gpu")
        cpu_time = performance_tracker.predict_processing_time(duration, "cpu")
        
        enriched_segments.append({
            "segment": segment,
            "duration": duration,
            "predicted_gpu_time": gpu_time,
            "predicted_cpu_time": cpu_time,
            "gpu_benefit": cpu_time - gpu_time  # How much faster on GPU
        })
    
    # Sort by GPU benefit (descending) - jobs that benefit most from GPU go first
    sorted_segments = sorted(enriched_segments, key=lambda x: x["gpu_benefit"], reverse=True)
    
    logger.info(f"Sorted {len(segments)} jobs by GPU benefit (longest first)")
    return sorted_segments


class JobScheduler:
    """
    Manages dynamic job allocation between GPU and CPU with intelligent scheduling.
    
    This class handles job queuing, allocation decisions, and execution tracking
    with support for the 80% endgame strategy and max CPU time limits.
    """
    
    def __init__(self, max_gpu_slots: int, max_cpu_slots: int, 
                 max_cpu_time_sec: int = 300, stop_cpu_at_progress: float = 0.8):
        """
        Initialize job scheduler.
        
        Args:
            max_gpu_slots: Maximum concurrent GPU jobs
            max_cpu_slots: Maximum concurrent CPU jobs
            max_cpu_time_sec: Maximum time per CPU job in seconds (default: 300)
            stop_cpu_at_progress: Stop using CPU at this progress ratio (default: 0.8)
        """
        self.max_gpu_slots = max_gpu_slots
        self.max_cpu_slots = max_cpu_slots
        self.max_cpu_time_sec = max_cpu_time_sec
        self.stop_cpu_at_progress = stop_cpu_at_progress
        
        self.gpu_futures: Dict[concurrent.futures.Future, Dict] = {}
        self.cpu_futures: Dict[concurrent.futures.Future, Dict] = {}
        self.completed: List[Tuple[int, Any]] = []
        self.total_jobs = 0
        
        logger.info(f"JobScheduler initialized: {max_gpu_slots} GPU slots, {max_cpu_slots} CPU slots, "
                   f"max CPU time: {max_cpu_time_sec}s, stop CPU at: {stop_cpu_at_progress*100:.0f}%")
    
    def allocate_job(self, job: Dict[str, Any], performance_tracker: PerformanceTracker) -> str:
        """
        Decide where to allocate a job: GPU or CPU.
        
        Args:
            job: Job to allocate
            performance_tracker: PerformanceTracker instance
        
        Returns:
            str: "gpu", "cpu", or "wait"
        """
        progress = len(self.completed) / self.total_jobs if self.total_jobs > 0 else 0
        
        # Near completion? Stop using CPU (endgame strategy)
        if progress >= self.stop_cpu_at_progress:
            if len(self.gpu_futures) < self.max_gpu_slots:
                logger.debug(f"Endgame mode: allocating to GPU (progress: {progress*100:.1f}%)")
                return "gpu"
            else:
                logger.debug(f"Endgame mode: waiting for GPU (progress: {progress*100:.1f}%)")
                return "wait"  # Wait for GPU slot
        
        # Check if CPU time would exceed max limit
        predicted_cpu_time = performance_tracker.predict_processing_time(job["duration"], "cpu")
        
        # Priority 1: Fill GPU slots with long jobs
        if len(self.gpu_futures) < self.max_gpu_slots:
            logger.debug(f"Allocating to GPU (slot {len(self.gpu_futures)+1}/{self.max_gpu_slots})")
            return "gpu"
        
        # Priority 2: Use CPU for short jobs (if within time limit)
        if len(self.cpu_futures) < self.max_cpu_slots:
            if predicted_cpu_time <= self.max_cpu_time_sec:
                logger.debug(f"Allocating to CPU (slot {len(self.cpu_futures)+1}/{self.max_cpu_slots}, "
                           f"predicted time: {predicted_cpu_time:.1f}s)")
                return "cpu"
            else:
                logger.debug(f"Job too long for CPU ({predicted_cpu_time:.1f}s > {self.max_cpu_time_sec}s), waiting for GPU")
                return "wait"  # Job too long for CPU, wait for GPU
        
        # All slots full
        logger.debug("All slots full, waiting")
        return "wait"
    
    def process_batch(self, sorted_jobs: List[Dict[str, Any]], performance_tracker: PerformanceTracker,
                     process_function: Callable, *args, **kwargs) -> List[Tuple[int, Any]]:
        """
        Main processing loop - allocate and manage jobs.
        
        Args:
            sorted_jobs: List of sorted jobs with predictions
            performance_tracker: PerformanceTracker instance
            process_function: Function to call for processing each job
            *args, **kwargs: Additional arguments to pass to process_function
        
        Returns:
            List of (index, result) tuples
        """
        self.total_jobs = len(sorted_jobs)
        self.completed = []
        queue = list(enumerate(sorted_jobs, 1))
        
        gpu_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_gpu_slots) if self.max_gpu_slots > 0 else None
        cpu_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_cpu_slots) if self.max_cpu_slots > 0 else None
        
        print(f"{Fore.CYAN} Starting adaptive batch processing: {len(queue)} jobs{Style.RESET_ALL}")
        print(f"{Fore.CYAN} GPU slots: {self.max_gpu_slots}, CPU slots: {self.max_cpu_slots}{Style.RESET_ALL}")
        
        try:
            while queue or self.gpu_futures or self.cpu_futures:
                # Try to allocate waiting jobs
                jobs_allocated = 0
                while queue:
                    job_index, job = queue[0]
                    allocation = self.allocate_job(job, performance_tracker)
                    
                    if allocation == "gpu" and gpu_executor:
                        queue.pop(0)
                        start_time = time.time()
                        future = gpu_executor.submit(process_function, job["segment"], "gpu", *args, **kwargs)
                        self.gpu_futures[future] = {"index": job_index, "job": job, "start_time": start_time}
                        jobs_allocated += 1
                        print(f"{Fore.GREEN}  → GPU slot {len(self.gpu_futures)}: Job {job_index} ({job['duration']:.1f}s audio){Style.RESET_ALL}")
                    
                    elif allocation == "cpu" and cpu_executor:
                        queue.pop(0)
                        start_time = time.time()
                        future = cpu_executor.submit(process_function, job["segment"], "cpu", *args, **kwargs)
                        self.cpu_futures[future] = {"index": job_index, "job": job, "start_time": start_time}
                        jobs_allocated += 1
                        print(f"{Fore.YELLOW}  → CPU slot {len(self.cpu_futures)}: Job {job_index} ({job['duration']:.1f}s audio){Style.RESET_ALL}")
                    
                    else:  # wait
                        break
                
                # Check for completed jobs
                completed_this_round = self._check_completed_jobs(performance_tracker)
                
                if completed_this_round == 0 and jobs_allocated == 0:
                    # Nothing completed and nothing allocated, wait a bit
                    time.sleep(0.1)
            
            print(f"{Fore.GREEN} Adaptive batch processing complete!{Style.RESET_ALL}")
            
        finally:
            if gpu_executor:
                gpu_executor.shutdown(wait=True)
            if cpu_executor:
                cpu_executor.shutdown(wait=True)
        
        # Sort results by index
        self.completed.sort(key=lambda x: x[0])
        return self.completed
    
    def _check_completed_jobs(self, performance_tracker: PerformanceTracker) -> int:
        """
        Check for and process completed jobs.
        
        Args:
            performance_tracker: PerformanceTracker instance
        
        Returns:
            int: Number of jobs completed in this check
        """
        completed_count = 0
        
        # Check GPU jobs
        done_gpu = [f for f in self.gpu_futures if f.done()]
        for future in done_gpu:
            job_info = self.gpu_futures.pop(future)
            processing_time = time.time() - job_info["start_time"]
            
            try:
                result = future.result()
                self.completed.append((job_info["index"], result))
                
                # Record performance
                performance_tracker.record_job(
                    job_info["job"]["duration"],
                    processing_time,
                    "gpu"
                )
                
                print(f"{Fore.GREEN}  ✓ GPU Job {job_info['index']} complete ({processing_time:.1f}s){Style.RESET_ALL}")
                completed_count += 1
            
            except Exception as e:
                logger.error(f"GPU Job {job_info['index']} failed: {e}")
                self.completed.append((job_info["index"], None))
                completed_count += 1
        
        # Check CPU jobs
        done_cpu = [f for f in self.cpu_futures if f.done()]
        for future in done_cpu:
            job_info = self.cpu_futures.pop(future)
            processing_time = time.time() - job_info["start_time"]
            
            try:
                result = future.result()
                self.completed.append((job_info["index"], result))
                
                # Record performance
                performance_tracker.record_job(
                    job_info["job"]["duration"],
                    processing_time,
                    "cpu"
                )
                
                print(f"{Fore.YELLOW}  ✓ CPU Job {job_info['index']} complete ({processing_time:.1f}s){Style.RESET_ALL}")
                completed_count += 1
            
            except Exception as e:
                logger.error(f"CPU Job {job_info['index']} failed: {e}")
                self.completed.append((job_info["index"], None))
                completed_count += 1
        
        return completed_count


class BatchConfig:
    """
    Configuration management for adaptive batch processing.
    
    Handles auto-detection of GPU capacity, user-configurable CPU settings,
    and configuration display.
    """
    
    def __init__(self, model_size_gb: float = 4.0, fallback_reserved_mb: int = 500):
        """
        Initialize batch configuration with defaults.
        
        Args:
            model_size_gb: Model size in GB for VRAM calculation (default: 4.0)
            fallback_reserved_mb: Fallback reserved memory in MB (default: 500)
        """
        # Auto-detected
        self.max_gpu_batches = detect_gpu_capacity(model_size_gb, fallback_reserved_mb)
        
        # User-configurable with smart defaults
        self.max_cpu_batches = suggest_cpu_capacity()
        self.max_cpu_time_per_job = 300  # 5 minutes in seconds
        self.stop_cpu_at_progress = 0.8  # Stop CPU at 80% completion
        self.model_size_gb = model_size_gb
        self.fallback_reserved_mb = fallback_reserved_mb
        
        logger.info(f"BatchConfig initialized: GPU={self.max_gpu_batches}, CPU={self.max_cpu_batches}")
    
    def update_from_user(self, cpu_batches: Optional[int] = None, 
                        max_cpu_time: Optional[int] = None, 
                        stop_cpu_at: Optional[float] = None):
        """
        Update configuration with user preferences.
        
        Args:
            cpu_batches: Number of CPU batch slots
            max_cpu_time: Maximum CPU time per job in seconds
            stop_cpu_at: Progress threshold to stop using CPU (0-1)
        """
        if cpu_batches is not None:
            self.max_cpu_batches = cpu_batches
            logger.info(f"Updated max_cpu_batches to {cpu_batches}")
        
        if max_cpu_time is not None:
            self.max_cpu_time_per_job = max_cpu_time
            logger.info(f"Updated max_cpu_time_per_job to {max_cpu_time}s")
        
        if stop_cpu_at is not None:
            self.stop_cpu_at_progress = stop_cpu_at
            logger.info(f"Updated stop_cpu_at_progress to {stop_cpu_at*100:.0f}%")
    
    def display_config(self) -> str:
        """
        Display current configuration in a formatted string.
        
        Returns:
            str: Formatted configuration display
        """
        config_str = f"""
{Fore.CYAN}╔═══════════════════════════════════════════╗{Style.RESET_ALL}
{Fore.CYAN}║  Adaptive Batch Processing Configuration  ║{Style.RESET_ALL}
{Fore.CYAN}╚═══════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}GPU Batches (Auto):{Style.RESET_ALL} {self.max_gpu_batches}
{Fore.YELLOW}CPU Batches (User):{Style.RESET_ALL} {self.max_cpu_batches}
{Fore.CYAN}Total Concurrent:{Style.RESET_ALL}   {self.max_gpu_batches + self.max_cpu_batches}

{Fore.YELLOW}Max CPU Time:{Style.RESET_ALL}       {self.max_cpu_time_per_job}s ({self.max_cpu_time_per_job/60:.1f} min)
{Fore.YELLOW}Stop CPU At:{Style.RESET_ALL}        {self.stop_cpu_at_progress*100:.0f}% completion
{Fore.GREEN}Model Size:{Style.RESET_ALL}         {self.model_size_gb:.1f}GB per job
"""
        return config_str


class OptimizationSuggester:
    """
    Analyzes performance and suggests optimizations.
    
    Provides intelligent suggestions based on runtime metrics to help users
    optimize their batch processing configuration.
    """
    
    def __init__(self, config: BatchConfig, performance_tracker: PerformanceTracker):
        """
        Initialize optimization suggester.
        
        Args:
            config: Current batch configuration
            performance_tracker: Performance tracker with historical data
        """
        self.config = config
        self.performance_tracker = performance_tracker
    
    def analyze_and_suggest(self) -> List[Dict[str, Any]]:
        """
        Analyze performance and suggest optimizations.
        
        Returns:
            list: List of suggestion dictionaries with reasoning
        """
        suggestions = []
        
        # Check if CPU jobs are finishing quickly
        if len(self.performance_tracker.cpu_jobs) >= 5:
            recent_cpu_jobs = self.performance_tracker.cpu_jobs[-5:]
            avg_cpu_time = sum(time for _, time in recent_cpu_jobs) / len(recent_cpu_jobs)
            
            if avg_cpu_time < 60:  # Less than 1 minute average
                suggestions.append({
                    "type": "increase_cpu_batches",
                    "current": self.config.max_cpu_batches,
                    "suggested": self.config.max_cpu_batches + 1,
                    "reason": "CPU jobs finishing quickly, can handle more parallel work",
                    "estimated_benefit": "~1-2 minutes faster completion"
                })
        
        # Check if CPU is being underutilized
        if len(self.performance_tracker.cpu_jobs) < 3 and len(self.performance_tracker.gpu_jobs) > 10:
            suggestions.append({
                "type": "increase_cpu_batches",
                "current": self.config.max_cpu_batches,
                "suggested": self.config.max_cpu_batches + 1,
                "reason": "CPU slots rarely used, may benefit from more CPU parallelization",
                "estimated_benefit": "Better resource utilization"
            })
        
        # Check CPU/GPU speed ratio
        if len(self.performance_tracker.gpu_jobs) >= 3 and len(self.performance_tracker.cpu_jobs) >= 3:
            speed_ratio = self.performance_tracker.get_speed_ratio()
            
            if speed_ratio < 8:  # CPU is faster than expected
                suggestions.append({
                    "type": "increase_cpu_usage",
                    "current": self.config.max_cpu_time_per_job,
                    "suggested": self.config.max_cpu_time_per_job + 60,
                    "reason": f"CPU performance is good (only {speed_ratio:.1f}x slower than GPU)",
                    "estimated_benefit": "More efficient job distribution"
                })
            elif speed_ratio > 15:  # CPU is much slower
                suggestions.append({
                    "type": "decrease_cpu_usage",
                    "current": self.config.max_cpu_time_per_job,
                    "suggested": max(60, self.config.max_cpu_time_per_job - 60),
                    "reason": f"CPU performance is slow ({speed_ratio:.1f}x slower than GPU)",
                    "estimated_benefit": "Reduce CPU bottlenecks"
                })
        
        logger.info(f"Generated {len(suggestions)} optimization suggestions")
        return suggestions
    
    def display_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Display optimization suggestions to the user.
        
        Args:
            suggestions: List of suggestion dictionaries
        """
        if not suggestions:
            print(f"\n{Fore.GREEN} No optimization suggestions at this time{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}╔═══════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║     Optimization Suggestions              ║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚═══════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{Fore.YELLOW}{i}. {suggestion['reason']}{Style.RESET_ALL}")
            print(f"   Current: {suggestion['current']}")
            print(f"   Suggested: {Fore.GREEN}{suggestion['suggested']}{Style.RESET_ALL}")
            print(f"   Benefit: {suggestion['estimated_benefit']}\n")
