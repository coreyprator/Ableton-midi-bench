import os
from dataclasses import dataclass


@dataclass
class SqlConfig:
    """SQL configuration read from environment variables.

    Required environment variables:
      - MIDI_BENCH_SQL_SERVER (e.g. .\SQLEXPRESS01)
      - MIDI_BENCH_SQL_DATABASE (e.g. ableton-midi-bench)

    This avoids hardcoding instance names in source code.
    """

    server: str = os.environ.get("MIDI_BENCH_SQL_SERVER", "")
    database: str = os.environ.get("MIDI_BENCH_SQL_DATABASE", "")
    # Windows auth by default
    trusted_connection: bool = True
    odbc_driver: str = os.environ.get("MIDI_BENCH_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    # Defaults tuned for local development with Driver 18
    encrypt: str | None = os.environ.get("MIDI_BENCH_ENCRYPT", "yes")
    trust_cert: str | None = os.environ.get("MIDI_BENCH_TRUST_CERT", "yes")

    def to_connection_string(self) -> str:
        if not self.server or not self.database:
            raise RuntimeError(
                "Environment variables MIDI_BENCH_SQL_SERVER and MIDI_BENCH_SQL_DATABASE must be set"
            )

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
from dataclasses import dataclass

@dataclass
class SqlConfig:
    # Defaults to the local SQLEXPRESS instance. Change instance if needed.
    import os
    from dataclasses import dataclass

    @dataclass
    class SqlConfig:
        # Read server/database from environment to avoid hardcoding.
        # Required environment variables:
        #   MIDI_BENCH_SQL_SERVER (e.g. .\SQLEXPRESS01)
        #   MIDI_BENCH_SQL_DATABASE (e.g. ableton-midi-bench)
        server: str = os.environ.get("MIDI_BENCH_SQL_SERVER", "")
        database: str = os.environ.get("MIDI_BENCH_SQL_DATABASE", "")
    # For LocalDB/Express on your box, Windows auth is easiest:
    trusted_connection: bool = True
    # ODBC driver name installed on your machine. Prefer the latest driver (18)
    odbc_driver: str = "ODBC Driver 18 for SQL Server"
    # Default local development settings: encrypt the connection but trust the
    # server certificate (common for self-signed certs created by SQL Server).
    # This avoids the "certificate chain was issued by an authority that is not
    # trusted" error when connecting to a local SQLEXPRESS instance.
    encrypt: str | None = "yes"      # set to "yes" for Driver 18
    trust_cert: str | None = "yes"   # set to "yes" to trust self-signed certs locally

    def to_connection_string(self) -> str:
        if not self.server or not self.database:
            raise RuntimeError(
                "MIDI_BENCH_SQL_SERVER and MIDI_BENCH_SQL_DATABASE must be set in the environment"
            )
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
