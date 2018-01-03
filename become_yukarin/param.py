from typing import NamedTuple


class VoiceParam(NamedTuple):
    sample_rate: int = 24000
    top_db: float = None
    pad_second: float = 0.0


class AcousticFeatureParam(NamedTuple):
    frame_period: int = 5
    order: int = 25
    alpha: float = 0.466


class Param(NamedTuple):
    voice_param: VoiceParam = VoiceParam()
    acoustic_feature_param: AcousticFeatureParam = AcousticFeatureParam()
