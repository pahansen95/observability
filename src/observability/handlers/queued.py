"""
Queued handler for non-blocking event processing.

Provides asynchronous event processing through a background thread,
decoupling event emission from potentially slow handler operations.
"""

import queue
import threading
import time
from typing import Optional

from ..types import EventDict, EventHandler
from .base import safe_handler_call


class QueuedHandler:
  """
  Non-blocking handler using background thread for event processing.
  
  Decouples event emission from handler processing by queuing events
  and processing them in a dedicated worker thread. Provides bounded
  memory usage and graceful shutdown with queue draining.
  
  Example:
      # Wrap slow handler for non-blocking operation
      file_handler = ManagedFileHandler('/var/log/app.log')
      queued = QueuedHandler(file_handler, max_queued=10000)
      
      # Events are queued immediately
      context.emit('event', data)  # Returns immediately
      
      # Worker processes events in background
  """

  def __init__(
    self,
    wrapped: EventHandler,
    max_queued: int = 10000,
    timeout: float = 5.0,
    drain_on_stop: bool = True
  ):
    """
    Initialize queued handler.

    Args:
        wrapped: Handler to receive queued events
        max_queued: Maximum queue size (drops events on overflow)
        timeout: Shutdown timeout in seconds
        drain_on_stop: Whether to process remaining events on stop
    """
    self.wrapped = wrapped
    self.max_queued = max_queued
    self.timeout = timeout
    self.drain_on_stop = drain_on_stop
    
    # Lifecycle state
    self._queue: Optional[queue.Queue] = None
    self._worker: Optional[threading.Thread] = None
    self._stop_event: Optional[threading.Event] = None
    self._dropped_count = 0
    self._processed_count = 0

  def start(self) -> None:
    """Start background processing thread."""
    if self._worker is not None:
      return  # Already started
    
    self._queue = queue.Queue(maxsize=self.max_queued)
    self._stop_event = threading.Event()
    self._dropped_count = 0
    self._processed_count = 0
    
    # Start wrapped handler if it has lifecycle
    if hasattr(self.wrapped, 'start'):
      self.wrapped.start()
    
    # Start worker thread
    self._worker = threading.Thread(
      target=self._process_events,
      name=f"QueuedHandler-{id(self)}",
      daemon=not self.drain_on_stop  # Daemon if not draining
    )
    self._worker.start()

  def stop(self) -> None:
    """Stop worker and optionally drain queue."""
    if self._stop_event is None:
      return  # Not started
    
    # Signal worker to stop
    self._stop_event.set()
    
    # Wait for worker with timeout
    if self._worker:
      self._worker.join(timeout=self.timeout)
      
      # Force terminate if still running
      if self._worker.is_alive() and __debug__:
        print(f"QueuedHandler worker did not stop within {self.timeout}s", 
              file=sys.stderr)
    
    # Drain remaining events if requested
    if self.drain_on_stop and self._queue:
      self._drain_queue()
    
    # Stop wrapped handler
    if hasattr(self.wrapped, 'stop'):
      self.wrapped.stop()
    
    # Clean up state
    self._queue = None
    self._worker = None
    self._stop_event = None

  def __call__(self, event: EventDict) -> None:
    """Queue event for background processing."""
    if not self._queue:
      return  # Not started
    
    try:
      self._queue.put_nowait(event)
    except queue.Full:
      self._dropped_count += 1
      if __debug__ and self._dropped_count == 1:
        print(f"QueuedHandler: Queue full, dropping events", file=sys.stderr)

  def _process_events(self) -> None:
    """Worker thread that processes queued events."""
    while not self._stop_event.is_set():
      try:
        # Get with timeout to check stop event periodically
        event = self._queue.get(timeout=0.1)
        
        # Process event through wrapped handler
        try:
          self.wrapped(event)
          self._processed_count += 1
        except Exception as e:
          safe_handler_call(
            f"QueuedHandler.{self.wrapped.__class__.__name__}",
            "processing event",
            e
          )
          
      except queue.Empty:
        continue  # Check stop event and continue

  def _drain_queue(self) -> None:
    """Process all remaining events in queue."""
    drained = 0
    start_time = time.time()
    
    while not self._queue.empty() and (time.time() - start_time) < self.timeout:
      try:
        event = self._queue.get_nowait()
        self.wrapped(event)
        drained += 1
      except queue.Empty:
        break
      except Exception as e:
        safe_handler_call(
          f"QueuedHandler.drain",
          "processing remaining event",
          e
        )
    
    if __debug__ and drained > 0:
      print(f"QueuedHandler: Drained {drained} events on shutdown", 
            file=sys.stderr)

  def get_stats(self) -> dict:
    """Get handler statistics."""
    return {
      'processed': self._processed_count,
      'dropped': self._dropped_count,
      'queued': self._queue.qsize() if self._queue else 0,
      'is_alive': self._worker.is_alive() if self._worker else False
    }
