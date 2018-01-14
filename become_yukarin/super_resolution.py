from functools import partial
from pathlib import Path
from typing import Optional

import chainer
import numpy
import pyworld

from become_yukarin.config.sr_config import SRConfig
from become_yukarin.data_struct import AcousticFeature
from become_yukarin.data_struct import Wave
from become_yukarin.dataset.dataset import LowHighSpectrogramFeatureLoadProcess
from become_yukarin.dataset.dataset import LowHighSpectrogramFeatureProcess
from become_yukarin.dataset.dataset import WaveFileLoadProcess
from become_yukarin.model.sr_model import create_predictor_sr


class SuperResolution(object):
    def __init__(self, config: SRConfig, model_path: Path):
        self.config = config
        self.model_path = model_path

        self.model = model = create_predictor_sr(config.model)
        chainer.serializers.load_npz(str(model_path), model)

        self._param = param = config.dataset.param
        self._wave_process = WaveFileLoadProcess(
            sample_rate=param.voice_param.sample_rate,
            top_db=None,
        )
        self._low_high_spectrogram_process = LowHighSpectrogramFeatureProcess(
            frame_period=param.acoustic_feature_param.frame_period,
            order=param.acoustic_feature_param.order,
            alpha=param.acoustic_feature_param.alpha,
        )
        self._low_high_spectrogram_load_process = LowHighSpectrogramFeatureLoadProcess(
            validate=True,
        )

    def convert(self, input: numpy.ndarray) -> numpy.ndarray:
        converter = partial(chainer.dataset.convert.concat_examples, padding=0)
        inputs = converter([numpy.log(input)[:, :-1]])

        with chainer.using_config('train', False):
            out = self.model(inputs).data[0]

        out = out[0]
        out[:, out.shape[1]] = out[:, -1]
        return out

    def convert_to_audio(
            self,
            input: numpy.ndarray,
            acoustic_feature: AcousticFeature,
            sampling_rate: Optional[int] = None,
    ):
        out = pyworld.synthesize(
            f0=acoustic_feature.f0.ravel(),
            spectrogram=input.astype(numpy.float64),
            aperiodicity=acoustic_feature.aperiodicity,
            fs=sampling_rate,
            frame_period=self._param.acoustic_feature_param.frame_period,
        )
        return Wave(out, sampling_rate=sampling_rate)

    def convert_from_audio_path(self, input: Path):
        input = self._wave_process(str(input), test=True)
        input = self._low_high_spectrogram_process(input, test=True)
        return self.convert(input.low)

    def convert_from_feature_path(self, input: Path):
        input = self._low_high_spectrogram_load_process(input, test=True)
        return self.convert(input.low)

    def __call__(
            self,
            input: numpy.ndarray,
            acoustic_feature: AcousticFeature,
            sampling_rate: Optional[int] = None,
    ):
        high = self.convert(input)
        return self.convert_to_audio(high, acoustic_feature=acoustic_feature, sampling_rate=sampling_rate)