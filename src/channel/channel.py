import random
from typing import Optional, Union

from coders.abstractCoder import AbstractCoder
from coders.interleaver import Interleaver
from src.coders.casts import BitListToInt
from src.coders.exeption import CodingException
from src.logger import log


class Channel:
    noiseProbability: int = 0  # вероятность ошибки
    countCyclical: int = 1
    duplex: bool = False
    information: str = ""
    coder: AbstractCoder
    interleaver: Interleaver.Interleaver = False

    countSuccessfullyMessage: int

    def __init__(self, coder: AbstractCoder or None, noiseProbability: int or float,
                 countCyclical: Optional[int],
                 duplex: Optional[bool], interleaver: Optional[Interleaver.Interleaver]):
        log.debug("Создание канала связи")
        self.coder: AbstractCoder = coder
        if noiseProbability is not None: self.noiseProbability = noiseProbability
        if countCyclical is not None: self.countCyclical = countCyclical
        if duplex is not None: self.duplex = duplex
        if interleaver is not None: self.interleaver = interleaver
        log.debug("Канал создан")

    def __str__(self) -> str:
        return "Вероятность ошибки в канале - {0}.\n"\
               "Является ли канал двухсторонним - {1}.\n"\
               "Используеммый кодер:\n {2}."\
               "Используется ли перемежитель на данном канале связи - {3}.\n"\
               "Количество циклов передачи пакета - {4}\n"\
               "Информация о последней передаче:\n{5}".format(
                self.noiseProbability,
                "Да" if self.duplex else "Нет",
                str(self.coder),
                "Нет" if not self.interleaver else "Да",
                self.countCyclical,
                self.information
                )

    def transfer(self, information: list) -> str:
        countSuccessfully: int = 0
        self.information += "Начата циклическая передача пакета ({0}).\n Количество передач {1}.\n".\
            format(information, self.countCyclical)

        for x in range(self.countCyclical):
            try:
                nowInformation: list = information
                nowInformation = self.coder.Encoding(nowInformation)
                if self.interleaver:
                    nowInformation = self.interleaver.shuffle(nowInformation)

                nowInformation = self.gen_interference(nowInformation)

                if self.interleaver:
                    nowInformation = self.interleaver.reestablish(nowInformation)

                nowInformation = self.coder.Decoding(nowInformation)
            except CodingException as err:
                self.information += "Пакет при передаче попыткой под номером {0} был повреждён и не подлежит "\
                                    "востановлению\n".format(x)
            else:
                if nowInformation == information:
                    countSuccessfully += 1
                    self.information += "Пакет при передаче попыткой под номером {0} был успешно передан\n".format(x)
                else:
                    self.information += "Пакет при передаче попыткой под номером {0} был повреждён и не подлежит "\
                                        "востановлению\n".format(x)

        self.information += "Циклическая передача пакета ({0}) завершена.\n"\
                            "Всего попыток передать пакет {1}.\n"\
                            "Количство успешно переданных пакетов {2}.\n"\
                            "Количество неудачно переданных пакетов {3}.\n".\
            format(information, self.countCyclical, countSuccessfully, self.countCyclical - countSuccessfully)

        return self.information

    def transfer_one_step(self, information: list) -> list:
        log.info("Производиться передача последовательности битов - {0}".format(information))
        now_information: list = information
        status: int = 0
        normalization_information = self.coder.try_normalization(information)
        try:
            now_information = self.coder.Encoding(normalization_information)

            if self.interleaver: now_information = self.interleaver.shuffle(now_information)

            help_information = now_information

            now_information = self.gen_interference(now_information, self.noiseProbability)

            if help_information != now_information: status = 1

            if self.interleaver: now_information = self.interleaver.reestablish(now_information)

            now_information = self.coder.Decoding(now_information)
        except CodingException as err:
            status = 2
            log.info("В ходе декодирования пакета {0} была обнаружена неисправляемая ошибка".format(now_information))
            self.information = "Пакет при передаче был повреждён и не подлежит востановлению\n"
        except:
            status = 2
            log.info("В ходе декодирования пакета {0} была обнаружена неисправляемая ошибка".format(now_information))
            self.information = "Пакет при передаче был повреждён и не подлежит востановлению\n"
        else:
            if now_information == normalization_information:
                if status != 1: status = 0
                log.info("Пакет {0} был успешно передан".format(information))
                self.information = "Пакет был успешно передан\n"
            else:
                status = 3
                log.error("Пакет {0} был повреждён при передаче передан и ошибку не удалось обнаружить".format(
                        now_information))
                self.information = "Пакет при передаче был повреждён и не подлежит "\
                                   "востановлению\n"
        return status

    def get_transfer_one_step(self, information: list) -> Union[list, int]:
        log.info("Производиться передача последовательности битов - {0}".format(information))
        now_information: list = information
        status: int = 0
        help_information: list
        try:
            now_information = self.coder.Encoding(now_information)
            if self.interleaver:
                now_information = self.interleaver.shuffle(now_information)

            help_information = now_information
            now_information = self.gen_interference(now_information, self.noiseProbability)

            if help_information != now_information:
                status = 1

            if self.interleaver:
                now_information = self.interleaver.reestablish(now_information)

            now_information = self.coder.Decoding(now_information)
        except CodingException as err:
            status = 2
            log.info("В ходе декодирования пакета {0} была обнаружена неисправляемая ошибка".format(now_information))
            self.information = "Пакет при передаче был повреждён и не подлежит востановлению\n"
        else:
            if BitListToInt(now_information) == BitListToInt(information):
                if status != 1: status = 0
                log.info("Пакет {0} был успешно передан".format(information))
                self.information = "Пакет был успешно передан\n"
            else:
                status = 3
                log.error("Пакет {0} был повреждён при передаче передан и ошибку не удалось обнаружить".format(
                        now_information))
                self.information = "Пакет при передаче был повреждён и не подлежит "\
                                   "востановлению\n"
        return [now_information, status]

    def get_information_about_last_transfer(self):
        return self.information

    def gen_interference(self, information: list, straight: Optional[float]) -> list:
        """
        Генерация помех с задданной вероятностью
        :param information: list Информация, представленная в виде массива битов
        :param straight: Optional[float] Вероятность помех принимает значения от 0.00 до 100.00, может быть опушенна, 
        в таком случае будет использоваться значение шума заданное в канале  
        :return: Искажённую информацию, представленную в виде массива битов
        """
        log.debug("Симуляция шума на канале с вероятностью {0}".format(straight))

        randomGenerator: random.Random = random.Random(random.random() * 50)  # генератор случайных чисел

        count_change_bit: int = int(len(information) * straight / 100)  # кол-во ошибок на канале
        if count_change_bit == 0 and straight != 0: count_change_bit = 0  # если ошибок не ноль, то увеличиваем до 1
        changes_bits: set = set()  # множество битов которые будут измененны

        while len(changes_bits) < count_change_bit:  # собираем номеров множество неповторяющихся битов
            changes_bits.add(randomGenerator.randint(0, len(information) - 1))

        changes_bits: list = list(changes_bits)  # преобразуем в список
        answer: list = information.copy()
        for x in changes_bits:  # инвертирование битов
            answer[x] ^= 1

        log.debug("В ходе симуляции шума пакет преобразовался в {0}".format(answer))
        return answer
