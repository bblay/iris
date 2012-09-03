"""Defines the class :class:`Recogniser`.""" 


from abc import ABCMeta, abstractmethod
import struct


class Recogniser(object):
    """Abstract base class for recognising a file format."""
    
    __metaclass__ = ABCMeta
    
    title = None
    """Description of format."""
    
    priority = 0
    """Lower value = lower priority."""
    
    loader = None
    """Function to load from the file format."""

    @abstractmethod
    def examine(self, filename, file_handle, cache=None):
        """Return True if the file is recognised, else False.
        
        Called by the :func:`iris.load` framework.
        
        Args:
        
            * filename    - filename to optioanlly examine 
            * file_handle - file_handle to optionally examine
            
        Kwargs:
        
            * cache - for faster operation, this can be used in conjunction with
                      :func:`~Recogniser.magic32` and :func:`~Recogniser.magic64`.
        
        """
        pass
    
    def load(self, filenames, callback):
        """Call the loader associated with this format.
        
        Args:
        
        * filenames - list of pp filenames to load
        
        Kwargs:
        
        * callback - a function which can be passed on to :func:`iris.io.run_callback`
        
        """
        
        # We can't call it directly because it get's a 'self' arg,
        # so call it through this method.
        return self.loader(filenames, callback)

    def __str__(self):
        return "%s (priority %s)" % (self.title, self.priority)
    
    # helper functions with optional cache
    def magic32(self, file_handle, cache=None):
        """Read a 32-bit number from the file, if not already in the optional cache."""
        result = None
        if cache:
            key = "magic32"
            result = cache.get(key)
        if not result:
            result = struct.unpack('>L', file_handle.read(4))[0]
        if cache:
            cache[key] = result
        return result
            
    def magic64(self, file_handle, cache=None):
        """Read a 64-bit number from the file, if not already in the optional cache."""
        result = None
        if cache:
            key = "magic64"
            result = cache.get(key)
        if not result:
            result = struct.unpack('>Q', file_handle.read(8))[0]
        if cache:
            cache[key] = result
        return result
