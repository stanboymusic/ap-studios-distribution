import csv
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime
from ..models.dsr import DSRRecord

class DSRParser(ABC):
    @abstractmethod
    def parse(self, file_content: str, dsp_name: str) -> List[DSRRecord]:
        pass

class GenericCSVParser(DSRParser):
    def parse(self, file_content: str, dsp_name: str) -> List[DSRRecord]:
        records = []
        # Use StringIO to treat string as a file
        import io
        f = io.StringIO(file_content)
        reader = csv.DictReader(f)
        
        for row in reader:
            record = DSRRecord(
                dsp=dsp_name,
                period_start=datetime.strptime(row['period_start'], '%Y-%m-%d').date(),
                period_end=datetime.strptime(row['period_end'], '%Y-%m-%d').date(),
                territory=row['territory'],
                isrc=row['isrc'],
                usage_type=row['usage_type'],
                quantity=int(row['quantity']),
                gross_revenue=float(row['gross_revenue']),
                currency=row.get('currency', 'USD')
            )
            records.append(record)
        return records

class DSRIngestService:
    def __init__(self):
        self.parsers: Dict[str, DSRParser] = {
            "generic": GenericCSVParser(),
            # Future: "spotify": SpotifyDSRParser(), etc.
        }

    def ingest(self, file_content: str, dsp_name: str, format: str = "generic") -> List[DSRRecord]:
        parser = self.parsers.get(format, self.parsers["generic"])
        return parser.parse(file_content, dsp_name)
