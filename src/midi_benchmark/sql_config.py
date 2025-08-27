from dataclasses import dataclass

@dataclass
class SqlConfig:
    # Defaults to LocalDB. Change instance if needed (e.g., r".\SQLEXPRESS")
    server: str = r"(localdb)\MSSQLLocalDB"
    database: str = "ableton-midi-bench"
    # For LocalDB/Express on your box, Windows auth is easiest:
    trusted_connection: bool = True
    # ODBC driver name installed on your machine:
    odbc_driver: str = "ODBC Driver 17 for SQL Server"  # or "ODBC Driver 18 for SQL Server"
    # For Driver 18 you may need: Encrypt=yes;TrustServerCertificate=yes
    encrypt: str | None = None        # e.g. "yes"
    trust_cert: str | None = None     # e.g. "yes"

    def to_connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.odbc_driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
        ]
        if self.trusted_connection:
            parts.append("Trusted_Connection=yes")
        if self.encrypt:
            parts.append(f"Encrypt={self.encrypt}")
        if self.trust_cert:
            parts.append(f"TrustServerCertificate={self.trust_cert}")
        return ";".join(parts)
