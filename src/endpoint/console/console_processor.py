from typing import Optional

from src.channel.enum_codec_type import EnumCodecType
from src.endpoint.console.app_parser import AppParser
from src.endpoint.console.codec_parser import CodecParser
from src.endpoint.console.coder_parser import CoderParser
from src.endpoint.console.console_chanel_simulate import ConsoleChanelSimulate
from src.endpoint.console.console_coder_simulate import ConsoleCoderSimulate
from src.helper.pattern.singleton import Singleton


class ConsoleProcessor(metaclass=Singleton):
    _appParser: AppParser
    _coderParser: CoderParser
    _codecParser: CodecParser

    def __init__(
            self,
            app_parser: Optional[AppParser] = None,
            coder_parser: Optional[CoderParser] = None,
            codec_parser: Optional[CodecParser] = None
    ):
        if app_parser is not None:
            self._appParser = app_parser
        else:
            self._appParser = AppParser()

        if coder_parser is not None:
            self._codecParser = codec_parser
        else:
            self._codecParser = AppParser().codec_parser

        if coder_parser is not None:
            self._coderParser = coder_parser
        else:
            self._coderParser = AppParser().coder_parser

    def transfer(self):

        first_coder: ConsoleCoderSimulate = ConsoleCoderSimulate(
            coder_type_int=self._coderParser.coder_type,
            hem_size_pack=self._appParser.first_coder.hamming_package_length,
        )

        second_coder: Optional[ConsoleCoderSimulate] = ConsoleCoderSimulate(
            coder_type_int=self._coderParser.coder_type,
            hem_size_pack=self._appParser.second_coder.hamming_package_length,
        )

        chanel: ConsoleChanelSimulate = ConsoleChanelSimulate(
            first_coder_params=first_coder,
            second_coder_params=second_coder,
            noise_start=self._codecParser.noise_start,
            noise_end=self._codecParser.noise_end,
            count_test=self._codecParser.test_quantity_cycles,
            test_info=self._codecParser.info_for_test,
            noise_mode=self._codecParser.noise_type,
            noise_package_length=self._codecParser.noise_package_length,
            flg_split_package=None,
            quantity_steps_in_test_cycle=20,
            package_period=self._codecParser.noise_package_period,
            flg_first_interleaver=None,
            flg_second_interleaver=None,
            length_first_interleaver=None,
            length_second_interleaver=None
        )

        if self._codecParser.codec_type == EnumCodecType.SINGLE:
            chanel.start_first_test_cycle()
        else:
            chanel.start_cascade_test_cycle()
