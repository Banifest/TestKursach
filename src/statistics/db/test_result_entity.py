# coding=utf-8
from enum import Enum, auto

from src.statistics.db.coderentity import CoderEntity
from src.statistics.db.entity import Entity


class TestResultEntity(Entity):
    TABLE_NAME: str = "TestResult"

    class NoisesType(Enum):
        SINGLE = auto()
        BLOCK = auto()

    timestamp: int
    flg_cascade: bool
    first_coder: CoderEntity
    second_coder: CoderEntity
    type_of_noise: NoisesType
    noise: float

    def __init__(
            self,
            timestamp,
            flg_cascade: bool,
            first_coder: CoderEntity,
            second_coder: CoderEntity,
            type_of_noise: NoisesType,
            noise
    ):
        super().__init__()

        self.timestamp = timestamp
        self.flg_cascade = flg_cascade
        self.first_coder = first_coder
        self.second_coder = second_coder
        self.type_of_noise = type_of_noise
        self.noise = noise

    def create(self):
        self._connection.query(f"""
                            INSERT INTO "TestResult"(
                                "Timestamp", 
                                first_coder, 
                                second_coder, 
                                flg_cascade, 
                                noise_type, 
                                noise
                            )  VALUES (
                            '{self.timestamp}', 
                            '{self.first_coder.guid}', 
                            '{self.second_coder.guid}', 
                            {self.flg_cascade}, 
                            {self.type_of_noise.value}, 
                            {self.noise}
                            )
                        """)

    def delete(self):
        self._connection.query(f"""
            DELETE FROM "TestResult"
            WHERE "Timestamp" = {self.timestamp};
        """)

    def read(self) -> list:
        return self._connection.query(f"""
        SELECT *
        FROM {TestResultEntity.TABLE_NAME};        
    """)