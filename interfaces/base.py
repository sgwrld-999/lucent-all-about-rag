"""Base interface for invokable components."""

from abc import ABC, abstractmethod

from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")

class Invokable(ABC, Generic[InputT, OutputT]):
    """ 
    An interface for components that can be invoked with input data to produce output data.
    """
    @abstractmethod
    def invoke(self, input_data: InputT) -> OutputT:
        pass