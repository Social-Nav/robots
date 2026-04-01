import typing
from pathlib import Path

import attrs
import yaml
from ament_index_python.packages import get_package_share_path
from arena_simulation_setup.tree import Identifier, PathView, SimplePathResolver
from arena_simulation_setup.utils.models import ModelWrapper
from arena_simulation_setup.utils.models.model_loader import (
    ModelProvider_URDF,
    ModelProvider_USD,
)


class ModelParams(dict[str, typing.Any]):
    @classmethod
    def from_yaml(cls, path: str) -> 'ModelParams':
        with open(path) as f:
            data = yaml.safe_load(f)
            assert isinstance(data, dict), f"Top-level structure in {path} must be a mapping"
            return cls(data)

    @property
    def base_frame(self) -> str:
        return self.get('robot_base_frame', 'base_link')

    @property
    def odom_frame(self) -> str:
        return self.get('robot_odom_frame', 'odom')

    @property
    def z_offset(self) -> float:
        return self.get('z_offset', 0.0)


class RobotView(PathView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_params: ModelParams | None = None

    @property
    def model_params(self) -> ModelParams:
        if self._cached_params is None:
            self._cached_params = ModelParams.from_yaml(str(self.path / 'model_params.yaml'))
        return self._cached_params

    @property
    def mappings(self) -> str:
        return str(self.path / 'mappings.yaml')

    @property
    def control(self) -> dict:
        with open(self.path / 'control.yaml') as f:
            mapping = yaml.safe_load(f)
            assert isinstance(mapping, dict), "Control file must contain a dictionary at the top level."
            return mapping

    @property
    def model(self) -> ModelWrapper:
        return ModelWrapper(
            self.name,
            {
                **ModelProvider_USD.asdict(self.path, self.name),
                **ModelProvider_URDF.asdict(self.path, self.name),
            }
        )


@attrs.define(eq=False, hash=False)
class RobotIdentifier(Identifier[RobotView]):
    def load(self, path: Path, /, **kwargs) -> RobotView:
        del kwargs  # unused
        return RobotView(path)


RobotIdentifier.use(SimplePathResolver(RobotIdentifier, get_package_share_path('arena_robots') / 'robots'))
