"""Pipeline Orchestrator for managing pipeline execution"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from app.pipeline.types import (
    PipelineStep, ProgressCallback, LogCallback,
    CancellationToken, StepResult, PipelineConfig
)
from app.core.logger_manager import LoggerManager


class PipelineOrchestrator:
    """
    Orchestrates pipeline execution with progress tracking, cancellation,
    and result caching.
    """
    
    def __init__(
        self,
        config: PipelineConfig,
        logger: LoggerManager
    ):
        """
        Initialize pipeline orchestrator.
        
        Args:
            config: Pipeline configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.cancellation_token = CancellationToken()
        
        # Step execution state
        self.current_step: Optional[PipelineStep] = None
        self.step_results: Dict[PipelineStep, StepResult] = {}
        self.execution_start_time: Optional[float] = None
        
        # Callbacks
        self.progress_callback: Optional[ProgressCallback] = None
        self.step_complete_callback: Optional[Any] = None
        
        self.logger.info("PipelineOrchestrator initialized", "Orchestrator")
    
    def set_progress_callback(self, callback: ProgressCallback) -> None:
        """Set progress callback for UI updates"""
        self.progress_callback = callback
    
    def set_step_complete_callback(self, callback: Any) -> None:
        """Set callback for when a step completes"""
        self.step_complete_callback = callback
    
    def cancel(self) -> None:
        """Cancel pipeline execution"""
        self.logger.warning("Pipeline cancellation requested", "Orchestrator")
        self.cancellation_token.cancel()
    
    def reset(self) -> None:
        """Reset orchestrator state"""
        self.cancellation_token.reset()
        self.current_step = None
        self.step_results.clear()
        self.execution_start_time = None
        self.logger.info("Orchestrator state reset", "Orchestrator")
    
    def execute_step(
        self,
        step: PipelineStep,
        step_function: Any,
        *args,
        **kwargs
    ) -> StepResult:
        """
        Execute a single pipeline step with progress tracking.
        
        Args:
            step: Pipeline step identifier
            step_function: Function to execute
            *args, **kwargs: Arguments to pass to step function
        
        Returns:
            StepResult from the step execution
        """
        if self.cancellation_token.is_cancelled():
            self.logger.warning(f"Step {step.value} skipped (cancelled)", "Orchestrator")
            return StepResult(
                success=False,
                data=None,
                metadata={"cancelled": True},
                errors=["Pipeline execution was cancelled"]
            )
        
        self.current_step = step
        self.logger.info(f"Starting step: {step.value}", "Orchestrator")
        start_time = time.time()
        try:
            # Execute step function with cancellation token
            if 'cancellation_token' not in kwargs:
                kwargs['cancellation_token'] = self.cancellation_token
            
            if 'progress_callback' not in kwargs and self.progress_callback:
                kwargs['progress_callback'] = self._create_step_progress_callback(step)
            
            result = step_function(*args, **kwargs)
            
            elapsed_time = time.time() - start_time
            
            # Add timing to metadata
            if not isinstance(result.metadata, dict):
                result.metadata = {}
            result.metadata['execution_time_sec'] = elapsed_time
            result.metadata['timestamp'] = datetime.now().isoformat()
            
            # Store result
            self.step_results[step] = result
            
            if result.success:
                self.logger.info(
                    f"[OK] Step {step.value} completed in {elapsed_time:.2f}s",
                    "Orchestrator"
                )
            else:
                self.logger.error(
                    f"[FAIL] Step {step.value} failed after {elapsed_time:.2f}s",
                    "Orchestrator"
                )
                if result.errors:
                    for error in result.errors:
                        self.logger.error(f"  - {error}", "Orchestrator")
            
            # Call step complete callback
            if self.step_complete_callback:
                self.step_complete_callback(step, result)
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(
                f"Exception in step {step.value}: {str(e)}",
                "Orchestrator",
                exc_info=True
            )
            
            result = StepResult(
                success=False,
                data=None,
                metadata={
                    "execution_time_sec": elapsed_time,
                    "timestamp": datetime.now().isoformat(),
                    "exception": str(e)
                },
                errors=[f"Exception: {str(e)}"]
            )
            
            self.step_results[step] = result
            return result
    
    def _create_step_progress_callback(self, step: PipelineStep) -> ProgressCallback:
        """Create a progress callback that includes step information"""
        def callback(progress: float, message: str) -> None:
            full_message = f"[{step.value}] {message}"
            if self.progress_callback:
                self.progress_callback(progress, full_message)
            self.logger.debug(f"Progress: {progress:.1f}% - {message}", "Orchestrator")
        
        return callback
    
    def get_step_result(self, step: PipelineStep) -> Optional[StepResult]:
        """Get result from a completed step"""
        return self.step_results.get(step)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of pipeline execution.
        
        Returns:
            Dictionary with execution statistics
        """
        total_time = 0.0
        successful_steps = 0
        failed_steps = 0
        
        for step, result in self.step_results.items():
            if result.success:
                successful_steps += 1
            else:
                failed_steps += 1
            
            if 'execution_time_sec' in result.metadata:
                total_time += result.metadata['execution_time_sec']
        
        return {
            "total_steps": len(self.step_results),
            "successful_steps": successful_steps,
            "failed_steps": failed_steps,
            "total_execution_time_sec": total_time,
            "cancelled": self.cancellation_token.is_cancelled()
        }
    
    def execute_pipeline_sequence(
        self,
        steps: List[tuple]
    ) -> bool:
        """
        Execute a sequence of pipeline steps.
        
        Args:
            steps: List of (PipelineStep, function, args, kwargs) tuples
        
        Returns:
            True if all steps succeeded, False otherwise
        """
        self.reset()
        self.execution_start_time = time.time()
        
        self.logger.info(f"Starting pipeline with {len(steps)} steps", "Orchestrator")
        
        for step, function, args, kwargs in steps:
            result = self.execute_step(step, function, *args, **kwargs)
            
            if not result.success:
                self.logger.error(
                    f"Pipeline halted at step {step.value}",
                    "Orchestrator"
                )
                return False
            
            if self.cancellation_token.is_cancelled():
                self.logger.warning("Pipeline cancelled by user", "Orchestrator")
                return False
        
        total_time = time.time() - self.execution_start_time
        self.logger.info(
            f"Pipeline completed successfully in {total_time:.2f}s",
            "Orchestrator"
        )
        
        return True
