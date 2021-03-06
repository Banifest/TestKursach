# coding=utf-8
import argparse
from sqlite3 import Connection
from typing import Optional
from uuid import UUID

import math
import numpy as np

from src.coders import abstract_coder
from src.coders.casts import *
from src.endpoint.console.abstract_group_parser import AbstractGroupParser
from src.logger import log
from src.statistics.db.enum_coders_type import EnumCodersType
from src.statistics.db.table import hamming_table


class Coder(abstract_coder.AbstractCoder):
    _typeOfCoder: EnumCodersType = EnumCodersType.HAMMING
    _name: str = "Hamming"
    _matrixTransformation: List[List[int]] = []

    def __init__(self, length_information: int):
        log.debug("Create of Hamming _coder")

        # sum (2**(n-1)-1) from 1 to n must be >= length_information for correct check
        for iterator in range(1, length_information):
            if 2 ** iterator - iterator - 1 >= length_information:
                self.lengthAdditional = iterator
                break

        self.lengthInformation = length_information
        self.lengthTotal = self.lengthInformation + self.lengthAdditional
        self._matrixTransformation = []

        for iterator in range(self.lengthAdditional):
            matrix_row: list = []
            flag = True
            # Count nullable symbols
            count_null_symbols = (1 << iterator) - 1
            for y in range((2 ** iterator) - 1):
                matrix_row.append(0)

            while count_null_symbols < self.lengthTotal:
                for y in range(2 ** iterator):
                    matrix_row.append(1) if flag else matrix_row.append(0)
                    count_null_symbols += 1
                    if count_null_symbols >= self.lengthTotal:
                        break
                flag: bool = not flag
            self._matrixTransformation.append(matrix_row)
        # noinspection PyTypeChecker
        self._matrixTransformation = np.transpose(np.array(self._matrixTransformation))

    def encoding(self, information: List[int]) -> List[int]:
        log.info("Encoding package {0} of Hamming _coder".format(information))
        list_encoding_information: list = information
        list_encoding_information.reverse()
        if len(list_encoding_information) < self.lengthInformation:
            for x in range(self.lengthInformation - len(list_encoding_information)):
                list_encoding_information.append(0)
        list_encoding_information.reverse()
        code: list = []

        step: int = 0
        # Add checks bits
        for count in range(self.lengthTotal):

            # Check that number enter in set of number (2^n), where n is natural number
            if math.log2(count + 1) != int(math.log2(count + 1)) or step >= self.lengthAdditional:
                code.append([list_encoding_information[count - int(math.log2(count)) - 1]])
            else:
                code.append([0])
                step += 1

        answer = [x[0] for x in code]
        code = np.transpose(np.array(code))
        backup_info = list((np.dot(code, self._matrixTransformation) % 2)[0])
        for x in range(self.lengthAdditional):
            answer[(1 << x) - 1] = backup_info[x]
        return answer

    def decoding(self, information: List[int]) -> List[int]:
        log.info("Decoding package {0} of Hamming _coder".format(information))

        code = np.transpose(np.array([[x] for x in information]))
        answer: list = []

        try:
            status: list = list((np.dot(code, self._matrixTransformation) % 2)[0])
        except ValueError:
            # Impossible decoding. Not valid package length
            return information

        status.reverse()
        status_int_form: int = bit_list_to_int(status)
        if status_int_form != 0:
            log.debug("Error(s) detected")

            if len(code[0]) > status_int_form - 1:
                code[0][status_int_form - 1] = (code[0][status_int_form - 1] + 1) % 2
                old_status = status_int_form
                status_int_form = bit_list_to_int(num=list((np.dot(code, self._matrixTransformation) % 2)[0]))

                if status_int_form != 0:
                    log.debug("Impossible correction this package. But errors found")
                log.debug("Successfully repair bit in position {0}".format(old_status))
            else:
                log.debug("Impossible correction this package")
        count: int = 0
        step: int = 0
        for iterator in code[0]:
            if math.log2(count + 1) != int(math.log2(count + 1)) \
                    or step >= self.lengthAdditional:
                answer.append(iterator)
            else:
                step += 1
            count += 1
        return answer

    def to_json(self) -> dict:
        # noinspection PyUnresolvedReferences
        return {
            'name': self.name,
            'length _information word': self.lengthInformation,
            'length additional bits': self.lengthAdditional,
            'length coding word': self.lengthTotal,
            'matrix of generating': self._matrixTransformation.tolist(),
            'speed': self.get_speed()
        }

    def save_to_database(self, coder_guid: UUID, connection: Connection) -> None:
        # noinspection PyUnresolvedReferences
        connection.execute(hamming_table.insert().values(
            guid=coder_guid,
            matrix=self._matrixTransformation.tolist()
        ))

    class HammingCoderParser(AbstractGroupParser):
        _prefix: str = ""
        __PACKAGE_LENGTH: str = "hamming_package_length"

        @property
        def hamming_package_length(self) -> int:
            return self.arguments["{0}{1}".format(self._prefix, self.__PACKAGE_LENGTH)]

        def __init__(
                self,
                argument_parser: Optional[argparse.ArgumentParser] = None,
                argument_group=None,
                prefix: str = ""
        ):
            super().__init__(
                argument_parser=argument_parser,
                argument_group=argument_group
            )
            self._prefix = prefix

            self._argumentParser.add_argument(
                "-{0}hmgpl".format(prefix), "--{0}{1}".format(prefix, self.__PACKAGE_LENGTH),
                type=int,
                help="""Length of package for Hamming _coder"""
            )

            # We should parse arguments only for unique _coder
            if self._argumentGroup is None:
                self.arguments = vars(self._argumentParser.parse_args())

    @staticmethod
    def get_coder_parameters(
            argument_parser: Optional[argparse.ArgumentParser] = None,
            argument_group=None,
            prefix: str = ""
    ) -> HammingCoderParser:
        return Coder.HammingCoderParser(
            argument_parser=argument_parser,
            argument_group=argument_group,
            prefix=prefix
        )
